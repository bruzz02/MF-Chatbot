import asyncio
import json
import logging
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

URLS = [
    "https://www.indmoney.com/mutual-funds/kotak-large-cap-direct-growth-3941",
    "https://www.indmoney.com/mutual-funds/kotak-midcap-fund-direct-growth-3945",
    "https://www.indmoney.com/mutual-funds/kotak-small-cap-direct-growth-3979",
    "https://www.indmoney.com/mutual-funds/kotak-multicap-fund-direct-growth-1039821",
    "https://www.indmoney.com/mutual-funds/kotak-elss-tax-saver-scheme-growth-direct-2565"
]

async def scrape_fund(context, url):
    page = await context.new_page()
    logging.info(f"Scraping {url}...")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        await page.wait_for_selector("h1", timeout=30000)
        fund_name = await page.inner_text("h1")
        
        if fund_name == "www.indmoney.com":
             h1_elements = await page.query_selector_all("h1")
             for h1 in h1_elements:
                 text = await h1.inner_text()
                 if "Fund" in text or "Kotak" in text:
                     fund_name = text.strip()
                     break

        # Click Overview
        try:
            # Scroll to make sure tabs are in view
            await page.evaluate("window.scrollTo(0, 400)")
            await asyncio.sleep(1)
            
            # First try a specific button text
            overview_btn = await page.wait_for_selector("button:has-text('Overview')", timeout=10000)
            if overview_btn:
                await overview_btn.click()
                logging.info("Clicked Overview tab.")
                
                # Wait for at least one of the target labels to be visible
                try:
                    await page.wait_for_selector("text=Expense ratio", timeout=10000)
                    logging.info("Overview data labels are now visible.")
                except:
                    logging.warning("Timed out waiting for 'Expense ratio' label to appear.")
                
                await asyncio.sleep(2) # Final settle time
        except Exception as e:
             logging.warning(f"Could not click Overview tab or wait for content: {e}")

        fund_data = {
            "URL": url,
            "Fund Name": fund_name
        }

        # NAV
        try:
            nav_value = await page.get_by_text("₹").filter(has_text=".").first.inner_text()
            fund_data["NAV"] = nav_value.strip()
        except:
            fund_data["NAV"] = "N/A"

        # General Details Extraction from Overview Grid
        target_labels = [
            "Expense ratio", "AUM", "Min Lumpsum/SIP", "Lock In", 
            "Risk", "Benchmark", "Inception Date", "Exit Load"
        ]
        
        # Initialize fields with N/A
        for label in target_labels:
            fund_data[label] = "N/A"

        # High-precision JS extraction for Overview grid
        overview_data = await page.evaluate("""(labels) => {
            const results = {};
            // Find all flex containers that typically hold label-value pairs
            const containers = Array.from(document.querySelectorAll('div.flex.justify-between'));
            
            // Get all 'p' and 'span' elements to search for labels
            const allElements = Array.from(document.querySelectorAll('p, span'));
            
            labels.forEach(target => {
                // Find elements that match the target label (allowing for icons/small text variations)
                const matchingLabel = allElements.find(el => {
                    const text = el.innerText.trim();
                    return text.toLowerCase() === target.toLowerCase() || 
                           (text.length < target.length + 5 && text.toLowerCase().includes(target.toLowerCase()));
                });
                
                if (matchingLabel) {
                    // Find the container for this label and the corresponding value
                    const container = matchingLabel.closest('div.flex.justify-between') || matchingLabel.parentElement;
                    if (container) {
                        const texts = Array.from(container.querySelectorAll('p, span'))
                                           .map(el => el.innerText.trim())
                                           .filter(t => t.length > 0 && 
                                                        t.toLowerCase() !== target.toLowerCase() && 
                                                        t !== "i" && 
                                                        !t.includes("Get key fund statistics"));
                        
                        if (texts.length > 0) {
                            // The value is usually the last text item in the container
                            results[target] = texts[texts.length - 1];
                        }
                    }
                }
            });
            return results;
        }""", target_labels)
        
        fund_data.update(overview_data)

        # Specialized extraction for Risk (often has a unique structure or gauge)
        if fund_data["Risk"] == "N/A" or "Ranking" in fund_data["Risk"]:
            try:
                risk_val = await page.evaluate("""() => {
                    const riskRow = Array.from(document.querySelectorAll('div.flex.justify-between')).find(el => el.innerText.includes('Risk'));
                    if (!riskRow) return null;
                    const texts = Array.from(riskRow.querySelectorAll('p, span')).map(el => el.innerText.trim());
                    // Look for standard risk levels
                    const levels = ["Low", "Low to Moderate", "Moderate", "Moderately High", "High", "Very High"];
                    for (let l of levels) {
                        if (riskRow.innerText.includes(l)) return l + " Risk";
                    }
                    return null;
                }""")
                if risk_val: fund_data["Risk"] = risk_val
            except: pass

        # Fund Manager Extraction (Improved)
        try:
             manager_name = await page.evaluate("""() => {
                 const aboutSection = document.querySelector('div:has-text("About")') || document.body;
                 const p = Array.from(aboutSection.querySelectorAll('p')).find(el => el.innerText.includes('managed by'));
                 if (p) {
                     const match = p.innerText.match(/managed by\s+([^.]+?)(?:\s+since|\.|$|,)/i);
                     return match ? match[1].trim() : null;
                 }
                 return null;
             }""")
             if manager_name: fund_name["Fund Manager"] = manager_name
        except: pass

        return fund_data

    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return {"URL": url, "Error": str(e)}
    finally:
        await page.close()

async def main():
    import os
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        
        results = []
        for url in URLS:
            res = await scrape_fund(context, url)
            results.append(res)
            await asyncio.sleep(2)
            
        await browser.close()

    output_path = os.path.join(os.path.dirname(__file__), "fund_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    logging.info(f"Scraping completed. Results saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())

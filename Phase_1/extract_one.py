import asyncio
import json
import logging
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def extract_fund_details(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        logging.info(f"Navigating to {url}...")
        await page.goto(url, wait_until="domcontentloaded")
        
        # Click the 'Overview' button if it exists
        try:
            await page.wait_for_selector("button:has-text('Overview')", timeout=10000)
            await page.click("button:has-text('Overview')")
            logging.info("Clicked Overview tab.")
            await asyncio.sleep(2) # Wait for content to settle
        except Exception as e:
            logging.warning(f"Could not click Overview tab: {e}")

        # Targeted extraction for the specific fields
        target_labels = [
            "Expense ratio", "AUM", "Min Lumpsum/SIP", "Lock In", 
            "Risk", "Benchmark", "Inception Date", "Exit Load"
        ]
        
        results = {label: "N/A" for label in target_labels}
        
        # Use Page.evaluate to extract precisely
        extracted_data = await page.evaluate("""(labels) => {
            const data = {};
            // Get all 'p' and 'span' elements
            const allElements = Array.from(document.querySelectorAll('p, span, div'));
            
            labels.forEach(target => {
                // Find all elements that contain the label text exactly or as a substring
                const matchingLabels = allElements.filter(el => {
                    const text = el.innerText.trim();
                    return text.toLowerCase() === target.toLowerCase() || 
                           (text.length < target.length + 5 && text.toLowerCase().includes(target.toLowerCase()));
                });
                
                matchingLabels.forEach(labelEl => {
                    // Look in the parent container for a value
                    const container = labelEl.closest('div.flex.justify-between') || labelEl.parentElement;
                    if (container) {
                        const texts = Array.from(container.querySelectorAll('p, span'))
                                           .map(el => el.innerText.trim())
                                           .filter(t => t.length > 0 && t.toLowerCase() !== target.toLowerCase() && !t.includes("i"));
                        
                        if (texts.length > 0) {
                            // The value is usually the last text item in the container that isn't the label
                            data[target] = texts[texts.length - 1];
                        }
                    }
                });
            });
            return data;
        }""", target_labels)
        
        results.update(extracted_data)
        
        # Special case for Risk if not found (sometimes it has a different icon/structure)
        if results["Risk"] == "N/A":
             risk_val = await page.evaluate("""() => {
                 const riskRow = Array.from(document.querySelectorAll('div.flex.justify-between')).find(el => el.innerText.includes('Risk'));
                 if (!riskRow) return null;
                 // Common risk labels found in mutual fund pages
                 const levels = ["Low", "Low to Moderate", "Moderate", "Moderately High", "High", "Very High"];
                 for (let l of levels) {
                     if (riskRow.innerText.includes(l)) return l + " Risk";
                 }
                 return null;
             }""")
             if risk_val: results["Risk"] = risk_val

        await browser.close()
        return results

if __name__ == "__main__":
    url = "https://www.indmoney.com/mutual-funds/kotak-large-cap-direct-growth-3941"
    data = asyncio.run(extract_fund_details(url))
    print(json.dumps(data, indent=4))

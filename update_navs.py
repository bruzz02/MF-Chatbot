import asyncio
import json
import logging
import os
import re
from datetime import datetime
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def scrape_fund_details(context, url):
    """Refined scraper for all fund details using flexible text-based extraction."""
    page = await context.new_page()
    logging.info(f"Full Refresh: Scraping {url}...")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_selector("h1", timeout=30000)
        fund_name = await page.inner_text("h1")

        # Give the page some time to load dynamic content
        await asyncio.sleep(3)
        
        # Scroll to ensure all content is loaded
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
        await asyncio.sleep(2)

        page_text = await page.evaluate("document.body.innerText")
        
        fund_data = {
            "URL": url,
            "Fund Name": fund_name.strip(),
            "NAV_Date": datetime.now().strftime("%d %B %Y")
        }

        # Helper to extract using regex from page text
        def extract_regex(pattern, text, default="N/A"):
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else default

        # Extract NAV (usually near ₹ symbol)
        fund_data["NAV"] = extract_regex(r'₹\s*([\d,]+\.\d{2})', page_text)
        if fund_data["NAV"] != "N/A":
            fund_data["NAV"] = "₹" + fund_data["NAV"]

        # Extract AUM
        fund_data["AUM"] = extract_regex(r'(?:AUM|Assets Under Management).*?₹\s*([\d,]+\s*[Cr|Cr\.]*)', page_text)
        if fund_data["AUM"] == "N/A":
            fund_data["AUM"] = extract_regex(r'₹\s*([\d,]+)\s*Cr', page_text)
            if fund_data["AUM"] != "N/A": fund_data["AUM"] = "₹" + fund_data["AUM"] + " Cr"

        # Extract Expense Ratio
        fund_data["Expense ratio"] = extract_regex(r'Expense ratio\s*([\d\.]+\s*%)', page_text)

        # Extract Min Lumpsum/SIP
        fund_data["Min Lumpsum/SIP"] = extract_regex(r'Min Lumpsum/SIP\s*(₹\s*[\d,]+\s*/\s*₹\s*[\d,]+)', page_text)

        # Extract Lock In
        fund_data["Lock In"] = extract_regex(r'Lock In\s*([\w\s-]+)', page_text)
        if "No Lock-in" in page_text: fund_data["Lock In"] = "No Lock-in"

        # Extract Risk
        fund_data["Risk"] = extract_regex(r'([\w\s]+)\s*Risk', page_text)
        if fund_data["Risk"] != "N/A": fund_data["Risk"] = fund_data["Risk"] + " Risk"

        # Extract Benchmark
        fund_data["Benchmark"] = extract_regex(r'Benchmark\s*([\w\s\d:]+)', page_text)

        # Extract Inception Date
        fund_data["Inception Date"] = extract_regex(r'Inception Date\s*([\d\s\w,]+)', page_text)

        # Extract Exit Load
        fund_data["Exit Load"] = extract_regex(r'Exit Load\s*([\d\.]+\s*%)', page_text)

        # Fallback for structured data using JS if regex fails
        structured_data = await page.evaluate("""() => {
            const results = {};
            const containers = Array.from(document.querySelectorAll('div.flex.justify-between, tr'));
            const labels = ["Expense ratio", "AUM", "Min Lumpsum/SIP", "Lock In", "Risk", "Benchmark", "Inception Date", "Exit Load"];
            
            labels.forEach(label => {
                const match = containers.find(c => c.innerText.includes(label));
                if (match) {
                    const text = match.innerText.replace(label, "").trim();
                    if (text) results[label] = text.split('\\n').pop(); // Get likely value
                }
            });
            return results;
        }""")
        
        for k, v in structured_data.items():
            if fund_data.get(k) == "N/A" or not fund_data.get(k):
                fund_data[k] = v

        logging.info(f"Scraped {fund_name}: {fund_data}")
        return fund_data

    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return None
    finally:
        await page.close()

async def update_all_data():
    data_paths = ["Phase_1/fund_data.json", "Phase_2/fund_data.json"]
    
    if not os.path.exists(data_paths[0]):
        logging.error("Base data Phase_1/fund_data.json not found.")
        return

    with open(data_paths[0], "r", encoding="utf-8") as f:
        existing_funds = json.load(f)

    urls = [f.get("URL") for f in existing_funds if f.get("URL")]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

        new_results = []
        for url in urls:
            res = await scrape_fund_details(context, url)
            if res:
                new_results.append(res)
            else:
                old_data = next((f for f in existing_funds if f["URL"] == url), None)
                if old_data: new_results.append(old_data)
            await asyncio.sleep(2)

        await browser.close()

    # Save to both locations
    for path in data_paths:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(new_results, f, indent=4, ensure_ascii=False)
        logging.info(f"Successfully refreshed all data in {path}")

if __name__ == "__main__":
    asyncio.run(update_all_data())

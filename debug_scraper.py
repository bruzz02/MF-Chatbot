import asyncio
from playwright.async_api import async_playwright

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        url = "https://www.indmoney.com/mutual-funds/kotak-large-cap-direct-growth-3941"
        print(f"Navigating to {url}...")
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print(f"Response status: {response.status}")
            
            # Click the Overview button in the sticky nav
            await page.click("button:has-text('Overview')")
            await asyncio.sleep(3)
            
            # Scroll to the fund-overview section
            await page.evaluate("document.getElementById('fund-overview')?.scrollIntoView()")
            await asyncio.sleep(2)
            
            await page.screenshot(path="debug_overview_screenshot.png")
            content = await page.content()
            with open("debug_overview_content.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("Overview screenshot and content saved.")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug())

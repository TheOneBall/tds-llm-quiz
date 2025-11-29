import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    """Simple test to verify Playwright works"""
    try:
        print("🔧 Starting Playwright...")
        playwright = await async_playwright().start()
        
        print("🌐 Launching browser...")
        browser = await playwright.chromium.launch(headless=True)
        
        print("📄 Creating page...")
        page = await browser.new_page()
        
        print("🔍 Navigating to Google...")
        await page.goto("https://www.google.com", wait_until="networkidle")
        
        print("✅ Successfully loaded page!")
        title = await page.title()
        print(f"Page title: {title}")
        
        await page.close()
        await browser.close()
        await playwright.stop()
        
        print("✨ Test passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e)}")

# Run this with: python test_playwright.py
asyncio.run(test_browser())

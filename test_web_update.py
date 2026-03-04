import asyncio
from playwright.async_api import async_playwright
import os

ARTIFACTS_DIR = r"C:\Users\admin\.gemini\antigravity\brain\5bf0ed95-18bb-4bad-b9e7-edf28d6277fb"

async def capture_desktop_plans():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Desktop Viewport
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        await page.goto('http://localhost:5173/plans')
        await asyncio.sleep(2) # Wait for animations/rendering
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, 'desktop_plans_features.png'), full_page=True)
        
        await browser.close()
        print("Screenshot captured successfully in artifacts directory.")

asyncio.run(capture_desktop_plans())

import asyncio
from playwright.async_api import async_playwright
import os

ARTIFACTS_DIR = r"C:\Users\admin\.gemini\antigravity\brain\5bf0ed95-18bb-4bad-b9e7-edf28d6277fb"

async def capture_screens():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Mobile Viewport
        context = await browser.new_context(
            viewport={'width': 375, 'height': 812},
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
        )
        page = await context.new_page()
        
        # Capture Login
        await page.goto('http://localhost:5173/login')
        await asyncio.sleep(2)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, 'mobile_login.png'))
        
        # We cannot easily view Dashboard without logging in, but we CAN view the Plans page if it's protected we might be redirected. Let's try /plans anyway.
        await page.goto('http://localhost:5173/plans')
        await asyncio.sleep(2)
        await page.screenshot(path=os.path.join(ARTIFACTS_DIR, 'mobile_plans_unauth.png'))

        await browser.close()
        print("Screenshots captured successfully in artifacts directory.")

asyncio.run(capture_screens())

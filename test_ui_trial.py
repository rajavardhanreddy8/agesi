import asyncio
from playwright.async_api import async_playwright
import uuid

async def test_ui():
    print("Starting Playwright UI Test...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Go to register page
        print("Navigating to http://localhost:5173/register...")
        try:
            await page.goto("http://localhost:5173/register", timeout=10000)
        except Exception as e:
            print(f"Failed to navigate: {e}")
            await browser.close()
            return
            
        uid = str(uuid.uuid4())[:6]
        email = f"uitest_{uid}@example.com"
        print(f"Registering new user: {email}")
        
        # Fill the form
        await page.fill('input[name="full_name"]', "UI Test User")
        await page.fill('input[name="roll_number"]', f"UI{uid}")
        await page.fill('input[name="student_phone"]', "1234567890")
        
        await page.fill('input[name="email"]', email)
        await page.fill('input[name="password"]', "password123")
        await page.fill('input[name="outlook_password"]', "outlook123")
        
        await page.fill('input[name="parent1_name"]', "Parent Name")
        await page.fill('input[name="parent1_phone"]', "0987654321")
        await page.fill('input[name="parent1_email"]', "parent@example.com")
        
        # Click register button
        print("Submitting registration...")
        # Find button with text Register
        await page.click("button:has-text('Register')")
        
        # Wait for potential redirect or response
        await asyncio.sleep(2)
        
        # Check if we got redirected to login
        print(f"Current URL: {page.url}")
        
        # Try to login
        print("Logging in...")
        await page.goto("http://localhost:5173/login")
        await page.fill('input[type="email"]', email)
        await page.fill('input[type="password"]', "password123")
        await page.click("button:has-text('Sign In')")
        
        await asyncio.sleep(3)
        print(f"Post-login URL: {page.url}")
        
        # Check if we are on dashboard (meaning trial is active)
        if "dashboard" in page.url:
            print("SUCCESS: User was allowed into the dashboard! Trial is active.")
        else:
            print("FAILED: User was not directed to the dashboard. They might have been blocked or redirected to /plans.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_ui())

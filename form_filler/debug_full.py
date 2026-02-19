
import os
import time
import logging
from ms_form_automation import MSFormAutomation
from db import get_db_connection
from auth_system_v2 import decrypt_outlook_password

# Configure logging
logging.basicConfig(level=logging.INFO)

def run_debug():
    print("🚀 Starting Debug Script...")
    
    # 1. Fetch User Credentials
    print("🔑 Fetching user credentials...")
    conn = get_db_connection()
    cur = conn.cursor()
    # Using the email from the screenshot
    target_email = 'guntaka.reddy_2028@woxsen.edu.in'
    
    cur.execute("SELECT email, outlook_password_encrypted FROM users WHERE email = %s", (target_email,))
    user = cur.fetchone()
    
    if not user:
        print(f"❌ User {target_email} not found in DB!")
        return

    email = user[0]
    enc_pass = user[1]
    password = decrypt_outlook_password(enc_pass)
    
    print(f"✅ User found: {email}")
    
    # 2. Initialize Automation
    bot = MSFormAutomation(headless=True)
    bot.start_browser(email=email)
    
    # 3. Login
    try:
        # We need to manually login or use the microsoft_login method
        # But microsoft_login expects us to be on the form page or login page
        # The form URL:
        url = "https://forms.office.com/pages/responsepage.aspx?id=LSD36rPvekOhA1Bbufv3X9NSKOayoK9NtQfVOU9-8dhUNTVLNjhLSDZYMUlRVUNOMEc1MDQ0WFNDTS4u"
        
        print(f"🌐 Navigating to Form URL: {url}")
        bot.page.goto(url)
        bot.wait_for_loading_screen()
        
        # DEBUG: Print status
        print(f"Current URL: {bot.page.url}")
        time.sleep(5) # Force wait for redirect/render
        
        sign_in_count = bot.page.locator('text=Sign in').count()
        email_input_count = bot.page.locator('input[type="email"]').count()
        print(f"DEBUG: 'Sign in' count: {sign_in_count}, Email input count: {email_input_count}")

        if 'login.microsoftonline.com' in bot.page.url or sign_in_count > 0 or email_input_count > 0:
            print("🔒 Login required. Attempting login...")
            if bot.microsoft_login(email, password):
                print("✅ Login successful!")
            else:
                print("❌ Login failed!")
                # Dump page for debugging login fail
                with open("debug_login_fail.txt", "w", encoding="utf-8") as f:
                    f.write(bot.page.locator("body").inner_text())
                return
        else:
            print("🔓 Already logged in (session reused).")
            
        bot.wait_for_loading_screen()
        time.sleep(5)
        
        # 4. Interact with Form
        print("\n🔎 Selecting 'School of Technology'...")
        
        # Try to find and click the School
        try:
            school_radio = bot.page.locator('div[role="radio"][aria-label="School of Technology"]')
            if school_radio.count() > 0:
                school_radio.first.click()
                print("✅ Clicked 'School of Technology'")
            else:
                print("❌ Could not find 'School of Technology' radio button! Trying text match...")
                bot.page.locator('text=School of Technology').click()
                print("✅ Clicked text 'School of Technology'")
        except Exception as e:
            print(f"❌ Error clicking School: {e}")
            with open("debug_dump.txt", "w", encoding="utf-8") as f:
                f.write(bot.page.locator("body").inner_text())
            print("📄 Page text dumped to debug_dump.txt")

            
        print("⏳ Waiting 3s for any conditional fields to appear...")
        time.sleep(3)
        
        # 5. HEADER/Programme Check
        print("\n📋 DUMPING QUESTIONS:")
        questions = bot.page.locator('div[data-automation-id="questionItem"]').all()
        found_programme = False
        
        with open("form_questions.txt", "w", encoding="utf-8") as f:
            for i, q in enumerate(questions):
                try:
                    q.scroll_into_view_if_needed()
                    title_el = q.locator('[data-automation-id="questionTitle"]').first
                    title = title_el.inner_text().replace('\n', ' ') if title_el.count() > 0 else "Unknown Title"
                    
                    log_line = f"Q{i+1}: {title}"
                    print(log_line)
                    f.write(log_line + "\n")
                    
                    if "Programme" in title:
                        found_programme = True
                        print(f"   🎯 FOUND PROGRAMME FIELD! Title: '{title}'")
                        f.write(f"   🎯 FOUND PROGRAMME FIELD!\n")
                        
                        # DUMP HTML
                        html_content = q.inner_html()
                        with open("debug_programme_html.html", "w", encoding="utf-8") as html_f:
                            html_f.write(html_content)
                        print("      ✅ Dumped HTML to debug_programme_html.html")
                        
                        # List options
                        radios = q.locator('[role="radio"]').all()
                        opts = [r.get_attribute('aria-label') for r in radios]
                        print(f"      OPTIONS: {opts}")
                        f.write(f"      OPTIONS: {opts}\n")
                        
                        # ATTEMPT SELECTION using shared logic
                        print("   🔍 Testing selection of 'B.Tech' via bot.select_radio...")
                        if bot.select_radio(title, "B.Tech"):
                            print(f"      ✅ bot.select_radio returned True")
                        else:
                            print(f"      ❌ bot.select_radio returned False")
                except Exception as e:
                    print(f"   Error reading Q{i+1}: {e}")
                    f.write(f"   Error reading Q{i+1}: {e}\n")
                
        if not found_programme:
            print("\n❌ 'Programme Name' field NOT found in DOM after selecting School of Technology.")
            
            # Check for B.Tech in page text just in case it's not a standard question
            if bot.page.locator('text=B.Tech').count() > 0:
                print("   ❓ Found text 'B.Tech' on page somewhere though...")
        
        # cleanup
        bot.browser.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ unexpected error: {e}")
        try:
            bot.browser.close()
        except: pass

if __name__ == "__main__":
    run_debug()

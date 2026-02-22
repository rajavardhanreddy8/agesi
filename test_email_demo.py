import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'mail_agent'))

from gmail_service import send_email

subject = "Test: Automation Mail Confirmation Working!"
body = "Hello! This is a test email sent from your Outing Automation Agent to demonstrate that the mail confirmation system is fully functional."
html_body = """
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <div style="padding: 20px; background-color: #f4f4f9; border-radius: 8px;">
      <h2 style="color: #4f46e5;">Automation Confirmation Test</h2>
      <p>Hello! This is a test email sent from your <strong>Outing Automation Agent</strong>.</p>
      <p>This demonstrates that the background task worker can successfully dispatch confirmation emails (including PDFs and screenshots) upon form completion.</p>
      <hr style="border: 0; border-top: 1px solid #ddd; margin: 20px 0;">
      <p style="font-size: 12px; color: #888;">Powered by Campus Automation</p>
    </div>
  </body>
</html>
"""

# Test address (from previous known context)
to_address = "guntaka.reddy_2028@woxsen.edu.in"
print(f"Sending test email to {to_address}...")
try:
    send_email(to_address, subject, body, html_body)
    print("Test email sent successfully!")
except Exception as e:
    print(f"Error sending email: {e}")

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def process_content_with_groq(email_content):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    client = Groq(api_key=api_key)

    prompt = f"""
    Analyze the following email content and extract:
    1. The weekend start date (e.g. 30.01.2026). 
    2. Any valid Microsoft Forms (forms.office.com) URL found.

    Email Subject: {email_content.get('subject')}
    Email Body Snippet:
    {email_content.get('body')[:2000]}

    Output PURE JSON ONLY:
    {{
        "start_date": "DD.MM.YYYY",
        "form_link": "https://..."
    }}
    If not found, return null values. do NOT wrap in markdown code blocks.
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        # Clean response
        content = chat_completion.choices[0].message.content
        content = content.replace('```json', '').replace('```', '').strip()
        import json
        return json.loads(content)
    except Exception as e:
        print(f"Grok API Error: {e}")
        return None

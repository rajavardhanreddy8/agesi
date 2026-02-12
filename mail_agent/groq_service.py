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
    1. The outing target date (e.g. 30.01.2026). This could be a weekend or a special mid-week holiday/event.
    2. Any valid Microsoft Forms (forms.office.com) URL found.
    3. The reason for the outing (e.g., "Home Visit", "Shopping", "Medical"). If not explicitly stated, infer it if possible, or return null.

    Email Subject: {email_content.get('subject')}
    Email Body Snippet:
    {email_content.get('body')[:2000]}

    Output PURE JSON ONLY:
    {{
        "start_date": "DD.MM.YYYY",
        "form_link": "https://...",
        "reason": "Home Visit"
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

def verify_form_data_with_groq(scraped_data, expected_data):
    """
    Verify if the filled form data matches expected data using AI.
    Returns: (is_valid, reason)
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return False, "API Key missing"

    client = Groq(api_key=api_key)

    prompt = f"""
    Compare the data filled in a Microsoft Form (Scraped Data) against the source of truth (Expected Data).
    
    1. Ignore formatting differences (e.g. +91 987 vs 987, "School of Tech" vs "School of Technology").
    2. Ignore case sensitivity.
    3. If a field is missing in Scraped Data but present in Expected, it's a MISMATCH.
    4. If Scraped Data has valid data where Expected was empty/null, it's a MATCH (enrichment).
    
    Expected Data:
    {json.dumps(expected_data, indent=2)}
    
    Scraped Form Data:
    {json.dumps(scraped_data, indent=2)}
    
    Output PURE JSON:
    {{
        "match": true/false,
        "reason": "Explanation if false, or 'Verified' if true"
    }}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        content = chat_completion.choices[0].message.content
        content = content.replace('```json', '').replace('```', '').strip()
        result = json.loads(content)
        return result.get('match', False), result.get('reason', 'AI returned no reason')
    except Exception as e:
        print(f"Grok Verification Error: {e}")
        # Fail safe: if AI fails, we might want to fail verification to be safe?
        # Or warn? User asked for verification. Better fail.
        return False, f"AI Error: {str(e)}"

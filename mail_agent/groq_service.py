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
    1. The weekend dates mentions (e.g. Saturday and Sunday dates).
    2. Any valid URL/link found in the email, especially permission form links.

    Email Subject: {email_content.get('subject')}
    Email Body:
    {email_content.get('body')}

    Output ONLY the result in this format:
    Weekend Dates: [Date 1, Date 2]
    Link: [The Link]
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    return chat_completion.choices[0].message.content

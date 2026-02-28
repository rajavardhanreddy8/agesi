from mail_agent.gmail_service import get_latest_email_content
query = 'subject:"Fwd: WEEKEND OUTING REQUEST"'
data = get_latest_email_content(query)
if data:
    try:
        from mail_agent.bridge import process_content_with_groq
        print('SUBJECT:', data.get('subject'))
        print('BODY LENGTH:', len(data.get('body', '')))
        print('REGEX LINKS:', data.get('form_links', []))
        res = process_content_with_groq(data)
        print('GROQ EXTRACT:', res)
    except Exception as e:
        print('Error:', e)
else:
    print('NO DATA FOUND')

import re

with open('email_body.txt', 'r', encoding='utf-8') as f:
    text = f.read()

href_pattern = re.compile(r'href\s*=\s*["\']((?:https?://)[^"\']+)')
raw_url_pattern = re.compile(r'(https?://[^\s"\'<>]+)')

hrefs = href_pattern.findall(text)
raws = raw_url_pattern.findall(text)

print("HREFs found:", hrefs)
print("RAW URLs found:", raws)
print("Form Links:", [l for l in (hrefs + raws) if "forms.office.com" in l or "docs.google.com" in l])

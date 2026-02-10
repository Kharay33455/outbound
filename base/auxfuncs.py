import requests, os
from django.template.loader import render_to_string

# send mails when via https smtp is down or unavailable
def send_mail_via_api(subject: str, html_content, to):
    try:
        subject = subject
        body ={"to": to,"subject": subject,"body": html_content,
            "subscribed": False,"name": "Cashien Administration","from": os.getenv("FE")}
        token = f"Bearer {os.getenv('EMAIL_API_KEY')}"
        headers = {"Authorization": token, "Content-Type":"application/json"}
        resp = requests.post("https://api.useplunk.com/v1/send", json=body, headers = headers)
    except:
        return False
    if resp.status_code == 200:
        return True
    else:
        return False

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
sg = SendGridAPIClient(SENDGRID_API_KEY)

message = Mail(
    from_email='akoskivaara@umass.edu',  # varmista, että verifioitu
    to_emails='attekosk@gmail.com',
    subject='Test',
    plain_text_content='Hello world'
)

try:
    response = sg.send(message)
    print(response.status_code)
except Exception as e:
    print(e)
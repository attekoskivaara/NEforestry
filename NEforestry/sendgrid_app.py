from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import os

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
if not SENDGRID_API_KEY:
    raise ValueError("SendGrid API key not found!")

FROM_EMAIL = "atte.koskivaara@luke.fi"  # vahvistettu
TO_EMAIL = "attekosk@gmail.com"

message = Mail(
    from_email=FROM_EMAIL,
    to_emails=TO_EMAIL,
    subject="Test Email",
    plain_text_content="HEIPPA! Käyhän tekemässä kysely: https://hulicupter.pythonanywhere.com/"
)

sg = SendGridAPIClient(SENDGRID_API_KEY)

try:
    response = sg.send(message)
    print(f"Email sent! Status code: {response.status_code}")
except Exception as e:
    print(f"Error sending email: {e}")

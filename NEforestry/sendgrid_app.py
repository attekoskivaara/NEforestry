from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Personalization
from dotenv import load_dotenv
import os
import csv

# Lataa .env
load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
if not SENDGRID_API_KEY:
    raise ValueError("SendGrid API key not found!")

FROM_EMAIL = "akoskivaara@umass.edu"
REPLY_TO_EMAIL = "attekoskivaara@luke.fi"

print(f"API key: {SENDGRID_API_KEY[:4]}...")  # Näet että key ei ole None
print(f"From email: {FROM_EMAIL}")           # Varmista että email on verifioitu


# Oletetaan, että CSV sisältää sarakkeet: email, first_name, username, password
recipients_file = "recipients_test.csv"

recipients = []
with open(recipients_file, newline="", encoding="utf-8-sig") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for row in reader:
        print(row)
        recipients.append(row)

# Lähetettävän viestin yleinen osa
SUBJECT = "Please participate in the New England forestry survey"

sg = SendGridAPIClient(SENDGRID_API_KEY)

for r in recipients:
    first_name = r.get("first_name")
    email = r.get("email")
    username = r.get("username")
    password = r.get("password")

    # Personoitu aloitus
    if first_name:
        greeting = f"Dear {first_name},"
    else:
        greeting = "Dear recipient,"

    # Viestin sisältö
    TEXT = f"""{greeting}

We need your expertise. Your experience in forest management and decision-making makes you a key contributor to understanding how New England’s forest landscapes are shaped.

By sharing your insights on preferred management practices, you will help guide the development of the desired landscape and forest management in New England. Additionally, by participating in the survey you will learn about the current state of New England’s forests and how they are utilized, providing a unique perspective on trade-offs and management decisions.

Your survey login credentials are:
Username: {username}
Password: {password}

Please take the survey here: https://hulicupter.pythonanywhere.com/

Thank you for contributing to a better understanding of forest management and ecosystem service governance. Your input will directly inform future planning and decision-making in the region.

If you know someone else who should participate, please feel free to share their email with us so we can send them the survey.

If you have any questions regarding the survey, please feel free to reply to this email.

Best regards,
Atte
"""

    # Luo ja lähetä viesti
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject=SUBJECT,
        plain_text_content=TEXT
    )
    message.reply_to = Email(REPLY_TO_EMAIL)

    try:
        response = sg.send(message)
        print(f"Email sent to {email}! Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email to {email}: {e}")

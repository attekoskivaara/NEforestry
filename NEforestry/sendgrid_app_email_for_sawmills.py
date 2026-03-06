from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Personalization, Header
from dotenv import load_dotenv
import os
import csv

# Lataa .env
load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
if not SENDGRID_API_KEY:
    raise ValueError("SendGrid API key not found!")

FROM_EMAIL = "survey@neforestvisions.org"
REPLY_TO_EMAIL = "atte.koskivaara@luke.fi"

print(f"API key: {SENDGRID_API_KEY[:4]}...")  # Näet että key ei ole None
print(f"From email: {FROM_EMAIL}")           # Varmista että email on verifioitu


# Oletetaan, että CSV sisältää sarakkeet: email, first_name, username, password
recipients_file = "emailing/1st_round/sendgrid/vain_attekosk.csv"

recipients = []
with open(recipients_file, newline="", encoding="utf-8-sig") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for row in reader:
        print(row)
        recipients.append(row)

# Lähetettävän viestin yleinen osa
SUBJECT = "Shaping the Future of New England’s Forests: Take Our Interactive Survey and Show How You Would Shape It"

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

You have been identified as a key actor in forest management and its practical implementation. The goal of this survey is to better understand how different stakeholders would prioritize forest uses and management decisions in the region.

***You do not need to be an expert on every topic in the survey. Your perspective and practical experience are what matter most. Your input will help shape future forest planning and management discussions in New England.***

Your survey login credentials are:
Username: {username}
Password: {password}

Please take the survey here:
https://www.neforestvisions.org/

The survey provides an overview of the current state of New England’s forests and allows you to explore how different land-use priorities affect the landscape and the services forests provide.

We recommend completing the survey on a computer, as it includes visualizations and interactive elements that are not optimized for small mobile screens.

If you know someone whose expertise would be valuable for this survey, please feel free to share their contact information with us.

If you have any questions, please feel free to reply to this email.

Best regards,

Atte Koskivaara
Visiting Postdoctoral Researcher, University of Massachusetts Amherst, USA
Researcher, Natural Resources Institute Finland (Luke)
    """

    # Luo ja lähetä viesti
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=email,
        subject=SUBJECT,
        plain_text_content=TEXT
    )
    message.reply_to = Email(REPLY_TO_EMAIL)
    message.add_header(Header("X-Entity-Ref-ID", "survey2026"))
    try:
        response = sg.send(message)
        print(f"Email sent to {email}! Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email to {email}: {e}")

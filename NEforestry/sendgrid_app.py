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
recipients_file = "recipients_test_240226_atte.csv"

recipients = []
with open(recipients_file, newline="", encoding="utf-8-sig") as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',')
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

You have been identified as a key actor in forest management and its practical implementation based on your experience and expertise. It is therefore especially important to understand your perspective on a central question: What should the future forest landscape and forestry in New England look like?

By sharing your insights on preferred land-use priorities and forest management decisions, you will help identify key priorities, trade-offs, and areas of alignment among stakeholders, and will directly inform future landscape planning and forest management discussions across the region.

In addition, participation provides you with an overview of the current state of New England’s forests, how they are currently utilized, and the broader trade-offs involved in management decisions—offering a structured perspective on how different objectives and ecosystem services interact.

Your survey login credentials are:
Username: {username}
Password: {password}

Please take the survey here:
https://www.neforestvisions.org/

Thank you for contributing to a better understanding of forest management and ecosystem service governance in New England. Your input will directly inform future planning and decision-making in the region.

If you know someone else whose expertise would be valuable for this survey, please feel free to share their contact information with us so we can send them an invitation.

If you have any questions regarding the survey, please feel free to reply to this email.

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

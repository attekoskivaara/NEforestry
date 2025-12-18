from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, Personalization
from dotenv import load_dotenv
import os

# Lataa .env
load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
if not SENDGRID_API_KEY:
    raise ValueError("SendGrid API key not found!")

FROM_EMAIL = "akoskivaara@umass.edu"
REPLY_TO_EMAIL = "akoskivaara@umass.edu"

# Lista vastaanottajia
recipients = [
    "attekosk@gmail.com",
    "atte.koskivaara@luke.fi"
]

TEXT = """
Hi Atte! 

I hope you're doing well. I wanted to ask if you would be willing to take a quick look at the survey for which I showed you a prototype when we met. It is available here: https://hulicupter.pythonanywhere.com/

with this username: jshakun@newenglandforestry.org and password: neff2025

Obviously, if you have any comments about its functionality or something is not clear etc. it would be great to hear about it. All feedback is welcome.

If any colleagues come to mind who might also be good test users, please feel free to let me know so I can share the link with their credentials as well.

In addition, I’d be very interested to hear if you are aware of any contact lists or networks that could be particularly relevant for responding to specific parts of the survey.

Many thanks in advance.

Best regards,
Atte
"""

# Luo pääviesti ilman vastaanottajia
message = Mail(
    from_email=FROM_EMAIL,
    subject="Testing my short survey",
    plain_text_content=TEXT
)

# Aseta reply-to
message.reply_to = Email(REPLY_TO_EMAIL)

# Lisää jokaiselle vastaanottajalle oma Personalization
for r in recipients:
    p = Personalization()
    p.add_to(Email(r))
    message.add_personalization(p)

# (Valinnainen) testikopio itsellesi BCC:n kautta
# message.add_bcc(Email("akoskivaara@umass.edu"))

# Lähetä
sg = SendGridAPIClient(SENDGRID_API_KEY)

try:
    response = sg.send(message)
    print(f"Email sent! Status code: {response.status_code}")
except Exception as e:
    print(f"Error sending email: {e}")

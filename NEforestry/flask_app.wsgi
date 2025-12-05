import sys
import os

# Lisää polku projektiisi
project_home = '/home/hulicupter/flask_app'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Aseta environment-muuttujat, jos tarvetta
os.environ['PYTHONPATH'] = project_home

# Tuo Dash app
from flask_app import app  # oletetaan, että Dash-appisi on flask_app.py tiedostossa ja muuttuja on 'app'

# Dash.app ei ole WSGI-app suoraan, joten otetaan sen Flask osa
application = app.server  # PythonAnywhere odottaa, että muuttuja on 'application'

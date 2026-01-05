# config/wsgi.py
import os
from django.core.wsgi import get_wsgi_application
from dotenv import load_dotenv

# This is the crucial change. We find the .env file at the project root
# and load it. This ensures that when Gunicorn starts, all environment
# variables are loaded into the process before the Django application
# itself is initialized.
# This command is safe for production because the .env file won't exist there,
# so it will correctly do nothing and rely on the environment variables
# set in the Render dashboard.
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
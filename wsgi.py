import sys
import os

# This is a placeholder path. We will change 'YourPythonAnywhereUsername'
# to your actual username on the PythonAnywhere server later.
# For now, it just sets up the structure.
project_home = '/home/YourPythonAnywhereUsername/notes_website'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Make sure the app can find the .env file if run via WSGI
# This assumes your .env file is in the project_home directory
from dotenv import load_dotenv
dotenv_path = os.path.join(project_home, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Import the Flask app instance
from app import app as application
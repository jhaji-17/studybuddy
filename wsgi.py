import sys
import os
from dotenv import load_dotenv

# Set the path to your project folder
project_home = '/home/studdybuddyy/studybuddy'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Load the .env file from your project folder
dotenv_path = os.path.join(project_home, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Import your Flask app instance from your app.py file
from app import app as application
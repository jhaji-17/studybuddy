import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# This defines the permission your app is asking for:
# "I just want to be able to create/upload files, that's it."
SCOPES = ['https://www.googleapis.com/auth/drive.file']

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # This line starts a temporary web server and opens your browser
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return creds

if __name__ == '__main__':
    get_credentials()
    print(f"--- SUCCESS ---")
    print(f"Authentication successful. The '{TOKEN_FILE}' file has been created.")
    print(f"You can now securely upload both '{CREDENTIALS_FILE}' and '{TOKEN_FILE}' to PythonAnywhere.")
    print(f"IMPORTANT: Make sure to add both of these filenames to your .gitignore file!")
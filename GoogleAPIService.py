from __future__ import print_function

from os import path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from apiclient import discovery
from urllib import response

class GoogleAPIService:

    def login(self, credentialsFileName, tokenFileName, scopesString):
        creds = None
        if path.exists(tokenFileName):
            creds = Credentials.from_authorized_user_file(tokenFileName, scopesString)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentialsFileName, scopesString)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(tokenFileName, 'w') as token:
                token.write(creds.to_json())
        self.form_service = discovery.build('forms', 'v1', credentials=creds)
        self.drive_service = discovery.build('drive', 'v3', credentials=creds)
        self.gmail_service = discovery.build("gmail", "v1", credentials=creds)

    def getFormService(self):
        return self.form_service
    
    def getDriveService(self):
        return self.drive_service
    
    def getGmailService(self):
        return self.gmail_service
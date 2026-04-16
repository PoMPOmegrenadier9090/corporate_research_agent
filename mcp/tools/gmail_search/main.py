import os
import datetime
from typing import Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

def _extract_header(headers, name: str) -> str:
    for h in headers:
        if h.get('name', '').lower() == name.lower():
            return h.get('value', '')
    return ''

def search_emails(query: str, max_results: int = 10) -> dict[str, Any]:
    """
    Search Gmail for messages matching query within the last 14 days.
    """
    try:
        service = get_gmail_service()
        
        # Enforce the newer_than:14d filter
        if "newer_than:" not in query and "after:" not in query:
            query = f"{query} newer_than:14d"

        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])

        if not messages:
            return {"status": "success", "messages": [], "message": "No messages found within the last 14 days."}

        email_data_list = []
        for msg in messages:
            txt = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            payload = txt.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = _extract_header(headers, "Subject")
            sender = _extract_header(headers, "From")
            date = _extract_header(headers, "Date")

            snippet = txt.get('snippet', '')
            
            email_data = {
                "id": msg['id'],
                "subject": subject,
                "from": sender,
                "date": date,
                "snippet": snippet
            }
            email_data_list.append(email_data)

        return {
            "status": "success",
            "messages": email_data_list,
            "query": query,
            "count": len(email_data_list)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

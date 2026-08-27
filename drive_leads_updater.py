import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# הרשאות גישה ל־Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def find_file_id(service, file_name):
    query = f"name = '{file_name}' and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    return None

def update_or_create_leads_in_drive(json_file_path, drive_file_name="leads_database.json"):
    # בדיקה מקדימה האם קובץ ה־JSON המקומי קיים לפני שמתחילים לתקשר עם ה־Drive
    if not os.path.exists(json_file_path):
        print(f"שגיאה: קובץ ה־JSON המקומי '{json_file_path}' לא נמצא בתיקייה!")
        print("אנא צור קובץ JSON עם נתוני הלידים והכנס אותו לתיקיית הפרויקט.")
        return

    service = get_drive_service()
    file_id = find_file_id(service, drive_file_name)
    media = MediaFileUpload(json_file_path, mimetype='application/json', resumable=True)

    if file_id:
        updated_file = service.files().update(
            fileId=file_id,
            media_body=media
        ).execute()
        print(f"הצלחה! הקובץ עודכן בהצלחה ב־Google Drive. מזהה קובץ: {updated_file.get('id')}")
    else:
        file_metadata = {
            'name': drive_file_name,
            'mimeType': 'application/json'
        }
        created_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        print(f"הצלחה! נוצר קובץ חדש ב־Google Drive. מזהה קובץ: {created_file.get('id')}")

if __name__ == "__main__":
    local_json_file = "leads_update.json"
    update_or_create_leads_in_drive(local_json_file)
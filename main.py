import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from playwright.sync_api import sync_playwright
import os
import time

# Define the scope
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive" # Need full Drive access to upload
]

##########################
# CONFIGURATION
##########################
SHEET_NAME = "AgentData" 
TARGET_URL = f"file://{os.path.abspath('form.html')}"

# Name of the folder in Google Drive where you want screenshots to go
# If empty, it goes to the root folder of the Service Account (hard to find!)
# BETTER: Share a folder with the service account email and put the ID here.
# For now, we will upload to root and print the link.
DRIVE_FOLDER_ID = None 

def get_creds():
    creds_file = 'credentials.json'
    if not os.path.exists(creds_file):
        print("Error: credentials.json not found!")
        return None
    return Credentials.from_service_account_file(creds_file, scopes=SCOPES)

def get_data_from_sheet():
    """Reads the first row of data (Name, Email) from the Google Sheet."""
    try:
        credentials = get_creds()
        if not credentials: return None
        
        gc = gspread.authorize(credentials)
        
        try:
            sh = gc.open(SHEET_NAME)
            worksheet = sh.sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"Error: Spreadsheet '{SHEET_NAME}' not found. Please create it!")
            return None

        row_values = worksheet.row_values(2)
        
        if not row_values:
            print("Row 2 is empty! Please add some data.")
            return None
            
        name = row_values[0] if len(row_values) > 0 else "Unknown"
        email = row_values[1] if len(row_values) > 1 else "unknown@example.com"
        
        return {"name": name, "email": email}

    except Exception as e:
        print(f"Error reading sheet: {e}")
        return None

def fill_form(data):
    """Uses Playwright to fill the form with the provided data."""
    if not data:
        return None

    print(f"Starting browser automation with data: {data}")
    screenshot_path = "form_submission.png"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print(f"Navigating to {TARGET_URL}...")
        page.goto(TARGET_URL)
        
        print(f"Typing Name: {data['name']}")
        page.fill("#name-input", data['name'])
        
        print(f"Typing Email: {data['email']}")
        page.fill("#email-input", data['email'])
        
        print("Clicking Submit...")
        page.click("#submit-btn")
        
        time.sleep(2)
        
        page.screenshot(path=screenshot_path)
        print(f"Success! Screenshot saved locally to {screenshot_path}")
        browser.close()
        
    return screenshot_path

def upload_to_drive(filename):
    """Uploads the file to Google Drive and returns the link."""
    print(f"Uploading {filename} to Google Drive...")
    try:
        credentials = get_creds()
        service = build('drive', 'v3', credentials=credentials)
        
        file_metadata = {'name': f"Screenshot_{int(time.time())}.png"}
        if DRIVE_FOLDER_ID:
            file_metadata['parents'] = [DRIVE_FOLDER_ID]
            
        media = MediaFileUpload(filename, mimetype='image/png')
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        print(f"File ID: {file.get('id')}")
        print(f"View it here: {file.get('webViewLink')}")
        
    except Exception as e:
        print(f"Error uploading to Drive: {e}")

def main():
    print("--- Step 1: Getting Data from Google Sheet ---")
    data = get_data_from_sheet()
    
    if data:
        print("--- Step 2: Filling the Web Form ---")
        screenshot = fill_form(data)
        
        if screenshot:
            print("--- Step 3: Uploading Screenshot to Google Drive ---")
            upload_to_drive(screenshot)
    else:
        print("Could not get data. Stopping.")

if __name__ == "__main__":
    main()

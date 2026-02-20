import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from playwright.sync_api import sync_playwright
import os
import sys
import time

# Define the scope
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive" 
]

##########################
# CONFIGURATION
##########################
SHEET_NAME = "AgentData" 
# Target URL - for now local form, but can be real URL
# When running as .exe, we look for form.html side-by-side or bundled
TARGET_URL = f"file://{os.path.abspath('form.html')}"

DRIVE_FOLDER_ID = None 

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_creds():
    # If bundled in .exe, look in temp folder. Otherwise look in current dir.
    creds_file_name = 'credentials.json'
    
    # Check current directory first (dev mode or user provided file)
    if os.path.exists(creds_file_name):
        return Credentials.from_service_account_file(creds_file_name, scopes=SCOPES)
    
    # Check bundled resource (packed inside .exe)
    bundled_path = resource_path(creds_file_name)
    if os.path.exists(bundled_path):
        return Credentials.from_service_account_file(bundled_path, scopes=SCOPES)
        
    print("Error: credentials.json not found!")
    return None

def get_data_from_sheet():
    try:
        credentials = get_creds()
        if not credentials: return None
        
        gc = gspread.authorize(credentials)
        
        try:
            sh = gc.open(SHEET_NAME)
            worksheet = sh.sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"Error: Spreadsheet '{SHEET_NAME}' not found.")
            return None

        row_values = worksheet.row_values(2)
        if not row_values:
            print("Row 2 is empty!")
            return None
            
        name = row_values[0] if len(row_values) > 0 else "Unknown"
        email = row_values[1] if len(row_values) > 1 else "unknown@example.com"
        
        return {"name": name, "email": email}

    except Exception as e:
        print(f"Error reading sheet: {e}")
        return None

def fill_form(data):
    if not data: return None

    print(f"Starting browser automation with data: {data}")
    screenshot_path = "form_submission.png"
    
    # Check if form.html is bundled
    target_url = TARGET_URL
    if "form.html" in target_url:
         # Resolving local file path correctly if bundled
         local_path = resource_path('form.html')
         target_url = f"file://{local_path}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print(f"Navigating to {target_url}...")
        page.goto(target_url)
        
        print(f"Typing Name: {data['name']}")
        try:
            page.fill("#name-input", data['name'])
            page.fill("#email-input", data['email'])
            page.click("#submit-btn")
        except:
            print("Could not find form elements. Check selectors.")
        
        time.sleep(2)
        page.screenshot(path=screenshot_path)
        print(f"Success! Screenshot saved locally to {screenshot_path}")
        browser.close()
        
    return screenshot_path

def upload_to_drive(filename):
    print(f"Uploading {filename} to Google Drive...")
    try:
        credentials = get_creds()
        service = build('drive', 'v3', credentials=credentials)
        
        file_metadata = {'name': f"Screenshot_{int(time.time())}.png"}
        if DRIVE_FOLDER_ID:
            file_metadata['parents'] = [DRIVE_FOLDER_ID]
            
        media = MediaFileUpload(filename, mimetype='image/png')
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        print(f"File ID: {file.get('id')}")
        print(f"View it here: {file.get('webViewLink')}")
        
    except Exception as e:
        print(f"Error uploading to Drive: {e}")

def main():
    print("--- Autopilot Agent Running ---")
    data = get_data_from_sheet()
    
    if data:
        print("--- Step 2: Filling Form ---")
        screenshot = fill_form(data)
        
        if screenshot:
            print("--- Step 3: Uploading ---")
            upload_to_drive(screenshot)
            
    print("\nDone. You can close this window.")
    # Keep window open so user can see output
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()

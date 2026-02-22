import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import sys
import shutil
import zipfile
import stat

# Configure Browser Path BEFORE importing Playwright
try:
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        target_browser_dir = os.path.join(bundle_dir, "pw-browsers")
        zip_path = os.path.join(bundle_dir, "pw-browsers.zip")
        
        if os.path.exists(zip_path) and not os.path.exists(target_browser_dir):
            print("Extracting bundled browsers... (this may take a moment)")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(bundle_dir) 
                
        # --- FIX: Restore Execute Permissions ---
        if os.path.exists(target_browser_dir):
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = target_browser_dir
            print(f"Playwright browsers configured at: {target_browser_dir}")
            
            # Walk through the folder and make binaries executable
            # Ideally we only need to target the main binary, but let's be safe.
            for root, dirs, files in os.walk(target_browser_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Simple heuristic: if it has no extension or is .app/Contents/MacOS/..., make it executable
                    # Or just try to make everything executable that looks like a binary
                    if "Google Chrome" in file or "chrome" in file.lower() or "node" in file.lower() or "ffmpeg" in file.lower():
                         try:
                            st = os.stat(file_path)
                            os.chmod(file_path, st.st_mode | stat.S_IEXEC)
                         except:
                            pass
        else:
             print("Warning: bundled browsers not found.")
    else:
        pass
except Exception as e:
    print(f"Error setting up environment: {e}")

from playwright.sync_api import sync_playwright
import time

# Define the scope
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive" 
]

SHEET_NAME = "AgentData" 
TARGET_URL = f"file://{os.path.abspath('form.html')}"
DRIVE_FOLDER_ID = "17gnQ3JcAodRCzzfqzELr2Y0GtMql8J3w" 

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_creds():
    creds_file_name = 'credentials.json'
    if os.path.exists(creds_file_name):
        return Credentials.from_service_account_file(creds_file_name, scopes=SCOPES)
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
    target_url = TARGET_URL
    if "form.html" in target_url:
         local_path = resource_path('form.html')
         target_url = f"file://{local_path}"

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        print(f"Navigating to {target_url}...")
        page.goto(target_url)
        print(f"Typing... {data['name']}")
        try:
            page.fill("#name-input", data['name'])
            page.fill("#email-input", data['email'])
            page.click("#submit-btn")
        except:
            print("Could not find form elements.")
        time.sleep(2)
        page.screenshot(path=screenshot_path)
        print(f"Success! Screenshot saved to {screenshot_path}")
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
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink',
            supportsAllDrives=True
        ).execute()
        print(f"File ID: {file.get('id')}")
        print(f"View it here: {file.get('webViewLink')}")
    except Exception as e:
        print(f"Error uploading to Drive: {e}")

def main():
    print("--- Autopilot Agent Running ---")
    data = get_data_from_sheet()
    if data:
        screenshot = fill_form(data)
        if screenshot:
            print("--- Step 3: Screenshot Ready ---")
            print(f"File saved: {screenshot}")
            # upload_to_drive(screenshot) # Disabled due to quota limits
            
            # Show success GUI message (works cleanly in windowed mode)
            try:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk()
                root.withdraw()
                root.lift()
                root.attributes('-topmost', True)
                messagebox.showinfo("Agent Complete", f"Success!\nForm filled and screenshot saved to: {screenshot}")
                root.destroy()
            except Exception:
                pass

    print("\nDone. You can close this window.")
    try:
        # Prompt only if safely running in a standard console (prevents crashes in windowed apps)
        input("Press Enter to exit...")
    except Exception:
        pass

if __name__ == "__main__":
    main()

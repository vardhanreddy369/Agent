import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import os
import sys
import shutil
import zipfile
import stat
import time
import threading
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from playwright.sync_api import sync_playwright

# Setup the theme for a premium "sellable" look
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Define the scope
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive" 
]

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
    return None

def setup_playwright():
    try:
        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
            target_browser_dir = os.path.join(bundle_dir, "pw-browsers")
            zip_path = os.path.join(bundle_dir, "pw-browsers.zip")
            
            if os.path.exists(zip_path) and not os.path.exists(target_browser_dir):
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(bundle_dir) 
                    
            if os.path.exists(target_browser_dir):
                os.environ["PLAYWRIGHT_BROWSERS_PATH"] = target_browser_dir
                for root, dirs, files in os.walk(target_browser_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if "Google Chrome" in file or "chrome" in file.lower() or "node" in file.lower() or "ffmpeg" in file.lower():
                             try:
                                st = os.stat(file_path)
                                os.chmod(file_path, st.st_mode | stat.S_IEXEC)
                             except:
                                pass
    except Exception as e:
        pass


class AutomationBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure Window
        self.title("SheetToForm Automation Bot v1.0")
        self.geometry("600x550")
        self.resizable(False, False)

        # Title Label
        self.title_label = ctk.CTkLabel(self, text="SheetToForm Pro", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        # Instructions
        self.desc_label = ctk.CTkLabel(self, text="Automate Google Sheet data directly into Google Forms.", font=ctk.CTkFont(size=14, slant="italic"), text_color="gray")
        self.desc_label.pack(pady=(0, 20))

        # Input Frame
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Sheet Name Input
        self.sheet_label = ctk.CTkLabel(self.frame, text="Google Sheet Name:", anchor="w")
        self.sheet_label.pack(fill="x", padx=15, pady=(15, 0))
        self.sheet_entry = ctk.CTkEntry(self.frame, placeholder_text="e.g. AgentData")
        self.sheet_entry.pack(fill="x", padx=15, pady=(5, 10))

        # Form URL Input
        self.url_label = ctk.CTkLabel(self.frame, text="Google Form URL:", anchor="w")
        self.url_label.pack(fill="x", padx=15, pady=(5, 0))
        self.url_entry = ctk.CTkEntry(self.frame, placeholder_text="https://docs.google.com/forms/...")
        self.url_entry.pack(fill="x", padx=15, pady=(5, 10))

        # Headless Toggle
        self.headless_var = ctk.BooleanVar(value=False)
        self.headless_checkbox = ctk.CTkCheckBox(self.frame, text="Run Invisibly (Headless Mode)", variable=self.headless_var)
        self.headless_checkbox.pack(anchor="w", padx=15, pady=(10, 10))

        # Status / Log Box
        self.log_box = ctk.CTkTextbox(self.frame, height=120, state="disabled")
        self.log_box.pack(fill="x", padx=15, pady=(10, 15))

        # Start Button
        self.start_btn = ctk.CTkButton(self, text="▶ Start Automation", font=ctk.CTkFont(size=15, weight="bold"), height=40, command=self.start_thread)
        self.start_btn.pack(pady=(10, 20))
        
        setup_playwright()
        self.log("System initialized. Ready to begin.")

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        self.update()

    def start_thread(self):
        sheet_name = self.sheet_entry.get().strip()
        form_url = self.url_entry.get().strip()

        if not sheet_name or not form_url:
            messagebox.showerror("Error", "Please fill in both the Sheet Name and Form URL.")
            return

        self.start_btn.configure(state="disabled", text="Running...")
        self.log("\n--- Starting Bot ---")
        
        # Run the heavy bot logic in a separate thread so GUI doesn't freeze
        thread = threading.Thread(target=self.run_bot_logic, args=(sheet_name, form_url, self.headless_var.get()))
        thread.start()

    def run_bot_logic(self, sheet_name, form_url, headless):
        try:
            self.log(f"Connecting to Google Sheet: {sheet_name}...")
            credentials = get_creds()
            if not credentials:
                self.log("ERROR: credentials.json not found!")
                self.start_btn.configure(state="normal", text="▶ Start Automation")
                return
                
            gc = gspread.authorize(credentials)
            sh = gc.open(sheet_name)
            worksheet = sh.sheet1
            
            # For this simple product version, we process row 2
            row_values = worksheet.row_values(2)
            if not row_values:
                self.log("ERROR: Row 2 in sheet is empty!")
                self.start_btn.configure(state="normal", text="▶ Start Automation")
                return
                
            name = row_values[0] if len(row_values) > 0 else "Unknown"
            email = row_values[1] if len(row_values) > 1 else "unknown@example.com"
            self.log(f"Successfully pulled Row 2: Name={name}, Email={email}")
            
            self.log("Launching Browser Automation...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=headless)
                page = browser.new_page()
                self.log(f"Navigating to Form...")
                page.goto(form_url)
                
                self.log("Locating input fields...")
                page.wait_for_selector('input[type="text"]', state="visible", timeout=15000)
                inputs = page.locator('input[type="text"]').all()
                
                if len(inputs) >= 2:
                    self.log(f"Typing Name ({name})...")
                    inputs[0].fill(name)
                    time.sleep(1)
                    self.log(f"Typing Email ({email})...")
                    inputs[1].fill(email)
                else:
                    self.log("ERROR: Could not find exactly two text inputs.")
                
                self.log("Clicking Submit button...")
                page.locator('div[role="button"]:has-text("Submit")').click()
                
                self.log("Waiting for confirmation page...")
                page.wait_for_selector('.freebirdFormviewerViewResponseConfirmationMessage, .vHW8K', state="visible", timeout=10000)
                
                screenshot_path = "success_shot.png"
                page.screenshot(path=screenshot_path)
                self.log(f"Screenshot saved to {screenshot_path}")
                browser.close()
                
            self.log("--- Automation Completed Successfully! ---")
            messagebox.showinfo("Success", "Automation completed successfully!")
            
        except Exception as e:
            self.log(f"CRITICAL ERROR: {str(e)}")
            messagebox.showerror("Error", f"Automation failed:\n\n{str(e)}")
        finally:
            self.start_btn.configure(state="normal", text="▶ Start Automation")

if __name__ == "__main__":
    app = AutomationBotGUI()
    app.mainloop()

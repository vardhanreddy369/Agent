# Google Sheets Automation Agent

This agent connects to a Google Sheet and logs a "Hello World" message. It is designed to run on Windows, Mac, or Linux.

## Prerequisites

1.  **Python 3.x**: Ensure Python is installed.
2.  **Google Cloud Project**: You need a Google Cloud project with the Google Sheets API enabled.

## Setup Instructions

### 1. Google Cloud Console Setup

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a new project (e.g., "My Automation Agent").
3.  **Enable API**:
    *   Search for "Google Sheets API" and enable it.
    *   Search for "Google Drive API" and enable it (optional but recommended for certain actions).
4.  **Create Service Account**:
    *   Go to "APIs & Services" > "Credentials".
    *   Click "Create Credentials" > "Service Account".
    *   Name it (e.g., "sheet-updater").
    *   Grant it the role **Editor** (optional, but easier for testing).
    *   Click "Done".
5.  **Download Key**:
    *   Click on the newly created service account email (it looks like `sheet-updater@project-id.iam.gserviceaccount.com`).
    *   Go to the "Keys" tab.
    *   Click "Add Key" > "Create new key" > "JSON".
    *   A file will download. **Rename it to `credentials.json`** and place it in this folder.

### 2. Google Sheet Setup

1.  Create a new Google Sheet in your browser.
2.  Name it `AgentLogs` (or whatever you set in `main.py`).
3.  **Share the Sheet**:
    *   Open `credentials.json` and find the `client_email` field.
    *   Copy that email address.
    *   Go to your `AgentLogs` Google Sheet, click "Share", and paste the email. give it **Editor** access.

### 3. Installation

Run the following command to install the required libraries:

```bash
pip install -r requirements.txt
```

### 4. Running the Agent

Run the script:

```bash
python main.py
```

If successful, you will see a new row added to your Google Sheet!

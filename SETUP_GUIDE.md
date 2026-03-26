# Video Prompt Agent - Setup Guide

This guide walks you through setting up the automated YouTube Shorts video prompt generation agent.

## Prerequisites

- GitHub account
- Google Cloud account
- Telegram account
- NVIDIA API account (for AI generation)

---

## Step 1: Google Cloud Setup

### 1.1 Create Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project: `video-prompt-agent`

### 1.2 Enable APIs
Enable the following APIs:
- Google Sheets API
- Google Drive API
- Google Docs API

### 1.3 Create Service Account
1. Go to **IAM & Admin** → **Service Accounts**
2. Create service account: `video-agent`
3. Grant roles:
   - **Sheets Viewer** (read topics, update status)
   - **Drive File Creator** (create docs)
   - **Docs Creator** (write content)
4. Download JSON key file
5. Copy the entire JSON content (you'll need it later)

### 1.4 Share Google Sheet with Service Account
1. Open your Google Sheet
2. Share with service account email: `video-agent@your-project.iam.gserviceaccount.com`
3. Give **Editor** access

### 1.5 Share Drive Folder with Service Account
1. Create a folder in Google Drive for output docs
2. Share with service account email
3. Give **Editor** access

---

## Step 2: Google Sheet Setup

Create a Google Sheet with this format:

| Column A (Title) | Column B (Status) |
|-----------------|-------------------|
| अगर आप च्युइंग गम निगल लें तो क्या होगा? | *(leave blank)* |
| सांप का जहर पीने से क्या होगा? | done |

- Column A: Video topic title
- Column B: Status (leave blank for pending, "done" when completed)

---

## Step 3: Telegram Bot Setup

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Create new bot: `/newbot`
3. Copy the bot token
4. Start a chat with your bot
5. Get your chat ID:
   - Send a message to the bot
   - Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Copy the `chat.id` from the response

---

## Step 4: NVIDIA API Setup

1. Go to [NVIDIA NGC](https://ngc.nvidia.com/)
2. Get your API key for NIM endpoints
3. Note the key (format: `nvapi-xxxxxxxx`)

---

## Step 5: GitHub Repository Setup

### 5.1 Create Repository
1. Create a new GitHub repository
2. Push the `video-prompt-agent` folder

### 5.2 Add Secrets
Go to **Settings** → **Secrets and variables** → **Actions**:

| Secret Name | Value |
|-------------|-------|
| `NVIDIA_API_KEY` | Your NVIDIA API key |
| `GOOGLE_SHEET_ID` | Sheet ID from URL (between `/d/` and `/edit`) |
| `GOOGLE_DRIVE_FOLDER_ID` | Folder ID from URL |
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your numeric chat ID |
| `SERVICE_ACCOUNT_JSON` | Entire JSON file content (as single line) |

### 5.3 Verify Sheet ID
- Sheet URL: `https://docs.google.com/spreadsheets/d/1abc123def456/edit`
- Sheet ID: `1abc123def456`

### 5.4 Verify Folder ID
- Folder URL: `https://drive.google.com/drive/folders/1abc123def456`
- Folder ID: `1abc123def456`

---

## Step 6: Test the Agent

### Manual Test
1. Go to **Actions** → **Video Prompt Agent**
2. Click **Run workflow** → **Run workflow**

### Check Results
- ✅ Google Doc created in Drive folder
- ✅ Sheet row marked "done"
- ✅ Telegram notification received

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Actions (every 3 hours or manual trigger)      │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  agent.py                                              │
│  1. Read pending topic from Google Sheet               │
│  2. Call NVIDIA API (Nemotron model)                   │
│  3. Create Google Doc with formatted prompts            │
│  4. Mark sheet row as "done"                           │
│  5. Send Telegram notification                         │
└─────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### "No pending topics found"
- Check that Column B is empty (not "done")
- Verify sheet is shared with service account

### "SERVICE_ACCOUNT_JSON not set"
- Make sure secret is set in GitHub
- JSON must be single line (no newlines)

### "Permission denied" errors
- Verify service account has correct roles
- Check sheet and folder are shared with service account email

### Telegram not working
- Verify bot token is correct
- Ensure you've started a chat with the bot first
- Check chat ID is numeric

---

## Cost Estimation

- **GitHub Actions (free tier)**: 2000 min/month
- **Agent runtime**: ~2-3 min per run
- **8 runs/day × 3 min**: 24 min/day → ~720 min/month ✅
- **NVIDIA API**: Pay per use (varies by model)

---

## Files Overview

| File | Purpose |
|------|---------|
| `agent.py` | Main Python script |
| `requirements.txt` | Python dependencies |
| `.github/workflows/agent.yml` | GitHub Actions workflow |
| `SETUP_GUIDE.md` | This file |

---

## Customization

Want to modify the agent? Here are options:

- **Change schedule**: Edit cron in `agent.yml` (e.g., `0 */6 * * *` for every 6 hours)
- **Different AI model**: Change `model` in `agent.py`
- **Additional logging**: Add more `logger.info()` calls
- **Retry logic**: Already included (3 retries for API calls)

---

*Setup complete! The agent will run automatically every 3 hours.*
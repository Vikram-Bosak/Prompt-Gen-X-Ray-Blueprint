# Video Prompt Agent

An automated YouTube Shorts video prompt generation agent that leverages NVIDIA's Nemotron model.

## Overview

This project automatically generates compelling scripts and prompts for YouTube Shorts based on topics provided in a Google Sheet. It uses GitHub Actions to run on a schedule, calls the NVIDIA API for AI generation, outputs the formatted prompts into a Google Doc, and sends notifications via a Telegram bot upon completion.

## Features

- **Automated Workflow**: Runs automatically via GitHub Actions (e.g., every 3 hours) or can be triggered manually.
- **Google Sheets Integration**: Reads pending video topics from a specified Google Sheet.
- **AI-Powered Generation**: Utilizes NVIDIA's Nemotron model to generate creative and engaging prompts for your Shorts.
- **Google Docs Export**: Automatically creates a structured Google Doc containing the generated script and prompts in a designated Google Drive folder.
- **Status Tracking**: Updates the Google Sheet row status to "done" once the video prompt generation is fully completed.
- **Telegram Notifications**: Sends a real-time Telegram message with a link to the generated Google Doc so you can instantly review the output.

## Architecture

1. **Trigger**: GitHub Actions scheduled workflow
2. **Input**: Google Sheets (reads pending topics)
3. **Processing**: Python script (`agent.py`) using NVIDIA API
4. **Output**: Google Docs (saves the generated output)
5. **Update**: Google Sheets (marks topic as "done")
6. **Notification**: Telegram bot

## Setup Instructions

Please see the [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed, step-by-step instructions on configuring the environment, enabling the necessary Google Cloud APIs, and setting up the required GitHub Secrets.

## Requirements

- Python 3.9+ 
- Dependencies are listed in `requirements.txt`
- Active GitHub account with Actions enabled
- Google Cloud Service Account with access to Google Sheets, Drive, and Docs APIs
- NVIDIA API key for Nemotron endpoints
- Telegram Bot token and chat ID

## Usage

Once configured according to the Setup Guide, the agent runs entirely hands-free. Simply add new topics to Column A of your Google Sheet. The agent will automatically detect pending topics, generate the scripts, and notify you on Telegram.

## License

This project is provided as-is. Feel free to fork and customize the workflow according to your own needs!
# Test Sat Mar 28 04:22:21 CET 2026
# Test Sat Mar 28 05:51:17 CET 2026

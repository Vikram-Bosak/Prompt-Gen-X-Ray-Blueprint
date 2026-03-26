import os
import json
import time
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

IST = ZoneInfo('Asia/Kolkata')

SHEET_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']

SYSTEM_PROMPT = """You are an expert YouTube Shorts video prompt generator for X-Ray/Animation channel.

OUTPUT FORMAT: JSON only - no markdown, no explanation.

Generate a complete 30-second YouTube Short video prompt with:

1. CHARACTER CARD - Define one consistent character for entire video:
   - Name/Role: Simple name suitable for all ages
   - Costume: FIXED - same throughout video (branding via clothing/props, never text overlay)
   - Hair + Skin Tone: Specific colors
   - Expression Range: Emotions character shows
   - Scale Reference: Human-scale reference for context

2. CAMERA JOURNEY PLAN - Single continuous camera for entire video:
   - ONE virtual camera that moves (pan/tilt/zoom/push-through/track/orbit)
   - NEVER switches cameras - continuous journey
   - Write camera directions (e.g., "Camera tilts UP", "Camera zooms IN")
   - Hard cut ONLY for location change

3. FIVE CLIPS (6 seconds each = 30 seconds total):

CLIP 1 (0s-6s) - CINEMATIC STORY ENTRY:
   - Scene setup with establishing shot
   - Introduce topic/context
   - VO: 20-25 words Hindi/Hinglish, natural hook

CLIP 2 (6s-12s) - KILLER HOOK:
   - Shocking fact or surprising reveal
   - Build curiosity
   - VO: 20-25 words Hindi/Hinglish

CLIP 3 (12s-18s) - X-RAY DIVE:
   - Inside body/mechanism/cross-section view
   - Visual explanation of what happens inside
   - VO: 20-25 words Hindi/Hinglish

CLIP 4 (18s-24s) - CLIMAX/CONFLICT:
   - Peak drama or critical moment
   - Maximum visual impact
   - VO: 20-25 words Hindi/Hinglish

CLIP FINAL (24s-30s) - PERFECT LOOP:
   - Connects back to CLIP 1 seamlessly
   - Last line of VO must loop to first line of CLIP 1
   - End on freeze frame or smooth transition point
   - VO: 20-25 words Hindi/Hinglish

For EACH CLIP provide:
- 🎥 CAMERA: Single camera movement instruction
- 👀 VISUAL: Scene description matching Character Card
- 🔊 SFX: Exact sound effects with timing (e.g., "Heartbeat at 0:03 | Splash at 0:05")
- 🎤 VO: Hindi/Hinglish voiceover 20-25 words

VIDEO PROMPTS per clip:
PROMPT A - IMAGE / Visual Action: 4K Ultra HD, 3D CGI Animation, [subject isolated only], detailed visual description
PROMPT B - IMAGE / Voiceover Concept: 4K Ultra HD, 3D CGI Animation, [diagram/cross-section isolated only], visual explanation
PROMPT C - VIDEO / Visual Action (SINGLE CAMERA): 4K Ultra HD, 3D CGI Animation, SINGLE CAMERA JOURNEY: Camera starts at [...] → moves to [...] → arrives at [...], CHARACTER LOCK: [hair] + [clothing] + [skin tone] + [expression], ANIMATION SEQUENCE with timecodes, SFX GUIDE
PROMPT D - VIDEO / Voiceover Diagram: 4K Ultra HD, 3D CGI Animation, CAMERA POSITION: neutral/static, ANIMATION SEQUENCE, SFX GUIDE

RULES:
- Language: Hindi/Hinglish only for voiceover
- NO "Hello दोस्तों", NO "Subscribe करें", NO outros
- Single camera system - NEVER switch cameras within a clip
- Character costume MUST be same across all clips
- CLIP FINAL VO last line should connect to CLIP 1 VO first line for loop effect

Return JSON format:
{
  "character_card": {...},
  "camera_journey": "...",
  "clips": [
    {
      "clip_number": 1,
      "time_range": "0s-6s",
      "title": "...",
      "camera": "...",
      "visual": "...",
      "sfx": "...",
      "vo": "...",
      "prompts": {
        "a": "...",
        "b": "...",
        "c": "...",
        "d": "..."
      }
    },
    ... (5 clips total)
  ]
}"""


def get_pending_topic(service):
    """Get the first pending video topic from Google Sheet."""
    sheet_id = os.environ.get('GOOGLE_SHEET_ID')
    range_name = 'Sheet1!A:B'
    
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=range_name
    ).execute()
    
    values = result.get('values', [])
    
    if not values or len(values) < 2:
        logger.error("Sheet is empty or has no data rows")
        return None, None, None
    
    for i, row in enumerate(values[1:], start=2):
        if len(row) < 1 or not row[0].strip():
            continue
        
        title = row[0].strip()
        status = row[1].strip().lower() if len(row) > 1 else ''
        
        if status != 'done':
            logger.info(f"Found pending topic: {title}")
            return title, i, 'A' if len(row) == 1 else 'B'
    
    logger.info("No pending topics found")
    return None, None, None


def mark_done(service, row_number):
    """Mark the row as done in Google Sheet."""
    sheet_id = os.environ.get('GOOGLE_SHEET_ID')
    range_name = f'Sheet1!B{row_number}'
    
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption='RAW',
        body={'values': [['done']]}
    ).execute()
    logger.info(f"Marked row {row_number} as done")


def generate_script(topic):
    """Generate video script using NVIDIA API."""
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.environ.get('NVIDIA_API_KEY')
    )
    
    user_prompt = f"""Generate video prompt for topic: {topic}

Create a complete 30-second animated video script following all rules:
- Single camera system (ONE camera, continuous movement)
- 5 clips × 6 seconds
- Hindi/Hinglish voiceover
- Character with fixed costume throughout
- X-Ray/inside view for CLIP 3
- Perfect loop ending

Topic: {topic}"""
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=1,
                top_p=0.95,
                max_tokens=8000,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": True},
                    "reasoning_budget": 8000
                }
            )
            
            content = response.choices[0].message.content
            
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("No JSON found in response, attempting full parse")
                return json.loads(content)
            
            return json.loads(content[json_start:json_end])
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise Exception(f"Failed to parse AI response after {max_retries} attempts")
            time.sleep(2)
        except Exception as e:
            logger.warning(f"API error (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(5)


def format_document_content(script, topic):
    """Format the script into Google Docs content structure."""
    lines = []
    
    lines.append(f"🎬 {topic}")
    lines.append(f"Generated: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST")
    lines.append("")
    
    cc = script.get('character_card', {})
    lines.append("👤 CHARACTER CARD")
    lines.append(f"  • Name/Role: {cc.get('Name/Role', 'N/A')}")
    lines.append(f"  • Costume (FIXED): {cc.get('Costume', 'N/A')}")
    lines.append(f"  • Hair + Skin Tone: {cc.get('Hair + Skin Tone', 'N/A')}")
    lines.append(f"  • Expression Range: {cc.get('Expression Range', 'N/A')}")
    lines.append(f"  • Scale Reference: {cc.get('Scale Reference', 'N/A')}")
    lines.append("")
    
    lines.append("🎥 CAMERA JOURNEY PLAN")
    lines.append(script.get('camera_journey', 'N/A'))
    lines.append("")
    lines.append("──────────────────────────────────────────────────")
    lines.append("")
    
    for clip in script.get('clips', []):
        clip_num = clip.get('clip_number', '')
        time_range = clip.get('time_range', '')
        title = clip.get('title', '')
        
        lines.append(f"CLIP {clip_num} ⏱ {time_range} — {title}")
        lines.append("──────────────────────────────────────────────────")
        lines.append(f"🎥 CAMERA: {clip.get('camera', 'N/A')}")
        lines.append(f"👀 VISUAL: {clip.get('visual', 'N/A')}")
        lines.append(f"🔊 SFX: {clip.get('sfx', 'N/A')}")
        lines.append(f"🎤 VO: {clip.get('vo', 'N/A')}")
        lines.append("")
        
        prompts = clip.get('prompts', {})
        lines.append("📸 VIDEO PROMPTS")
        lines.append(f"PROMPT A — IMAGE / Visual Action:")
        lines.append(prompts.get('a', 'N/A'))
        lines.append("")
        lines.append(f"PROMPT B — IMAGE / Voiceover Concept:")
        lines.append(prompts.get('b', 'N/A'))
        lines.append("")
        lines.append(f"PROMPT C — VIDEO / Visual Action (SINGLE CAMERA):")
        lines.append(prompts.get('c', 'N/A'))
        lines.append("")
        lines.append(f"PROMPT D — VIDEO / Voiceover Diagram:")
        lines.append(prompts.get('d', 'N/A'))
        lines.append("")
        lines.append("──────────────────────────────────────────────────")
        lines.append("")
    
    return [{'insertText': {'location': {'index': 0}, 'text': '\n'.join(lines)}}]


def create_google_doc(drive_service, docs_service, topic, script):
    """Create Google Doc in Drive folder."""
    folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
    
    file_metadata = {
        'name': topic,
        'mimeType': 'application/vnd.google-apps.document',
        'parents': [folder_id]
    }
    
    doc = drive_service.files().create(body=file_metadata, fields='id').execute()
    doc_id = doc.get('id')
    logger.info(f"Created Google Doc: {doc_id}")
    
    content = format_document_content(script, topic)
    
    for request in content:
        try:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': [request]}
            ).execute()
        except Exception as e:
            logger.warning(f"Error applying text format: {e}")
    
    return doc_id


def send_telegram_message(message):
    """Send notification via Telegram Bot."""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        logger.warning("Telegram credentials not configured")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
    
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            logger.info("Telegram notification sent")
        else:
            logger.warning(f"Telegram send failed: {response.status_code}")
    except Exception as e:
        logger.warning(f"Telegram error: {e}")


def send_error_notification(error_msg):
    """Send error notification to Telegram."""
    next_run = datetime.now(IST) + timedelta(hours=3)
    message = f"❌ Video Prompt Agent Error\n\n{error_msg}\n\n⏰ Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')} IST"
    send_telegram_message(message)


def get_gcp_credentials():
    """Get GCP credentials from service account JSON."""
    sa_json = os.environ.get('SERVICE_ACCOUNT_JSON')
    if not sa_json:
        raise ValueError("SERVICE_ACCOUNT_JSON not set")
    
    info = json.loads(sa_json)
    return service_account.Credentials.from_service_account_info(
        info, scopes=SHEET_SCOPES + DRIVE_SCOPES
    )


def main():
    """Main agent execution."""
    try:
        logger.info("Starting Video Prompt Agent")
        
        credentials = get_gcp_credentials()
        
        sheets_service = build('sheets', 'v4', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        docs_service = build('docs', 'v1', credentials=credentials)
        
        topic, row_number, _ = get_pending_topic(sheets_service)
        
        if not topic:
            logger.info("No pending topics. Exiting.")
            return
        
        script = generate_script(topic)
        
        doc_id = create_google_doc(drive_service, docs_service, topic, script)
        doc_link = f"https://docs.google.com/document/d/{doc_id}/edit"
        
        mark_done(sheets_service, row_number)
        
        next_run = datetime.now(IST) + timedelta(hours=3)
        success_msg = f"✅ Video Prompt Ready!\n\n🎬 Title: {topic}\n📄 Google Doc: [Link]({doc_link})\n🕐 Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST\n\n⏰ Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')} IST"
        
        send_telegram_message(success_msg)
        logger.info("Agent completed successfully")
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        send_error_notification(error_msg)
        raise


if __name__ == '__main__':
    from datetime import timedelta
    main()
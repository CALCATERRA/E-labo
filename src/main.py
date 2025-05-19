from appwrite.client import Client
from appwrite.exception import AppwriteException
import os
import json
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime

# Headers CORS
cors_headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, x-appwrite-key",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Credentials": "true"
}

def main(context):
    # Inizializza Appwrite Client
    client = (
        Client()
        .set_endpoint(os.environ["APPWRITE_FUNCTION_API_ENDPOINT"])
        .set_project(os.environ["APPWRITE_FUNCTION_PROJECT_ID"])
        .set_key(context.req.headers["x-appwrite-key"])
    )

    context.log("✅ Connessione Appwrite OK.")

    if context.req.method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": cors_headers,
            "body": ""
        }

    if context.req.path == "/ping":
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": "Pong"
        }

    if context.req.method == "POST":
        try:
            # Estrai dati
            data = context.req.body if isinstance(context.req.body, dict) else json.loads(context.req.body)
            user_msg = data.get("msg", "").strip()
            history = data.get("history", [])

            # Carica prompt.json
            with open(os.path.join(os.path.dirname(__file__), "prompt.json"), "r") as f:
                prompt_data = json.load(f)

            system_instruction = prompt_data.get("system_instruction", "")

            # Costruzione del prompt
            sorted_messages = history[-10:]
            prompt_parts = [{"text": system_instruction + "\n"}]

            for m in sorted_messages:
                prompt_parts.append({"text": f"Utente: {m.get('message', '')}\n"})

            prompt_parts.append({"text": f"Utente: {user_msg}\n"})

            # === Google Calendar Integration ===
            credentials_info = json.loads(os.environ.get("credentials"))
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            service = build('calendar', 'v3', credentials=credentials)

            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            if not events:
                calendar_summary = "Non ci sono eventi nel calendario."
            else:
                calendar_summary = "Ecco i prossimi eventi:\n"
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    calendar_summary += f"- {event.get('summary', 'Senza titolo')} | Inizio: {start}\n"

            # Configura Gemini
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")

            # Chiamata a Gemini
            response = model.generate_content(
                prompt_parts,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 65536,
                    "top_k": 64,
                    "top_p": 0.95
                }
            )

            # Risposta finale con calendario incluso
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({
                    "reply": response.text,
                    "calendar": calendar_summary
                })
            }

        except Exception as e:
            context.error(f"❌ Errore durante la generazione: {e}")
            return {
                "statusCode": 500,
                "headers": cors_headers,
                "body": json.dumps({"error": str(e)})
            }

    return {
        "statusCode": 200,
        "headers": cors_headers,
        "body": json.dumps({
            "info": "Usa POST con {'msg': '...'} e 'history': [...] per parlare con Gemini."
        })
    }


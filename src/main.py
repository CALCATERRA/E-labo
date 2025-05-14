from appwrite.client import Client
from appwrite.exception import AppwriteException
import os
import json
import google.generativeai as genai

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

    # Gestione preflight OPTIONS
    if context.req.method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": cors_headers,
            "body": ""
        }

    # Test semplice
    if context.req.path == "/ping":
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": "Pong"
        }

    # Gestione POST
    if context.req.method == "POST":
        try:
            # Leggi messaggio utente e storia della chat
            data = context.req.body if isinstance(context.req.body, dict) else json.loads(context.req.body)
            user_msg = data.get("msg", "").strip()
            history = data.get("history", [])

            # Carica il prompt da prompt.json
            try:
                with open(os.path.join(os.path.dirname(__file__), "prompt.json"), "r") as f:
                    prompt_data = json.load(f)
                    intro_prompt = prompt_data if isinstance(prompt_data, str) else prompt_data.get("prompt", "")
            except Exception as e:
                context.log(f"⚠️ Errore caricamento prompt.json: {e}")
                intro_prompt = ""

            # Prepara cronologia per Gemini (max 10 messaggi)
            trimmed_history = history[-10:]
            conversation = []
            for h in trimmed_history:
                if h["role"] not in ["user", "model"]:
                    continue
                conversation.append({"role": h["role"], "parts": [h["text"]]})

            # Configura Gemini
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")

            chat = model.start_chat(
                history=conversation,
                system_instruction=intro_prompt
            )

            # Invia messaggio
            response = chat.send_message(user_msg)

            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({"reply": response.text})
            }

        except Exception as e:
            context.error(f"❌ Errore durante la generazione: {e}")
            return {
                "statusCode": 500,
                "headers": cors_headers,
                "body": json.dumps({"error": str(e)})
            }

    # Risposta predefinita
    return {
        "statusCode": 200,
        "headers": cors_headers,
        "body": json.dumps({
            "info": "Usa POST con {'msg': '...'} e 'history': [...] per parlare con Gemini."
        })
    }

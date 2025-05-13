from appwrite.client import Client
from appwrite.exception import AppwriteException
import os
import json
import google.generativeai as genai

def main(context):
    # Inizializza Appwrite Client
    client = (
        Client()
        .set_endpoint(os.environ["APPWRITE_FUNCTION_API_ENDPOINT"])
        .set_project(os.environ["APPWRITE_FUNCTION_PROJECT_ID"])
        .set_key(context.req.headers["x-appwrite-key"])
    )

    context.log("✅ Connessione Appwrite OK.")

    # Headers CORS comuni
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, x-appwrite-key"
    }

    # Gestione preflight OPTIONS
    if context.req.method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": cors_headers,
            "body": ""
        }

    # Ping
    if context.req.path == "/ping":
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": "Pong"
        }

    # POST con messaggio utente
    if context.req.method == "POST":
        try:
            data = json.loads(context.req.body.decode("utf-8"))
            user_msg = data.get("msg", "").strip()

            # Prompt personalizzato
            intro_prompt = ""
            try:
                with open("prompt.json", "r") as f:
                    prompt_data = json.load(f)
                    intro_prompt = prompt_data.get("intro", "")
            except Exception as e:
                context.log(f"⚠️ Nessun prompt.json trovato o errore: {e}")

            full_prompt = f"{intro_prompt}\n\nUtente: {user_msg}"

            # Gemini API
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")
            response = model.generate_content(full_prompt)

            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({ "reply": response.text })
            }

        except Exception as e:
            context.error(f"❌ Errore durante la generazione: {e}")
            return {
                "statusCode": 500,
                "headers": cors_headers,
                "body": json.dumps({ "error": str(e) })
            }

    # Messaggio generico
    return {
        "statusCode": 200,
        "headers": cors_headers,
        "body": json.dumps({
            "info": "Usa POST con {'msg': '...'} per parlare con Gemini."
        })
    }

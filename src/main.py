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
            try:
                with open(os.path.join(os.path.dirname(__file__), "prompt.json"), "r") as f:
                    prompt_data = json.load(f)
                    system_instruction = prompt_data.get("system_instruction", "")
            except Exception as e:
                context.log(f"⚠️ Errore caricamento prompt.json: {e}")
                system_instruction = ""

            # Prepara contesto per Gemini
            prompt_parts = []
            if system_instruction:
                prompt_parts.append({"text": system_instruction + "\n"})

            # Aggiungi gli ultimi 10 scambi dalla history
            for h in history[-10:]:
                role_prefix = "Utente" if h["role"] == "user" else "Simone"
                prompt_parts.append({"text": f"{role_prefix}: {h['text']}\n"})

            # Aggiungi l'ultimo messaggio utente
            prompt_parts.append({"text": f"Utente: {user_msg}\nSimone:"})

            # Configura Gemini
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")

            # Chiamata a Gemini
            response = model.generate_content(
                prompt_parts,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 1,
                    "top_k": 40,
                    "max_output_tokens": 512,
                }
            )

            reply_text = response.text.strip() if hasattr(response, "text") else "🤖 Nessuna risposta."

            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({"reply": reply_text})
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

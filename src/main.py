from appwrite.client import Client
from appwrite.exception import AppwriteException
import os
import json
import google.generativeai as genai

# Headers CORS da aggiungere a tutte le risposte
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
            # Leggi messaggio utente e storia della chat dal body
            data = context.req.body if isinstance(context.req.body, dict) else json.loads(context.req.body)
            user_msg = data.get("msg", "").strip()
            history = data.get("history", [])  # deve essere una lista di dizionari [{role: 'user'|'model', text: '...'}]

            # Carica il prompt da prompt.json
        with open(os.path.join(os.path.dirname(__file__), "prompt.json"), "r") as f:
            intro_prompt = json.load(f)
            except Exception as e:
                context.log(f"⚠️ Nessun prompt.json trovato o errore: {e}")

            # Prepara la conversazione (max ultimi 10 messaggi)
            trimmed_history = history[-10:]  # massimo 10 scambi
            conversation = []
            for h in trimmed_history:
                if h["role"] not in ["user", "model"]:
                    continue
                conversation.append({"role": h["role"], "parts": [h["text"]]})

            # Aggiungi il prompt di introduzione come messaggio utente iniziale se esiste
            if intro_prompt:
                conversation.insert(0, {"role": "user", "parts": [intro_prompt]})

            # Aggiungi l'ultimo messaggio dell'utente
            conversation.append({"role": "user", "parts": [user_msg]})

            # Configura Gemini
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")

            # Chiamata a Gemini
            response = model.generate_content(
                contents=conversation,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 1,
                    "top_k": 40,
                    "max_output_tokens": 512,
                }
            )

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

    # Risposta di default per altri metodi
    return {
        "statusCode": 200,
        "headers": cors_headers,
        "body": json.dumps({
            "info": "Usa POST con {'msg': '...'} e 'history': [...] per parlare con Gemini."
        })
    }

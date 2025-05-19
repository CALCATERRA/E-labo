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
    try:
        context.log("🚀 Funzione avviata.")  # <-- LOG INIZIALE

        # Inizializza Appwrite Client
        client = (
            Client()
            .set_endpoint(os.environ["APPWRITE_FUNCTION_API_ENDPOINT"])
            .set_project(os.environ["APPWRITE_FUNCTION_PROJECT_ID"])
            .set_key(context.req.headers["x-appwrite-key"])
        )

        context.log("✅ Connessione Appwrite OK.")

        if context.req.method == "OPTIONS":
            context.log("ℹ️ Richiesta OPTIONS ricevuta.")
            return {
                "statusCode": 204,
                "headers": cors_headers,
                "body": ""
            }

        if context.req.path == "/ping":
            context.log("📡 Ping ricevuto.")
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": "Pong"
            }

        if context.req.method == "POST":
            try:
                context.log("📥 Richiesta POST ricevuta.")
                data = context.req.body if isinstance(context.req.body, dict) else json.loads(context.req.body)
                user_msg = data.get("msg", "").strip()
                history = data.get("history", [])
                context.log(f"📝 Messaggio utente: {user_msg}")
                context.log(f"🕓 Lunghezza cronologia: {len(history)}")

                prompt_path = os.path.join(os.path.dirname(__file__), "prompt.json")
                context.log(f"📦 prompt.json path: {prompt_path}")
                if not os.path.exists(prompt_path):
                    raise FileNotFoundError("prompt.json non trovato nella funzione.")

                with open(prompt_path, "r") as f:
                    prompt_data = json.load(f)

                system_instruction = prompt_data.get("system_instruction", "")
                context.log("📄 Prompt di sistema caricato.")

                sorted_messages = history[-10:]
                prompt_parts = [{"text": system_instruction + "\n"}]
                for m in sorted_messages:
                    prompt_parts.append({"text": f"Utente: {m.get('message', '')}\n"})
                prompt_parts.append({"text": f"Utente: {user_msg}\n"})

                gemini_api_key = os.environ.get("GEMINI_API_KEY")
                if not gemini_api_key:
                    raise EnvironmentError("Variabile GEMINI_API_KEY non impostata.")

                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")
                context.log("🤖 Modello Gemini configurato. Chiamata in corso...")

                response = model.generate_content(
                    prompt_parts,
                    generation_config={
                        "temperature": 0.7,
                        "max_output_tokens": 65536,
                        "top_k": 64,
                        "top_p": 0.95
                    }
                )

                context.log("✅ Risposta generata.")
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

        context.log("ℹ️ Metodo non gestito.")
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps({
                "info": "Usa POST con {'msg': '...'} e 'history': [...] per parlare con Gemini."
            })
        }

    except Exception as e:
        context.error(f"💥 Errore globale nella funzione main: {e}")
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": str(e)})
        }

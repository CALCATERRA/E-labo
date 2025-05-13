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

    # ✅ Verifica connessione Appwrite
    context.log("✅ Connessione Appwrite OK.")

    # ✅ Gestione preflight CORS
    if context.req.method == "OPTIONS":
        return context.res.empty().with_headers({
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, x-appwrite-key"
        })

    # 👉 Ping di test
    if context.req.path == "/ping":
        return context.res.text("Pong").with_headers({
            "Access-Control-Allow-Origin": "*"
        })

    # 👉 POST con messaggio utente
    if context.req.method == "POST":
        try:
            # 🔄 Correzione per il parsing del body
            data = json.loads(context.req.body.decode("utf-8"))
            user_msg = data.get("msg", "").strip()

            # 🔍 Leggi il prompt personalizzato da prompt.json
            intro_prompt = ""
            try:
                with open("prompt.json", "r") as f:
                    prompt_data = json.load(f)
                    intro_prompt = prompt_data.get("intro", "")
            except Exception as e:
                context.log(f"⚠️ Nessun prompt.json trovato o errore: {e}")

            # ✍️ Componi il prompt finale
            full_prompt = f"{intro_prompt}\n\nUtente: {user_msg}"

            # ✅ Configura Gemini
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")

            # 🚀 Genera risposta
            response = model.generate_content(full_prompt)

            # ✅ Ritorna la risposta al client con header CORS
            return context.res.json({"reply": response.text}).with_headers({
                "Access-Control-Allow-Origin": "*"
            })

        except Exception as e:
            context.error(f"❌ Errore durante la generazione: {e}")
            return context.res.json({"error": str(e)}).with_status(500).with_headers({
                "Access-Control-Allow-Origin": "*"
            })

    # ℹ️ Messaggio di default
    return context.res.json({
        "info": "Usa POST con {'msg': '...'} per parlare con Gemini."
    }).with_headers({
        "Access-Control-Allow-Origin": "*"
    })

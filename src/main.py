from appwrite.client import Client
from appwrite.services.users import Users
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
        .set_key(os.environ["APPWRITE_FUNCTION_API_KEY"])  # Usiamo la chiave direttamente dalle variabili d'ambiente
    )
    
    # Test di connessione ad Appwrite
    users = Users(client)
    try:
        response = users.list()
        context.log(f"✅ Connessione Appwrite OK - Utenti trovati: {response['total']}")
    except AppwriteException as err:
        context.error(f"❌ Errore di connessione ad Appwrite: {err}")
        return context.res.json({"error": "Connessione a Appwrite fallita"}, status_code=500)

    # Ping di test
    if context.req.path == "/ping":
        return context.res.text("Pong")

    # POST con messaggio utente
    if context.req.method == "POST":
        try:
            data = context.req.json()
            user_msg = data.get("msg", "").strip()

            if not user_msg:
                return context.res.json({"error": "Messaggio vuoto"}, status_code=400)

            # Leggi il prompt personalizzato da prompt.json
            intro_prompt = ""
            try:
                with open("prompt.json", "r") as f:
                    prompt_data = json.load(f)
                    intro_prompt = prompt_data.get("intro", "")
                    context.log("✅ Prompt personalizzato caricato correttamente.")
            except Exception as e:
                context.log(f"⚠️ Nessun prompt.json trovato o errore durante la lettura: {e}")

            # Componi il prompt finale
            full_prompt = f"{intro_prompt}\n\nUtente: {user_msg}"
            context.log(f"✏️ Prompt inviato a Gemini: {full_prompt}")

            # Configura Gemini
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")

            # Genera risposta
            response = model.generate_content(full_prompt)

            if response and response.text:
                context.log("✅ Risposta ricevuta da Gemini")
                return context.res.json({"reply": response.text})
            else:
                context.log("⚠️ Nessuna risposta ricevuta da Gemini")
                return context.res.json({"reply": "Nessuna risposta disponibile."}, status_code=500)

        except Exception as e:
            context.error(f"❌ Errore durante la generazione della risposta: {e}")
            return context.res.json({"error": str(e)}, status_code=500)

    return context.res.json({
        "info": "Usa POST con {'msg': '...'} per parlare con Gemini."
    })

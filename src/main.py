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
        .set_key(context.req.headers["x-appwrite-key"])
    )
    users = Users(client)

    try:
        response = users.list()
        context.log("Totale utenti: " + str(response["total"]))
    except AppwriteException as err:
        context.error("Errore Appwrite: " + repr(err))

    # Ping di test
    if context.req.path == "/ping":
        return context.res.text("Pong")

    # POST con messaggio utente
    if context.req.method == "POST":
        try:
            # 🔄 Correzione per il parsing del body
            data = json.loads(context.req.body)
            user_msg = data.get("msg", "").strip()

            # Leggi il prompt personalizzato da prompt.json
            intro_prompt = ""
            try:
                with open("prompt.json", "r") as f:
                    prompt_data = json.load(f)
                    intro_prompt = prompt_data.get("intro", "")
            except Exception as e:
                context.log(f"Nessun prompt.json trovato o errore: {e}")

            # Componi prompt finale
            full_prompt = f"{intro_prompt}\n\nUtente: {user_msg}"

            # Configura Gemini
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")

            # Genera risposta
            response = model.generate_content(full_prompt)

            return context.res.json({"reply": response.text})

        except Exception as e:
            context.error(f"Errore durante la generazione: {e}")
            context.res.status = 500  # 🔄 Correzione dello status
            return context.res.json({"error": str(e)})

    return context.res.json({
        "info": "Usa POST con {'msg': '...'} per parlare con Gemini."
    })

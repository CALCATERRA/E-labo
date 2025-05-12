from appwrite.client import Client
from appwrite.services.users import Users
from appwrite.exception import AppwriteException
import os
import json
import google.generativeai as genai

def main(context):
    # Inizializza Appwrite
    client = (
        Client()
        .set_endpoint(os.environ["APPWRITE_FUNCTION_API_ENDPOINT"])
        .set_project(os.environ["APPWRITE_FUNCTION_PROJECT_ID"])
        .set_key(context.req.headers["x-appwrite-key"])
    )
    users = Users(client)

    try:
        response = users.list()
        context.log("Total users: " + str(response["total"]))
    except AppwriteException as err:
        context.error("Could not list users: " + repr(err))

    if context.req.path == "/ping":
        return context.res.text("Pong")

    if context.req.method == "POST":
        try:
            body = context.req.json()
            user_msg = body.get("msg", "").strip()

            # Leggi prompt.json (se presente)
            intro_prompt = ""
            try:
                with open("prompt.json", "r") as f:
                    prompt_data = json.load(f)
                    intro_prompt = prompt_data.get("intro", "")
            except Exception as e:
                context.log(f"Nessun prompt.json o errore nel leggerlo: {e}")

            # Componi prompt per Gemini
            full_prompt = f"{intro_prompt}\n\nUtente: {user_msg}"

            # Inizializza Gemini
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(full_prompt)

            return context.res.json({"reply": response.text})

        except Exception as e:
            context.error(f"Errore: {e}")
            return context.res.json({"error": str(e)}, status_code=500)

    return context.res.json({"info": "Invia una richiesta POST con {'msg': '...'} per ottenere una risposta da Gemini."})

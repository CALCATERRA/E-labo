import google.generativeai as genai
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Imposta la tua chiave API Gemini da variabile ambiente
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Inizializza il modello
model = genai.GenerativeModel("gemini-1.5-flash")

@app.route("/", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_message = data.get("msg", "")

        if not user_message:
            return jsonify({"reply": "Messaggio vuoto."}), 400

        response = model.generate_content(user_message)
        reply_text = response.text.strip()

        return jsonify({"reply": reply_text})
    
    except Exception as e:
        return jsonify({"reply": f"Errore interno: {str(e)}"}), 500


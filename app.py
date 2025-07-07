from flask import Flask, render_template, request, jsonify
import openai
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Inicializa cliente OpenAI com a nova API
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("chatbot.html")

@app.route("/send", methods=["POST"])
def send():
    data = request.get_json()
    user_message = data.get("message")
    print(f"Mensagem recebida do usuário: {user_message}")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        bot_reply = response.choices[0].message.content.strip()
        print(f"Resposta gerada pela IA: {bot_reply}")
        return jsonify({"reply": bot_reply})
    except Exception as e:
        print(f"Erro na chamada da API OpenAI: {e}")
        return jsonify({"reply": f"Erro: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)

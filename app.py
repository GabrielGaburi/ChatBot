from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Inicializa cliente OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
            model="gpt-4",  # Use gpt-3.5-turbo se não tiver acesso ao 4
            messages=[
                {
                    "role": "system",
                        "content": (
                            "Você é um assistente empático e acolhedor que conversa com pessoas afetadas pelo vício em apostas. "
                            "Suas respostas devem ser curtas, diretas e sensíveis ao sofrimento do usuário. "
                            "Jamais incentive, ensine ou cite qualquer tipo de aposta, jogo ou site relacionado. "
                            "Você não deve sair do tema de vício em apostas, nem fornecer links ou sugestões externas. "
                            "Seu foco é ouvir, acolher, validar sentimentos e, quando possível, oferecer conselhos breves de apoio emocional."
                    )
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.7
        )

        bot_reply = response.choices[0].message.content.strip()
        print(f"Resposta gerada pela IA: {bot_reply}")
        return jsonify({"reply": bot_reply})

    except Exception as e:
        print(f"Erro na chamada da API OpenAI: {e}")
        return jsonify({"reply": f"Erro: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)

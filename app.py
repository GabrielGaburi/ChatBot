from flask import Flask, render_template, request, jsonify
import os
import uuid
from dotenv import load_dotenv
import openai

# Carrega variáveis de ambiente
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Armazena sessões na memória
usuarios_humano = set()  # sessões que pediram profissional
# sessions: { session_id: [ {id: "uuid", sender: "user"/"bot"/"human", text: "..."} ] }
sessions = {}

# ---------------- Rotas de páginas ---------------- #
@app.route("/")
def home():
    return render_template("chatbot.html")

@app.route("/painel")
def painel():
    return render_template("painel.html")

# ---------------- APIs do painel ---------------- #
@app.route("/lista_sessoes")
def lista_sessoes():
    # retorna lista de sessões que pediram humano
    return jsonify(list(usuarios_humano))

@app.route("/mensagens/<session_id>")
def mensagens(session_id):
    # retorna histórico completo (front faz dedupe/render incremental)
    return jsonify(sessions.get(session_id, []))

@app.route("/enviar_profissional/<session_id>", methods=["POST"])
def enviar_profissional(session_id):
    data = request.get_json(force=True) or {}
    texto = (data.get("message") or "").strip()
    if not texto:
        return jsonify({"ok": False, "error": "Mensagem vazia"}), 400

    msg_id = str(uuid.uuid4())
    sessions.setdefault(session_id, []).append({
        "id": msg_id, "sender": "human", "text": texto
    })
    print(f"[PROFISSIONAL -> {session_id}] {texto}")
    return jsonify({"ok": True, "id": msg_id})

@app.route("/perfil/meu")
def perfil_meu():
    perfil = {
        "nome": "Dr. Gabriel",
        "especialidade": "Psicólogo Clínico",
        "biografia": "Experiência no atendimento a vícios e suporte emocional."
    }
    return jsonify(perfil)

# ---------------- APIs do usuário ---------------- #
@app.route("/status_sessao/<session_id>")
def status_sessao(session_id):
    # (mantemos só UMA rota /status_sessao)
    return jsonify({"humano": session_id in usuarios_humano})

@app.route("/transfer", methods=["POST"])
def transfer():
    data = request.get_json(force=True) or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "message": "session_id não informado"}), 400

    usuarios_humano.add(session_id)
    sessions.setdefault(session_id, [])
    sessions[session_id].append({
        "id": str(uuid.uuid4()),
        "sender": "bot",
        "text": "Você será atendido por um profissional em instantes. Aguarde aqui."
    })

    print(f"[TRANSFER] Sessão {session_id} marcada para atendimento humano")
    return jsonify({"status": "ok", "message": "Pedido de atendimento humano recebido."})

@app.route("/encerrar/<session_id>", methods=["POST"])
def encerrar(session_id):
    usuarios_humano.discard(session_id)
    if session_id in sessions:
        sessions[session_id].append({
            "id": str(uuid.uuid4()),
            "sender": "bot",
            "text": "A conversa com o profissional foi encerrada. Volte quando quiser conversar novamente."
        })
    return jsonify({"ok": True})

@app.route("/send", methods=["POST"])
def send():
    data = request.get_json(force=True) or {}
    user_message = (data.get("message") or "").strip()
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"reply": "Sessão não identificada."}), 400

    sessions.setdefault(session_id, [])

    # salva mensagem do usuário (sempre, para histórico)
    user_msg_id = str(uuid.uuid4())
    sessions[session_id].append({"id": user_msg_id, "sender": "user", "text": user_message})
    print(f"[USUÁRIO {session_id}] {user_message}")

    # Se pediu humano, IA não responde
    if session_id in usuarios_humano:
        print(f"[AGUARDANDO PROFISSIONAL] {session_id} - IA desligada")
        # opcional: retornar id da msg do usuário para o front deduplicar render local
        return jsonify({"reply": "Um profissional está atendendo você. Aguarde a resposta dele aqui.", "id": user_msg_id})

    # Resposta da IA
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um amigo empático e confiável, pronto para conversar com alguém que enfrenta dificuldades com o vício em apostas. "
                        "Converse de forma acolhedora, sem julgar, com frases curtas e gentis. "
                        "Não recomende links/serviços, nem incentive apostas. Foque em validar sentimentos e apoiar."
                    )
                },
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )
        bot_reply = response.choices[0].message.content.strip()
        bot_msg_id = str(uuid.uuid4())
        sessions[session_id].append({"id": bot_msg_id, "sender": "bot", "text": bot_reply})
        print(f"[IA -> {session_id}] {bot_reply}")
        # Agora retorna também o ID para o front deduplicar
        return jsonify({"reply": bot_reply, "id": bot_msg_id})

    except Exception as e:
        print(f"[ERRO IA] {e}")
        return jsonify({"reply": f"Erro: {str(e)}"})

if __name__ == "__main__":
    # Em dev: debug=True. Em produção: use servidor WSGI (gunicorn/uwsgi) e desative debug.
    app.run(debug=True)

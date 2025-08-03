from flask import Flask, render_template, request, jsonify
import openai
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Armazena sessões na memória
usuarios_humano = set()  # sessões que pediram profissional
sessions = {}  # {session_id: [ {sender: "user"/"bot"/"human", "text": "..."} ]}

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
    return jsonify(list(usuarios_humano))

@app.route("/mensagens/<session_id>")
def mensagens(session_id):
    return jsonify(sessions.get(session_id, []))

@app.route("/enviar_profissional/<session_id>", methods=["POST"])
def enviar_profissional(session_id):
    data = request.get_json()
    texto = data.get("message", "").strip()
    if not texto:
        return jsonify({"ok": False, "error": "Mensagem vazia"})
    # adiciona mensagem ao histórico
    sessions.setdefault(session_id, []).append({"sender": "human", "text": texto})
    print(f"[PROFISSIONAL] para {session_id}: {texto}")
    return jsonify({"ok": True})

@app.route("/perfil/meu")
def perfil_meu():
    # Mock - substitua por dados reais depois
    perfil = {
        "nome": "Dr. Gabriel",
        "especialidade": "Psicólogo Clínico",
        "biografia": "Experiência no atendimento a vícios e suporte emocional."
    }
    return jsonify(perfil)

# ---------------- APIs do usuário ---------------- #
# ... (todo o código anterior igual)

# ---------------- APIs do usuário ---------------- #
@app.route("/status_sessao/<session_id>")
def verificar_status_sessao(session_id):  # Nome diferente aqui
    return jsonify({"humano": session_id in usuarios_humano})

@app.route("/transfer", methods=["POST"])
def transfer():
    data = request.get_json()
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"status": "error", "message": "session_id não informado"}), 400

    usuarios_humano.add(session_id)
    sessions.setdefault(session_id, [])
    sessions[session_id].append({
        "sender": "bot",
        "text": "Você será atendido por um profissional em instantes. Aguarde aqui."
    })

    print(f"[TRANSFER] Sessão {session_id} marcada para atendimento humano")
    return jsonify({"status": "ok", "message": "Pedido de atendimento humano recebido."})

# ... (continua normalmente com a função send e o restante do código)


@app.route("/encerrar/<session_id>", methods=["POST"])
def encerrar(session_id):
    usuarios_humano.discard(session_id)
    if session_id in sessions:
        sessions[session_id].append({
            "sender": "bot",
            "text": "A conversa com o profissional foi encerrada. Volte quando quiser conversar novamente."
        })
    return jsonify({"ok": True})


@app.route("/status_sessao/<session_id>")
def status_sessao(session_id):
    return jsonify({"humano": session_id in usuarios_humano})

@app.route("/send", methods=["POST"])
def send():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"reply": "Sessão não identificada."}), 400

    # 👉 Se não existir histórico, inicializa um novo
    if session_id not in sessions:
        sessions[session_id] = []

    # 👉 Zerar histórico se necessário: basta limpar ao criar
    # sessions[session_id] = []  # descomente se quiser sempre começar do zero

    # salva mensagem do usuário
    sessions[session_id].append({"sender": "user", "text": user_message})
    print(f"[USUÁRIO {session_id}] {user_message}")

    # 👉 Se a sessão está aguardando humano, IA não responde
    if session_id in usuarios_humano:
        print(f"[AGUARDANDO PROFISSIONAL] {session_id} - IA desligada")
        return jsonify({"reply": "Um profissional está atendendo você. Aguarde a resposta dele aqui."})

    # 👉 Caso contrário, responde com IA
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente empático e próximo, alguém que conversa de coração aberto com pessoas afetadas pelo vício em apostas. "
                        "Fale como um amigo que quer ajudar, validando sentimentos, mostrando compreensão e carinho. "
                        "Suas respostas devem ser curtas, diretas e cheias de humanidade, como alguém que está ali para ouvir e apoiar. "
                        "Jamais diga apenas que não pode ajudar ou que precisa procurar um profissional – você deve tentar ajudar com palavras de conforto e dicas práticas simples para lidar com o vício e o sofrimento. "
                        "Nunca incentive ou ensine qualquer tipo de aposta, jogo ou site relacionado. "
                        "Não forneça links, telefones ou recomendações de serviços externos. "
                        "Mantenha o foco em acolher, ouvir, validar e oferecer conselhos breves, como alguém próximo que está disposto a conversar, encorajar e ajudar a pessoa a se sentir menos sozinha. "
                        "Use linguagem simples, frases curtas e um tom humano e acolhedor. "
                        "Se a pessoa compartilhar dores ou frustrações, responda com empatia e apoio, sem julgamentos."
                    )
                },
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )
        bot_reply = response.choices[0].message.content.strip()
        sessions[session_id].append({"sender": "bot", "text": bot_reply})
        print(f"[IA] para {session_id}: {bot_reply}")
        return jsonify({"reply": bot_reply})

    except Exception as e:
        print(f"[ERRO IA] {e}")
        return jsonify({"reply": f"Erro: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)

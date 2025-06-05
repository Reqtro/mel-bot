import os
import requests
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CallbackContext

# URL atualizada do seu Web App do Google Apps Script
GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbwu1jj8sINXMlbPb1RoAi9YgCddfIjQ-1FDwITJ1aplDJLv892chav0mfHkWpaAX-si/exec"

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

app = Flask(__name__)

def cumprimento_por_horario():
    hora_utc = datetime.utcnow()
    hora_brasil = hora_utc - timedelta(hours=3)
    hora = hora_brasil.hour
    if 6 <= hora < 12:
        return "Bom dia"
    elif 12 <= hora < 18:
        return "Boa tarde"
    else:
        return "Boa noite"

def responder(update: Update, context: CallbackContext):
    msg = update.message.text.lower()
    usuario = update.message.from_user.first_name

    if "@mel" not in msg:
        return

    cumprimento = cumprimento_por_horario()

    if any(p in msg for p in ["apresente-se", "apresenta-se", "apresentar", "se mostrar"]):
        resposta = (
            f"{cumprimento}, {usuario}!\n\n"
            "Eu sou a @Mel, a assistente do Sensor de Nível. "
            "Estou aqui para ajudar na obtenção de informações sobre o nível e o status atual do abastecimento da caixa d'água.\n\n"
            "Para que eu diga qual é o nível atual de água, basta me chamar assim: \"@Mel qual é o nível?\"\n"
            "Para saber qual é o status do abastecimento, me chame assim: \"@Mel qual é o abs?\"\n"
            "E para saber quais são os links do mostrador do nível e do status do abastecimento, é só me chamar assim: \"@Mel me mande os links\"\n"
            "Pronto facinho né?  Vamos tentar?"
        )
        bot.send_message(chat_id=update.effective_chat.id, text=resposta)
        return

    try:
        response = requests.get(GOOGLE_SHEETS_URL)
        dados = response.json()
        nivel = dados.get("nivel")
        abastecimento = dados.get("abastecimento")
    except Exception:
        nivel = None
        abastecimento = None

    if any(p in msg for p in ["qual o nível", "qual o nivel", "nível?", "nivel?", "nível", "nivel"]):
        if nivel is not None:
            resposta = f"{cumprimento}, o nível atual é: {nivel}"
        else:
            resposta = f"{cumprimento}, não consegui obter o nível agora."
        bot.send_message(chat_id=update.effective_chat.id, text=resposta)
        return

    if any(p in msg for p in ["qual o abs", "abs?", "abs", "abastecimento", "status do abastecimento"]):
        if abastecimento is not None:
            resposta = f"{cumprimento}, o status do abastecimento é: {abastecimento}"
        else:
            resposta = f"{cumprimento}, não consegui obter o status do abastecimento agora."
        bot.send_message(chat_id=update.effective_chat.id, text=resposta)
        return

    if any(p in msg for p in ["me mande os links", "link", "links", "os links", "sites", "os sites"]):
        resposta = (
            "O link do nível da caixa é:\n"
            "https://docs.google.com/spreadsheets/d/e/2PACX-1vSGQUHrkneAPzQ8_mkF7whwPMJBD_YOEoW9-a717T00lGm8w0J0wpUjgkHkZPh_rU9goDdBhD5bU5u0/pubchart?oid=117157366&format=interactive\n\n"
            "O link do status do Abastecimento é:\n"
            "https://docs.google.com/spreadsheets/d/e/2PACX-1vSGQUHrkneAPzQ8_mkF7whwPMJBD_YOEoW9-a717T00lGm8w0J0wpUjgkHkZPh_rU9goDdBhD5bU5u0/pubchart?oid=1264620463&format=interactive"
        )
        bot.send_message(chat_id=update.effective_chat.id, text=resposta)
        return

    bot.send_message(chat_id=update.effective_chat.id, text=f"{cumprimento}, Ixi... Não posso te ajudar com isso...")

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok', 200

@app.route('/')
def home():
    return 'Bot @Mel rodando com webhook!', 200

if __name__ == "__main__":
    from telegram.ext import Dispatcher
    dispatcher = Dispatcher(bot, None, use_context=True)
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), responder))

    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT)

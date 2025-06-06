import os
import requests
from datetime import datetime, timedelta
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, MessageHandler, Filters, CallbackContext

TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbwu1jj8sINXMlbPb1RoAi9YgCddfIjQ-1FDwITJ1aplDJLv892chav0mfHkWpaAX-si/exec"

bot = Bot(token=TOKEN)
app = Flask(__name__)

dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0, use_context=True)

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
    cumprimento = cumprimento_por_horario()

    if "@mel" not in msg:
        return

    if any(p in msg for p in ["apresente-se", "apresenta-se", "apresentar", "se mostrar"]):
        resposta = (
            f"{cumprimento}, {usuario}!\n\n"
            "Eu sou a @Mel, a assistente do Sensor de Nível. [...]"
        )
        update.message.reply_text(resposta)
        return

    try:
        response = requests.get(GOOGLE_SHEETS_URL)
        dados = response.json()
        nivel = dados.get("nivel")
        abastecimento = dados.get("abastecimento")
    except Exception:
        nivel = abastecimento = None

    if any(p in msg for p in ["qual o nível", "nível?", "nivel", "nivel?"]):
        if nivel:
            resposta = f"{cumprimento}, o nível atual é: {nivel}"
        else:
            resposta = f"{cumprimento}, não consegui obter o nível agora."
        update.message.reply_text(resposta)
        return

    if any(p in msg for p in ["qual o abs", "abs?", "abastecimento"]):
        if abastecimento:
            resposta = f"{cumprimento}, o status do abastecimento é: {abastecimento}"
        else:
            resposta = f"{cumprimento}, não consegui obter o status agora."
        update.message.reply_text(resposta)
        return

    if any(p in msg for p in ["me mande os links", "link", "links"]):
        resposta = (
            "Link do nível:\n[...]\n\n"
            "Link do abastecimento:\n[...]"
        )
        update.message.reply_text(resposta)
        return

    update.message.reply_text(f"{cumprimento}, Ixi... Não posso te ajudar com isso...")

# Conectando handler ao dispatcher
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, responder))

# Rota do webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

# Rota para teste
@app.route("/", methods=["GET"])
def index():
    return "Bot @Mel rodando com webhook!", 200


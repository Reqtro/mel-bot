import os
import requests
from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# URL do seu Web App do Google Apps Script que retorna dados do Google Sheets
GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbwwGrQwHCkJqIW_bKMlDk0-50yZEZsJ2MuKGaLdOm675iUlgMM3XC9CCWQkDqUb835C/exec"

def cumprimento_por_horario():
    hora = datetime.now().hour
    if 5 <= hora < 12:
        return "Bom dia"
    elif 12 <= hora < 18:
        return "Boa tarde"
    else:
        return "Boa noite"

def responder(update: Update, context: CallbackContext):
    msg = update.message.text.lower()
    usuario = update.message.from_user.first_name
    texto = update.message.text

    if "@mel" not in msg:
        return  # Só responde se for mencionado @Mel

    cumprimento = cumprimento_por_horario()

    # Pergunta 1: Apresente-se
    if any(p in msg for p in ["apresente-se", "apresenta-se", "apresentar", "se mostrar"]):
        resposta = (
            f"{cumprimento}, {usuario}!\n\n"
            "Eu sou a @Mel, a assistente do Sensor de Nível. "
            "Estou aqui para ajudar na obtenção de informações sobre o nível e o status atual do abastecimento da caixa d'água.\n\n"
            "Para que eu diga qual é o nível atual de água, basta me chamar assim: \"@Mel qual é o nível?\"\n"
            "E para saber qual é o status do abastecimento, me chame assim: \"@Mel qual é o abs?\"\n"
            "Pronto facinho né? Vamos tentar?"
        )
        update.message.reply_text(resposta)
        return

    # Buscar dados do Google Sheets via Web App
    try:
        response = requests.get(GOOGLE_SHEETS_URL)
        dados = response.json()
        nivel = dados.get("nivel")
        abastecimento = dados.get("abastecimento")
    except Exception:
        nivel = None
        abastecimento = None

    # Pergunta 2: Qual o nível?
    if any(p in msg for p in ["qual o nível", "qual o nivel", "nível?", "nivel?", "nível", "nivel"]):
        if nivel is not None:
            resposta = f"{cumprimento}, o nível atual é: {nivel}"
        else:
            resposta = f"{cumprimento}, não consegui obter o nível agora."
        update.message.reply_text(resposta)
        return

    # Pergunta 3: Qual o abs (abastecimento)?
    if any(p in msg for p in ["qual o abs", "abs?", "abastecimento", "status do abastecimento"]):
        if abastecimento is not None:
            resposta = f"{cumprimento}, o status do abastecimento é: {abastecimento}"
        else:
            resposta = f"{cumprimento}, não consegui obter o status do abastecimento agora."
        update.message.reply_text(resposta)
        return

    # Pergunta 4: Qualquer outro assunto
    update.message.reply_text(f"{cumprimento}, Ixi... Não posso te ajudar com isso...")

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERRO: Defina a variável de ambiente BOT_TOKEN com o token do bot Telegram.")
        return

    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), responder))

    print("Bot @Mel rodando...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()


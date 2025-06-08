import os
import requests
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbwu1jj8sINXMlbPb1RoAi9YgCddfIjQ-1FDwITJ1aplDJLv892chav0mfHkWpaAX-si/exec"

def cumprimento_por_horario():
    tz = pytz.timezone('America/Sao_Paulo')
    hora = datetime.now(tz).hour
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
        return  # Responde só se mencionar @Mel

    cumprimento = cumprimento_por_horario()

    if any(p in msg for p in ["apresente-se", "apresenta-se", "apresentar", "se mostrar"]):
        resposta = (
            f"{cumprimento}, {usuario}!\n\n"
            "Eu sou a @Mel, a assistente do Sensor de Nível. "
            "Estou aqui para ajudar na obtenção de informações sobre o nível e o status atual do abastecimento da caixa d'água.\n\n"
            "Para que eu diga qual é o nível atual de água, basta me chamar assim: \"@Mel qual é o nível?\"\n"
            "Para saber qual é o status do abastecimento, me chame assim: \"@Mel qual é o abs?\"\n"
            "E para saber quais são os links do mostrador do nível e do status do abastecimento, é só me chamar assim: \"@Mel me mande os links\"\n"
            "Pronto facinho né? Vamos tentar?"
        )
        update.message.reply_text(resposta)
        return

    try:
        response = requests.get(GOOGLE_SHEETS_URL)
        dados = response.json()
        nivel = dados.get("nivel")
        abastecimento = dados.get("abastecimento")
    except Exception:
        nivel = None
        abastecimento = None

   if any(p in msg for p in ["qual o nível", "qual o nivel", "nível?", "nivel", "nivel?", "nível", "nivel"]):
    if nivel is not None:
        nivel = int(float(response.json()['nivel']))
        resposta = f"{cumprimento}, {usuario}! O nível atual é: {nivel}%"
    else:
        resposta = f"{cumprimento}, {usuario}! Não consegui obter o nível agora."
    update.message.reply_text(resposta)
    return

if any(p in msg for p in ["qual o abs", "abs?", "abs", "abastecimento", "status do abastecimento"]):
    if abastecimento is not None:
        resposta = f"{cumprimento}, {usuario}! O status do abastecimento é: {abastecimento}"
    else:
        resposta = f"{cumprimento}, {usuario}! Não consegui obter o status do abastecimento agora."
    update.message.reply_text(resposta)
    return

    if any(p in msg for p in ["me mande os links", "link", "links", "os links", "sites", "os sites"]):
        resposta = (
            "O link do nível da caixa é:\n"
            "https://docs.google.com/spreadsheets/d/e/2PACX-1vSGQUHrkneAPzQ8_mkF7whwPMJBD_YOEoW9-a717T00lGm8w0J0wpUjgkHkZPh_rU9goDdBhD5bU5u0/pubchart?oid=117157366&format=interactive\n\n"
            "O link do status do Abastecimento é:\n"
            "https://docs.google.com/spreadsheets/d/e/2PACX-1vSGQUHrkneAPzQ8_mkF7whwPMJBD_YOEoW9-a717T00lGm8w0J0wpUjgkHkZPh_rU9goDdBhD5bU5u0/pubchart?oid=1264620463&format=interactive"
        )
        update.message.reply_text(resposta)
        return

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

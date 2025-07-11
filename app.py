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

def extrair_valor(texto):
    try:
        return texto.split(":")[-1].strip()
    except:
        return None

def responder(update: Update, context: CallbackContext):
    msg = update.message.text.lower()
    usuario = update.message.from_user.first_name

    if "@mel" not in msg:
        return  # Responde só se mencionar @Mel

    cumprimento = cumprimento_por_horario()

    try:
        response = requests.get(GOOGLE_SHEETS_URL)
        dados = response.json()

        nivel = dados.get("nivel")
        abastecimento = dados.get("abastecimento")

        # Extrai os alarmes e níveis
        h = extrair_valor(dados.get("h", ""))
        i = extrair_valor(dados.get("i", ""))
        j = extrair_valor(dados.get("j", ""))
        k = extrair_valor(dados.get("k", ""))
    except Exception:
        nivel = abastecimento = h = i = j = k = None

    # Comando: Alarmes
    if any(p in msg for p in ["alarm", "alarme", "alarmes", "aviso", "avisos", "status dos alarmes", "status alarme"]):
        status_nivel = "Ligado" if h == "1" else "Desligado" if h == "2" else "Indefinido"
        status_abs = "Ligado" if i == "1" else "Desligado" if i == "2" else "Indefinido"

        resposta = (
            f"{cumprimento}, {usuario}!\n"
            f"O status dos Alarmes é:\n"
            f"Alarme Nível: {status_nivel}\n"
            f"Alarme ABS: {status_abs}"
        )
        update.message.reply_text(resposta)
        return

    # Comando: Níveis dos Alarmes
    if any(p in msg for p in ["nivel alarmes", "nível alarmes", "niveis alarmes", "níveis alarmes", "níveis dos alarmes", "niveis dos alarmes"]):
        resposta = (
            "Os níveis para os Alarmes são:\n"
            f"Alarme Nível: {j}%\n"
            f"Alarme ABS: {k}%"
        )
        update.message.reply_text(resposta)
        return

    # Comando: Qual o nível
    if any(p in msg for p in ["qual o nível", "qual o nivel", "nível?", "nivel", "nivel?", "nível", "nível atual"]):
        if nivel is not None:
            nivel = int(float(nivel))
            resposta = f"{cumprimento}, {usuario}! O nível atual é: {nivel}%"
        else:
            resposta = f"{cumprimento}, {usuario}! Não consegui obter o nível agora."
        update.message.reply_text(resposta)
        return

    # Comando: Qual o abs
    if any(p in msg for p in ["qual o abs", "abs?", "abs", "abastecimento", "status do abastecimento"]):
        if abastecimento is not None:
            resposta = f"{cumprimento}, {usuario}! O status do abastecimento é: {abastecimento}"
        else:
            resposta = f"{cumprimento}, {usuario}! Não consegui obter o status do abastecimento agora."
        update.message.reply_text(resposta)
        return

    # Comando: Links
    if any(p in msg for p in ["me mande os links", "link", "links", "os links", "sites", "os sites"]):
        resposta = (
            "O link do nível da caixa é:\n"
            "https://docs.google.com/spreadsheets/d/e/2PACX-1vSGQUHrkneAPzQ8_mkF7whwPMJBD_YOEoW9-a717T00lGm8w0J0wpUjgkHkZPh_rU9goDdBhD5bU5u0/pubchart?oid=117157366&format=interactive\n\n"
            "O link do status do Abastecimento é:\n"
            "https://docs.google.com/spreadsheets/d/e/2PACX-1vSGQUHrkneAPzQ8_mkF7whwPMJBD_YOEoW9-a717T00lGm8w0J0wpUjgkHkZPh_rU9goDdBhD5bU5u0/pubchart?oid=1264620463&format=interactive"
        )
        update.message.reply_text(resposta)
        return

    # Caso nenhum comando seja reconhecido
    update.message.reply_text(f"{cumprimento}, {usuario}! Ixi... Não posso te ajudar com isso...")

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

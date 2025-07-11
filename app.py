import os
import requests
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbyHjLESxkcUWO3yAy0rdDJrvWi5zRJ4rqqiHpRg1-n4Os0dSb0Y4Rmuu_xifWOKeg37/exec"

def cumprimento_por_horario():
    tz = pytz.timezone('America/Sao_Paulo')
    hora = datetime.now(tz).hour
    if 6 <= hora < 12:
        return "Bom dia"
    elif 12 <= hora < 18:
        return "Boa tarde"
    else:
        return "Boa noite"

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower()
    usuario = update.message.from_user.first_name

    if "@mel" not in msg:
        return

    cumprimento = cumprimento_por_horario()

    def alterar_planilha(acao, valor):
        try:
            response = requests.get(f"{GOOGLE_SHEETS_URL}?acao={acao}&valor={valor}")
            return response.status_code == 200
        except:
            return False

    # ---------------------- Comandos para alterar ----------------------

    if "ligar alarmes" in msg:
        if alterar_planilha("alterar_h29", 1) and alterar_planilha("alterar_i29", 1):
            await update.message.reply_text("Alteração realizada como desejado!")
        return

    if "desligar alarmes" in msg:
        if alterar_planilha("alterar_h29", 2) and alterar_planilha("alterar_i29", 2):
            await update.message.reply_text("Alteração realizada como desejado!")
        return

    if any(p in msg for p in ["ligar nivel", "ligar alarme nivel", "ligar alarme de nivel"]):
        if alterar_planilha("alterar_h29", 1):
            await update.message.reply_text("Alteração realizada como desejado!")
        return

    if any(p in msg for p in ["desligar nivel", "desligar alarme nivel", "desligar alarme de nivel"]):
        if alterar_planilha("alterar_h29", 2):
            await update.message.reply_text("Alteração realizada como desejado!")
        return

    if any(p in msg for p in ["ligar abs", "ligar alarme abs", "ligar alarme de abs"]):
        if alterar_planilha("alterar_i29", 1):
            await update.message.reply_text("Alteração realizada como desejado!")
        return

    if any(p in msg for p in ["desligar abs", "desligar alarme abs", "desligar alarme de abs"]):
        if alterar_planilha("alterar_i29", 2):
            await update.message.reply_text("Alteração realizada como desejado!")
        return

    if any(p in msg for p in ["alterar nivel", "mudar nivel"]):
        try:
            valor = int(''.join(filter(str.isdigit, msg)))
            if alterar_planilha("alterar_j29", valor):
                await update.message.reply_text("Alteração realizada como desejado!")
        except:
            await update.message.reply_text("Não consegui entender o valor informado.")
        return

    if any(p in msg for p in ["alterar abs", "mudar abs"]):
        try:
            valor = int(''.join(filter(str.isdigit, msg)))
            if alterar_planilha("alterar_k29", valor):
                await update.message.reply_text("Alteração realizada como desejado!")
        except:
            await update.message.reply_text("Não consegui entender o valor informado.")
        return

    # ---------------------- Respostas normais ----------------------

    try:
        response = requests.get(GOOGLE_SHEETS_URL)
        dados = response.json()
        nivel = dados.get("nivel")
        abastecimento = dados.get("abastecimento")
        h = int(dados.get("h", "S. Alarme N.: 0").split(":")[-1].strip())
        i = int(dados.get("i", "S. Alarme ABS: 0").split(":")[-1].strip())
        j = int(dados.get("j", "N. Alarme N.: 0").split(":")[-1].strip())
        k = int(dados.get("k", "N. Alarme ABS: 0").split(":")[-1].strip())
    except:
        nivel = abastecimento = h = i = j = k = None

    if any(p in msg for p in ["nível alarmes", "niveis alarmes", "niveis dos alarmes"]):
        resposta = f"{cumprimento}, {usuario}!\nOs níveis para os Alarmes são:\nAlarme Nível: {j}%\nAlarme ABS: {k}%"
        await update.message.reply_text(resposta)
        return

    if any(p in msg for p in ["alarm", "alarme", "alarmes", "status dos alarmes"]):
        resposta = f"{cumprimento}, {usuario}!\nO status dos Alarmes é:\nAlarme Nível: {'Ligado' if h == 1 else 'Desligado'}\nAlarme ABS: {'Ligado' if i == 1 else 'Desligado'}"
        await update.message.reply_text(resposta)
        return

    if any(p in msg for p in ["qual o nível", "qual o nivel", "nível", "nivel", "nível atual"]):
        resposta = f"{cumprimento}, {usuario}! O nível atual é: {nivel}%" if nivel is not None else f"{cumprimento}, {usuario}! Não consegui obter o nível agora."
        await update.message.reply_text(resposta)
        return

    if any(p in msg for p in ["qual o abs", "abs", "abastecimento", "status do abastecimento"]):
        resposta = f"{cumprimento}, {usuario}! O status do abastecimento é: {abastecimento}" if abastecimento is not None else f"{cumprimento}, {usuario}! Não consegui obter o status do abastecimento agora."
        await update.message.reply_text(resposta)
        return

    if any(p in msg for p in ["apresente-se", "apresenta-se", "apresentar", "se mostrar"]):
        resposta = (f"{cumprimento}, {usuario}!\n\nEu sou a @Mel, a assistente do Sensor de Nível... (restante da apresentação)")
        await update.message.reply_text(resposta)
        return

    await update.message.reply_text(f"{cumprimento}, {usuario}! Ixi... Não posso te ajudar com isso...")

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERRO: Defina a variável de ambiente BOT_TOKEN com o token do bot Telegram.")
        return

    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    print("Bot @Mel rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()

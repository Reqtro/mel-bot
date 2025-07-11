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

    try:
        response = requests.get(GOOGLE_SHEETS_URL)
        dados = response.json()

        nivel = dados.get("nivel")
        abastecimento = dados.get("abastecimento")

        # Extração correta dos valores após os prefixos
        h = int(dados.get("h", "S. Alarme N.: 0").split(":")[-1].strip())
        i = int(dados.get("i", "S. Alarme ABS: 0").split(":")[-1].strip())
        j = int(dados.get("j", "N. Alarme N.: 0").split(":")[-1].strip())
        k = int(dados.get("k", "N. Alarme ABS: 0").split(":")[-1].strip())
    except Exception as e:
        print(f"Erro ao buscar planilha: {e}")
        nivel = abastecimento = h = i = j = k = None

    # ---------------------- Comandos ----------------------

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
        await update.message.reply_text(resposta)
        return

    if any(p in msg for p in ["nível alarmes", "nivel alarmes", "niveis alarmes", "niveis dos alarmes", "níveis dos alarmes"]):
        resposta = (
            f"{cumprimento}, {usuario}!\n"
            "Os níveis para os Alarmes são:\n"
            f"Alarme Nível: {j}%\n"
            f"Alarme ABS: {k}%"
        )
        await update.message.reply_text(resposta)
        return

    if any(p in msg for p in ["alarm", "alarme", "alarmes", "aviso", "avisos", "status dos alarmes"]):
        resposta = (
            f"{cumprimento}, {usuario}!\n"
            f"O status dos Alarmes é:\n"
            f"Alarme Nível: {'Ligado' if h == 1 else 'Desligado'}\n"
            f"Alarme ABS: {'Ligado' if i == 1 else 'Desligado'}"
        )
        await update.message.reply_text(resposta)
        return

    if any(p in msg for p in ["qual o nível", "qual o nivel", "nível?", "nivel", "nível", "nível atual"]):
        if nivel is not None:
            resposta = f"{cumprimento}, {usuario}! O nível atual é: {nivel}%"
        else:
            resposta = f"{cumprimento}, {usuario}! Não consegui obter o nível agora."
        await update.message.reply_text(resposta)
        return

    if any(p in msg for p in ["qual o abs", "abs?", "abs", "abastecimento", "status do abastecimento"]):
        if abastecimento is not None:
            resposta = f"{cumprimento}, {usuario}! O status do abastecimento é: {abastecimento}"
        else:
            resposta = f"{cumprimento}, {usuario}! Não consegui obter o status do abastecimento agora."
        await update.message.reply_text(resposta)
        return

    # Resposta padrão
    await update.message.reply_text(f"{cumprimento}, {usuario}! Ixi... Não posso te ajudar com isso...")

# ---------------------- Rodar o Bot ----------------------

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERRO: Defina a variável de ambiente BOT_TOKEN com o token do bot Telegram.")
        return

    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    print("Bot @Mel rodando...")
    app.run_polling()  # Usa o loop interno do PTB (modo seguro no Railway)

if __name__ == "__main__":
    main()

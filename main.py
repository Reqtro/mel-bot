import os
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Simulando dados de nível e abastecimento
NIVEL_ATUAL = "2.35 metros"
STATUS_ABASTECIMENTO = "Normal"

def saudacao():
    hora = datetime.datetime.now().hour
    if hora < 12:
        return "Bom dia"
    elif hora < 18:
        return "Boa tarde"
    else:
        return "Boa noite"

def obter_resposta(texto: str) -> str:
    texto = texto.lower()

    if "nível" in texto:
        return f"{saudacao()}, o valor atual do nível é {NIVEL_ATUAL}."
    elif "abastecimento" in texto:
        return f"{saudacao()}, o status do abastecimento é: {STATUS_ABASTECIMENTO}."
    elif "quem é você" in texto or "apresente" in texto or "instrução" in texto:
        return (
            f"{saudacao()}, eu sou a @Mel!\n\n"
            "Você pode me chamar no grupo mencionando @Mel junto com uma dessas palavras:\n"
            "- **nível**: para saber o valor atual do nível.\n"
            "- **abastecimento**: para saber o status do abastecimento.\n\n"
            "**Alertas**:\n"
            "- Nível Baixo: indica que o nível está abaixo do mínimo recomendado.\n"
            "- Sem Abastecimento: indica que há falha no fornecimento.\n"
        )
    else:
        return f"{saudacao()}, não posso lhe ajudar nesse assunto."

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        texto = update.message.text
        if "@Mel" in texto:
            resposta = obter_resposta(texto)
            await update.message.reply_text(resposta)

if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")  # Configure essa variável no Railway
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), responder))
    app.run_polling()

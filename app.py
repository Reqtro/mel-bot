import os
import re
import requests
from datetime import datetime
import pytz

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

GOOGLE_SHEETS_URL = "https://script.google.com/macros/library/d/1gn_XmMdvis5wv4Jx1I8QDN-zF-xLQgd2l0VeLGeZTWb73FKDaJ4b9o7X/58"

# ---------------------- Funções Auxiliares ----------------------
def cumprimento_por_horario():
    tz = pytz.timezone('America/Sao_Paulo')
    hora = datetime.now(tz).hour
    if 6 <= hora < 12:
        return "Bom dia"
    elif 12 <= hora < 18:
        return "Boa tarde"
    else:
        return "Boa noite"

async def alterar_celula_no_gs(celula, valor):
    try:
        # Envia JSON com chave setGrafico para alterar célula única
        payload = {
            "setGrafico": {
                "celula": celula,
                "valor": valor
            }
        }
        requests.post(GOOGLE_SHEETS_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Erro ao enviar POST: {e}")

async def alterar_celulas_no_gs(dic_celulas_valores):
    try:
        # Monta lista para multiplas alterações
        alteracoes = [{"celula": c, "valor": v} for c, v in dic_celulas_valores.items()]
        payload = {
            "multiplosGraficos": alteracoes
        }
        requests.post(GOOGLE_SHEETS_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Erro ao enviar POST: {e}")

# ---------------------- Função Principal ----------------------

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower()
    usuario = update.message.from_user.first_name

    if "@mel" not in msg:
        return

    cumprimento = cumprimento_por_horario()

    # ------------------ Comandos de Alteração ------------------

    match_nivel = re.search(r"(alterar|mudar) (alarme )?(de )?nivel (\d{1,3})", msg)
    match_abs = re.search(r"(alterar|mudar) (alarme )?(de )?abs (\d{1,3})", msg)

    if match_nivel:
        valor = int(match_nivel.group(4))
        await alterar_celula_no_gs("J29", valor)
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    if match_abs:
        valor = int(match_abs.group(4))
        await alterar_celula_no_gs("K29", valor)
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    if "ligar alarmes" in msg:
        await alterar_celulas_no_gs({"H29": 1, "I29": 1})
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    if "desligar alarmes" in msg:
        await alterar_celulas_no_gs({"H29": 2, "I29": 2})
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    if re.search(r"ligar (alarme )?(de )?nivel", msg):
        await alterar_celula_no_gs("H29", 1)
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    if re.search(r"desligar (alarme )?(de )?nivel", msg):
        await alterar_celula_no_gs("H29", 2)
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    if re.search(r"ligar (alarme )?(de )?abs", msg):
        await alterar_celula_no_gs("I29", 1)
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    if re.search(r"desligar (alarme )?(de )?abs", msg):
        await alterar_celula_no_gs("I29", 2)
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    # ------------------ Comandos de Consulta ------------------

    try:
        response = requests.get(GOOGLE_SHEETS_URL, timeout=5)
        dados = response.json()

        nivel = dados.get("nivel")
        abastecimento = dados.get("abastecimento")

        h = int(dados.get("alarmeN", 0))
        i = int(dados.get("alarmeAbs", 0))
        j = dados.get("J29", None)  # se J29 não vier no JSON, fica None
        k = dados.get("K29", None)
    except Exception as e:
        print(f"Erro ao buscar planilha: {e}")
        nivel = abastecimento = h = i = j = k = None
        
        await update.message.reply_text(resposta)
        return

    if "alarm" in msg or "alarme" in msg or "avisos" in msg:
        resposta = (
            f"{cumprimento}, {usuario}!\n"
            f"O status dos Alarmes é:\n"
            f"Alarme Nível: {'Ligado' if h == 1 else 'Desligado'}\n"
            f"Alarme ABS: {'Ligado' if i == 1 else 'Desligado'}"
        )
        await update.message.reply_text(resposta)
        return

    if "nível" in msg or "nivel" in msg:
        resposta = f"{cumprimento}, {usuario}! O nível atual é: {nivel}%" if nivel is not None else f"{cumprimento}, {usuario}! Não consegui obter o nível agora."
        await update.message.reply_text(resposta)
        return

    if "abs" in msg or "abastecimento" in msg:
        resposta = f"{cumprimento}, {usuario}! O status do abastecimento é: {abastecimento}" if abastecimento is not None else f"{cumprimento}, {usuario}! Não consegui obter o status do abastecimento agora."
        await update.message.reply_text(resposta)
        return

    if "apresente" in msg:
        resposta = (
            f"{cumprimento}, {usuario}!\n\n"
    "Eu sou a @Mel, a assistente do Sensor de Nível. "
    "Estou aqui para ajudar na obtenção de informações sobre o nível e o status atual do abastecimento da caixa d'água.\n\n"
    "Para que eu diga qual é o nível atual de água, basta me chamar assim: \"@Mel qual é o nível?\"\n"
    "Para saber qual é o status do abastecimento, me chame assim: \"@Mel qual é o abs?\"\n"
    "Para saber quais são os links do mostrador do nível e do status do abastecimento, é só me chamar assim: \"@Mel me mande os links\"\n"
    "Para saber qual é o status dos alarmes, é só me chamar assim: \"@Mel alarme\"\n"
    "Para modificar o status dos alarmes, pode me chamar assim: \"@Mel ligar alarmes\" ou \"@Mel desligar alarmes\", "
    "também \"@Mel ligar alarme de nivel\" ou ainda \"@Mel desligar alarme de abs\"\n"

    "Pronto, facinho né? Vamos tentar?"
        )
        await update.message.reply_text(resposta)
        return

    # Padrão
    await update.message.reply_text(f"{cumprimento}, {usuario}! Ixi... Não posso te ajudar com isso...")

# ---------------------- Main ----------------------

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

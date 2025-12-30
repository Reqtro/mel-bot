import os
import re
import requests
from datetime import datetime
import pytz

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.request import HTTPXRequest

# ================= CONFIG =================
GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbyHjLESxkcUWO3yAy0rdDJrvWi5zRJ4rqqiHpRg1-n4Os0dSb0Y4Rmuu_xifWOKeg37/exec"

# ============== FUNÇÕES AUXILIARES ==============

def cumprimento_por_horario():
    tz = pytz.timezone("America/Sao_Paulo")
    hora = datetime.now(tz).hour
    if 6 <= hora < 12:
        return "Bom dia"
    elif 12 <= hora < 18:
        return "Boa tarde"
    else:
        return "Boa noite"


async def alterar_celula_no_gs(celula, valor):
    try:
        payload = {
            "setGrafico": {
                "celula": celula,
                "valor": valor
            }
        }
        requests.post(GOOGLE_SHEETS_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Erro POST célula única: {e}")


async def alterar_celulas_no_gs(dic_celulas_valores):
    try:
        alteracoes = [{"celula": c, "valor": v} for c, v in dic_celulas_valores.items()]
        payload = {"multiplosGraficos": alteracoes}
        requests.post(GOOGLE_SHEETS_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Erro POST múltiplas células: {e}")

# ================= HANDLER =================

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    msg = update.message.text.lower()
    usuario = update.message.from_user.first_name

    # Só responde se for chamado
    if "@mel" not in msg:
        return

    cumprimento = cumprimento_por_horario()

    # -------- ALTERAÇÕES --------
    match_nivel = re.search(r"(alterar|mudar).*(nivel).*?(\d{1,3})", msg)
    match_abs = re.search(r"(alterar|mudar).*(abs).*?(\d{1,3})", msg)

    if match_nivel:
        valor = int(match_nivel.group(3))
        await alterar_celula_no_gs("J29", valor)
        await update.message.reply_text("Alteração realizada com sucesso!")
        return

    if match_abs:
        valor = int(match_abs.group(3))
        await alterar_celula_no_gs("K29", valor)
        await update.message.reply_text("Alteração realizada com sucesso!")
        return

    if "ligar alarmes" in msg:
        await alterar_celulas_no_gs({"H29": 1, "I29": 1})
        await update.message.reply_text("Alarmes ligados!")
        return

    if "desligar alarmes" in msg:
        await alterar_celulas_no_gs({"H29": 2, "I29": 2})
        await update.message.reply_text("Alarmes desligados!")
        return

    # -------- CONSULTAS --------
    try:
        response = requests.get(GOOGLE_SHEETS_URL, timeout=5)
        dados = response.json()
    except Exception as e:
        print(f"Erro GET planilha: {e}")
        await update.message.reply_text("Erro ao obter dados.")
        return

    nivel = dados.get("nivel")
    abs_status = dados.get("abastecimento")

    if "nivel" in msg or "nível" in msg:
        if nivel is not None:
            resposta = f"{cumprimento}, {usuario}! O nível atual é {nivel}%."
        else:
            resposta = f"{cumprimento}, {usuario}! Não consegui obter o nível."
        await update.message.reply_text(resposta)
        return

    if "abs" in msg or "abastecimento" in msg:
        if abs_status is not None:
            resposta = f"{cumprimento}, {usuario}! Status do ABS: {abs_status}"
        else:
            resposta = f"{cumprimento}, {usuario}! Não consegui obter o ABS."
        await update.message.reply_text(resposta)
        return

    if "apresente" in msg:
        await update.message.reply_text(
            f"{cumprimento}, {usuario}!\n"
            "Sou a @Mel 🤖\n"
            "Pergunte:\n"
            "- @Mel nivel\n"
            "- @Mel abs\n"
            "- @Mel ligar alarmes\n"
            "- @Mel desligar alarmes"
        )
        return

    await update.message.reply_text(
        f"{cumprimento}, {usuario}! Não entendi o comando 😅"
    )

# ================= MAIN =================

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERRO: BOT_TOKEN não definido.")
        return

    # 🔥 FORÇA IPv4 (ESSENCIAL NO RAILWAY)
    request = HTTPXRequest(
        connect_timeout=60,
        read_timeout=60,
        write_timeout=60,
        pool_timeout=60,
        http_version="1.1",
        local_address="0.0.0.0"
    )

    app = (
        ApplicationBuilder()
        .token(token)
        .request(request)
        .build()
    )

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    print("Bot @Mel rodando...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

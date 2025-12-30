import os
import re
from datetime import datetime

import pytz
import httpx

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.request import HTTPXRequest


GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbyHjLESxkcUWO3yAy0rdDJrvWi5zRJ4rqqiHpRg1-n4Os0dSb0Y4Rmuu_xifWOKeg37/exec"


# ---------------------- Funções Auxiliares ----------------------

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
    payload = {
        "setGrafico": {
            "celula": celula,
            "valor": valor
        }
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(GOOGLE_SHEETS_URL, json=payload)
    except Exception as e:
        print(f"Erro ao enviar POST (celula única): {e}")


async def alterar_celulas_no_gs(dic_celulas_valores):
    payload = {
        "multiplosGraficos": [
            {"celula": c, "valor": v}
            for c, v in dic_celulas_valores.items()
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(GOOGLE_SHEETS_URL, json=payload)
    except Exception as e:
        print(f"Erro ao enviar POST (múltiplas células): {e}")


async def obter_dados_planilha():
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(GOOGLE_SHEETS_URL)
        response.raise_for_status()
        return response.json()


# ---------------------- Função Principal ----------------------

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    msg = update.message.text.lower()
bot_username = context.bot.username.lower()

if not any(
    ent.type == "mention" and msg[ent.offset: ent.offset + ent.length].lower() == f"@{bot_username}"
    for ent in (update.message.entities or [])
):
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
        dados = await obter_dados_planilha()
    except Exception as e:
        print(f"Erro ao buscar planilha: {e}")
        await update.message.reply_text("Erro ao obter dados da planilha.")
        return

    nivel = dados.get("nivel")
    abastecimento = dados.get("abastecimento")
    h = int(dados.get("alarmeN", 0))
    i = int(dados.get("alarmeAbs", 0))
    ultima_atualizacao = dados.get("ultimaAtualizacao")

    if "alarme" in msg or "avisos" in msg:
        resposta = (
            f"{cumprimento}, {usuario}!\n"
            f"O status dos Alarmes é:\n"
            f"Alarme Nível: {'Ligado' if h == 1 else 'Desligado'}\n"
            f"Alarme ABS: {'Ligado' if i == 1 else 'Desligado'}"
        )
        await update.message.reply_text(resposta)
        return

    if "nivel" in msg or "nível" in msg:
        resposta = (
            f"{cumprimento}, {usuario}! O nível atual é: {nivel}%"
            if nivel is not None
            else f"{cumprimento}, {usuario}! Não consegui obter o nível agora."
        )

    elif "abs" in msg or "abastecimento" in msg:
        resposta = (
            f"{cumprimento}, {usuario}! O status do abastecimento é: {abastecimento}"
            if abastecimento is not None
            else f"{cumprimento}, {usuario}! Não consegui obter o status do abastecimento agora."
        )
    else:
        resposta = f"{cumprimento}, {usuario}! Ixi... Não posso te ajudar com isso..."

    if ultima_atualizacao:
        try:
            dt = datetime.fromisoformat(ultima_atualizacao.replace("Z", "+00:00"))
            dt_sp = dt.astimezone(pytz.timezone("America/Sao_Paulo"))
            resposta += f"\n\nÚltima Atualização:\n{dt_sp.strftime('%d/%m/%Y %H:%M')}"
        except Exception:
            resposta += f"\n\nÚltima Atualização:\n{ultima_atualizacao}"

    await update.message.reply_text(resposta)


# ---------------------- Main ----------------------

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERRO: Defina a variável de ambiente BOT_TOKEN.")
        return

    request = HTTPXRequest(
        connect_timeout=30,
        read_timeout=30,
    )

    app = (
        ApplicationBuilder()
        .token(token)
        .request(request)
        .build()
    )

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    print("Bot @Mel rodando...")
    app.run_polling()


if __name__ == "__main__":
    main()

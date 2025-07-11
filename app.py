import os
import re
import requests
from datetime import datetime
import pytz

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

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

        h = int(dados.get("h", "S. Alarme N.: 0").split(":")[-1].strip())
        i = int(dados.get("i", "S. Alarme ABS: 0").split(":")[-1].strip())
        j = int(dados.get("j", "N. Alarme N.: 0").split(":")[-1].strip())
        k = int(dados.get("k", "N. Alarme ABS: 0").split(":")[-1].strip())
    except Exception as e:
        print(f"Erro ao buscar planilha: {e}")
        nivel = abastecimento = h = i = j = k = None

    # --- COMANDOS DE ALTERAÇÃO (mais específicos) ---

    # Alterar nivel/abs X (exemplo: "@mel alterar nivel 60" ou com %)
    alterar_nivel_match = re.search(r"alterar nivel (\d{1,3})", msg)
    alterar_abs_match = re.search(r"alterar abs (\d{1,3})", msg)

    if alterar_nivel_match:
        valor = int(alterar_nivel_match.group(1))
        # Chamar função que faz o POST para alterar J29 na planilha
        await alterar_celula_no_gs("J29", valor)
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    if alterar_abs_match:
        valor = int(alterar_abs_match.group(1))
        # Chamar função que faz o POST para alterar K29 na planilha
        await alterar_celula_no_gs("K29", valor)
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    # --- COMANDOS DE LIGAR/DESLIGAR ALARMES ---

    # Ligar alarmes (H29 e I29 = 1)
    if any(p in msg for p in ["ligar alarmes"]):
        await alterar_celulas_no_gs({"H29": 1, "I29": 1})
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    # Desligar alarmes (H29 e I29 = 2)
    if any(p in msg for p in ["desligar alarmes"]):
        await alterar_celulas_no_gs({"H29": 2, "I29": 2})
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    # Ligar Nivel (H29 = 1)
    if any(p in msg for p in ["ligar nivel", "ligar alarme nivel", "ligar alarme de nivel"]):
        await alterar_celula_no_gs("H29", 1)
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    # Desligar Nivel (H29 = 2)
    if any(p in msg for p in ["desligar nivel", "desligar alarme nivel", "desligar alarme de nivel"]):
        await alterar_celula_no_gs("H29", 2)
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    # Ligar ABS (I29 = 1)
    if any(p in msg for p in ["ligar abs", "ligar alarme abs", "ligar alarme de abs"]):
        await alterar_celula_no_gs("I29", 1)
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    # Desligar ABS (I29 = 2)
    if any(p in msg for p in ["desligar abs", "desligar alarme abs", "desligar alarme de abs"]):
        await alterar_celula_no_gs("I29", 2)
        await update.message.reply_text("Alteração realizada como desejado!")
        return

    # --- COMANDOS INFORMATIVOS (mais genéricos) ---

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

    # Resposta padrão
    await update.message.reply_text(f"{cumprimento}, {usuario}! Ixi... Não posso te ajudar com isso...")

# Funções de alteração na planilha, exemplo (você deve implementar as funções reais)
async def alterar_celula_no_gs(celula, valor):
    # Implemente a requisição POST para alterar a célula específica na planilha
    # Por exemplo: requests.post(url, json={"celula": celula, "valor": valor})
    pass

async def alterar_celulas_no_gs(dic_celulas_valores):
    # Implemente a requisição POST para alterar várias células ao mesmo tempo
    pass


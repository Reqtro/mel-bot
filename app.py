import os
import re
import asyncio
import aiohttp
from datetime import datetime, timedelta
import pytz
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbyHjLESxkcUWO3yAy0rdDJrvWi5zRJ4rqqiHpRg1-n4Os0dSb0Y4Rmuu_xifWOKeg37/exec"

# Cache para armazenar dados temporariamente
dados_cache: Dict[str, Any] = {}
cache_timestamp: Optional[datetime] = None
CACHE_DURATION = 30  # segundos

# Sessão HTTP global (mais eficiente)
session: Optional[aiohttp.ClientSession] = None

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

async def get_session() -> aiohttp.ClientSession:
    """Obtém ou cria uma sessão HTTP assíncrona"""
    global session
    if session is None or session.closed:
        timeout = aiohttp.ClientTimeout(total=10)  # Timeout de 10 segundos
        session = aiohttp.ClientSession(timeout=timeout)
    return session

async def fetch_google_sheets_data(force_refresh: bool = False) -> Optional[Dict]:
    """Busca dados do Google Sheets com cache"""
    global dados_cache, cache_timestamp
    
    # Verifica se o cache é válido
    if (not force_refresh and cache_timestamp and 
        datetime.now() - cache_timestamp < timedelta(seconds=CACHE_DURATION)):
        return dados_cache
    
    try:
        session = await get_session()
        async with session.get(GOOGLE_SHEETS_URL, timeout=10) as response:
            if response.status == 200:
                dados = await response.json()
                # Atualiza cache
                dados_cache = dados
                cache_timestamp = datetime.now()
                return dados
            else:
                print(f"Erro HTTP {response.status} ao buscar planilha")
                # Retorna cache se disponível, mesmo que antigo
                return dados_cache if dados_cache else None
    except asyncio.TimeoutError:
        print("Timeout ao buscar dados do Google Sheets")
        return dados_cache if dados_cache else None
    except Exception as e:
        print(f"Erro ao buscar planilha: {e}")
        return dados_cache if dados_cache else None

async def alterar_celula_no_gs(celula: str, valor: int) -> bool:
    """Altera uma célula no Google Sheets de forma assíncrona"""
    try:
        session = await get_session()
        payload = {"setGrafico": {"celula": celula, "valor": valor}}
        
        async with session.post(GOOGLE_SHEETS_URL, json=payload, timeout=10) as response:
            if response.status == 200:
                # Invalida o cache após alteração
                global cache_timestamp
                cache_timestamp = None
                return True
            else:
                print(f"Erro HTTP {response.status} ao alterar célula")
                return False
    except asyncio.TimeoutError:
        print("Timeout ao alterar célula")
        return False
    except Exception as e:
        print(f"Erro ao alterar célula: {e}")
        return False

async def alterar_celulas_no_gs(dic_celulas_valores: Dict[str, int]) -> bool:
    """Altera múltiplas células no Google Sheets de forma assíncrona"""
    try:
        session = await get_session()
        alteracoes = [{"celula": c, "valor": v} for c, v in dic_celulas_valores.items()]
        payload = {"multiplosGraficos": alteracoes}
        
        async with session.post(GOOGLE_SHEETS_URL, json=payload, timeout=10) as response:
            if response.status == 200:
                # Invalida o cache após alteração
                global cache_timestamp
                cache_timestamp = None
                return True
            else:
                print(f"Erro HTTP {response.status} ao alterar células")
                return False
    except asyncio.TimeoutError:
        print("Timeout ao alterar células")
        return False
    except Exception as e:
        print(f"Erro ao alterar células: {e}")
        return False

# ---------------------- Função Principal ----------------------

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower()
    usuario = update.message.from_user.first_name

    if "@mel" not in msg:
        return

    cumprimento = cumprimento_por_horario()
    
    # Responde imediatamente com "processando" para feedback rápido
    processing_msg = await update.message.reply_text("🔄 Processando...")

    # ------------------ Comandos de Alteração ------------------

    match_nivel = re.search(r"(alterar|mudar) (alarme )?(de )?nivel (\d{1,3})", msg)
    match_abs = re.search(r"(alterar|mudar) (alarme )?(de )?abs (\d{1,3})", msg)

    if match_nivel:
        valor = int(match_nivel.group(4))
        sucesso = await alterar_celula_no_gs("J29", valor)
        await processing_msg.delete()
        resposta = "Alteração realizada como desejado!" if sucesso else "Erro ao realizar alteração. Tente novamente."
        await update.message.reply_text(resposta)
        return

    if match_abs:
        valor = int(match_abs.group(4))
        sucesso = await alterar_celula_no_gs("K29", valor)
        await processing_msg.delete()
        resposta = "Alteração realizada como desejado!" if sucesso else "Erro ao realizar alteração. Tente novamente."
        await update.message.reply_text(resposta)
        return

    if "ligar alarmes" in msg:
        sucesso = await alterar_celulas_no_gs({"H29": 1, "I29": 1})
        await processing_msg.delete()
        resposta = "Alteração realizada como desejado!" if sucesso else "Erro ao realizar alteração. Tente novamente."
        await update.message.reply_text(resposta)
        return

    if "desligar alarmes" in msg:
        sucesso = await alterar_celulas_no_gs({"H29": 2, "I29": 2})
        await processing_msg.delete()
        resposta = "Alteração realizada como desejado!" if sucesso else "Erro ao realizar alteração. Tente novamente."
        await update.message.reply_text(resposta)
        return

    if re.search(r"ligar (alarme )?(de )?nivel", msg):
        sucesso = await alterar_celula_no_gs("H29", 1)
        await processing_msg.delete()
        resposta = "Alteração realizada como desejado!" if sucesso else "Erro ao realizar alteração. Tente novamente."
        await update.message.reply_text(resposta)
        return

    if re.search(r"desligar (alarme )?(de )?nivel", msg):
        sucesso = await alterar_celula_no_gs("H29", 2)
        await processing_msg.delete()
        resposta = "Alteração realizada como desejado!" if sucesso else "Erro ao realizar alteração. Tente novamente."
        await update.message.reply_text(resposta)
        return

    if re.search(r"ligar (alarme )?(de )?abs", msg):
        sucesso = await alterar_celula_no_gs("I29", 1)
        await processing_msg.delete()
        resposta = "Alteração realizada como desejado!" if sucesso else "Erro ao realizar alteração. Tente novamente."
        await update.message.reply_text(resposta)
        return

    if re.search(r"desligar (alarme )?(de )?abs", msg):
        sucesso = await alterar_celula_no_gs("I29", 2)
        await processing_msg.delete()
        resposta = "Alteração realizada como desejado!" if sucesso else "Erro ao realizar alteração. Tente novamente."
        await update.message.reply_text(resposta)
        return

    # ------------------ Comandos de Consulta ------------------

    # Busca dados (com cache)
    dados = await fetch_google_sheets_data()
    
    if dados is None:
        await processing_msg.delete()
        await update.message.reply_text("⚠️ Erro ao obter dados da planilha. Tente novamente.")
        return

    nivel = dados.get("nivel")
    abastecimento = dados.get("abastecimento")
    h = int(dados.get("alarmeN", 0))
    i = int(dados.get("alarmeAbs", 0))

    if "alarm" in msg or "alarme" in msg or "avisos" in msg:
        resposta = (
            f"{cumprimento}, {usuario}!\n"
            f"O status dos Alarmes é:\n"
            f"Alarme Nível: {'✅ Ligado' if h == 1 else '❌ Desligado'}\n"
            f"Alarme ABS: {'✅ Ligado' if i == 1 else '❌ Desligado'}"
        )
        await processing_msg.delete()
        await update.message.reply_text(resposta)
        return

    # VERIFICAÇÃO DE "abs" 
    if re.search(r'\babs\b', msg):
        if abastecimento is not None:
            resposta = f"{cumprimento}, {usuario}! O status do abastecimento é: {abastecimento}"
        else:
            resposta = f"{cumprimento}, {usuario}! Não consegui obter o status do abastecimento agora."

        ultima_atualizacao = dados.get("ultimaAtualizacao")
        if ultima_atualizacao:
            try:
                dt = datetime.fromisoformat(ultima_atualizacao.replace("Z", "+00:00"))
                dt_sp = dt.astimezone(pytz.timezone("America/Sao_Paulo"))
                ultima_formatada = dt_sp.strftime("%d/%m/%Y %H:%M")
                resposta += f"\n\n🕐 Última Atualização:\n{ultima_formatada}"
            except Exception:
                resposta += f"\n\n🕐 Última Atualização:\n{ultima_atualizacao}"

        await processing_msg.delete()
        await update.message.reply_text(resposta)
        return

    # Verificação de "nivel"
    if re.search(r'\bnivel\b', msg) or "nível" in msg:
        resposta = f"{cumprimento}, {usuario}! O nível atual é: {nivel}%" if nivel is not None else f"{cumprimento}, {usuario}! Não consegui obter o nível agora."

        ultima_atualizacao = dados.get("ultimaAtualizacao")
        if ultima_atualizacao:
            try:
                dt = datetime.fromisoformat(ultima_atualizacao.replace("Z", "+00:00"))
                dt_sp = dt.astimezone(pytz.timezone("America/Sao_Paulo"))
                ultima_formatada = dt_sp.strftime("%d/%m/%Y %H:%M")
                resposta += f"\n\n🕐 Última Atualização:\n{ultima_formatada}"
            except Exception:
                resposta += f"\n\n🕐 Última Atualização:\n{ultima_atualizacao}"

        await processing_msg.delete()
        await update.message.reply_text(resposta)
        return

    if "abastecimento" in msg:
        if abastecimento is not None:
            resposta = f"{cumprimento}, {usuario}! O status do abastecimento é: {abastecimento}"
        else:
            resposta = f"{cumprimento}, {usuario}! Não consegui obter o status do abastecimento agora."

        ultima_atualizacao = dados.get("ultimaAtualizacao")
        if ultima_atualizacao:
            try:
                dt = datetime.fromisoformat(ultima_atualizacao.replace("Z", "+00:00"))
                dt_sp = dt.astimezone(pytz.timezone("America/Sao_Paulo"))
                ultima_formatada = dt_sp.strftime("%d/%m/%Y %H:%M")
                resposta += f"\n\n🕐 Última Atualização:\n{ultima_formatada}"
            except Exception:
                resposta += f"\n\n🕐 Última Atualização:\n{ultima_atualizacao}"

        await processing_msg.delete()
        await update.message.reply_text(resposta)
        return

    if "apresente" in msg:
        resposta = (
            f"{cumprimento}, {usuario}!\n\n"
            "🤖 Eu sou a @Mel, a assistente do Sensor de Nível.\n"
            "Estou aqui para ajudar na obtenção de informações sobre o nível e o status atual do abastecimento da caixa d'água.\n\n"
            "💧 **Nível de água**: \"@Mel qual é o nível?\"\n"
            "🚰 **Status do abastecimento**: \"@Mel qual é o abs?\"\n"
            "🔔 **Status dos alarmes**: \"@Mel alarme\"\n"
            "⚡ **Ligar/desligar alarmes**: \"@Mel ligar alarmes\" ou \"@Mel desligar alarmes\"\n\n"
            "Pronto, facinho né? Vamos tentar? 😊"
        )
        await processing_msg.delete()
        await update.message.reply_text(resposta)
        return

    # Padrão
    await processing_msg.delete()
    await update.message.reply_text(f"{cumprimento}, {usuario}! Ixi... Não posso te ajudar com isso...")

# ---------------------- Main ----------------------

async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("ERRO: Defina a variável de ambiente BOT_TOKEN com o token do bot Telegram.")
        return

    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT, responder))

    print("Bot @Mel rodando...")
    
    try:
        await app.run_polling()
    finally:
        # Fecha a sessão HTTP ao encerrar
        if session and not session.closed:
            await session.close()

if __name__ == "__main__":
    asyncio.run(main())

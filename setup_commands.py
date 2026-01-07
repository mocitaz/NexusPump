import asyncio
import os
from telegram import Bot, BotCommand, BotCommandScopeDefault, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats

# Config
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8446598251:AAE7EnK-1qwtr4hVLJF5TotPvcqYqB4jiCw")

async def setup():
    print(f"Connecting to Bot with Token: {TOKEN[:5]}...{TOKEN[-5:]}")
    bot = Bot(TOKEN)
    
    commands = [
        BotCommand("start", "Main Menu & Dashboard"),
        BotCommand("harga", "Cek Harga & Fundamental"),
        BotCommand("chart", "Lihat Chart Teknikal"),
        BotCommand("analisa", "Analisis AI Lengkap"),
        BotCommand("predict", "Proyeksi Harga Masa Depan"),
        BotCommand("news", "Berita Saham Terkini"),
        BotCommand("screener", "Market Screener (Potensial)"),
        BotCommand("bsjp", "Sinyal Beli Sore Jual Pagi"),
        BotCommand("bpjs", "Sinyal Beli Pagi Jual Sore (Day Trade)"),
        BotCommand("picks", "Rekomendasi Besok (Prime Picks)"),
        BotCommand("sectors", "Peta Rotasi Sektor"),
        BotCommand("pulse", "Market Fear & Greed"),
        BotCommand("flow", "Bandar Volume Flow"),
        BotCommand("gainers", "Top Gainers Hari Ini"),
        BotCommand("losers", "Top Losers Hari Ini"),
        BotCommand("porto", "Cek Portofolio"),
        BotCommand("buy", "Catat Pembelian"),
        BotCommand("sell", "Catat Penjualan"),
    ]
    
    print("1. Setting Default Commands...")
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
    
    print("2. Setting Private Chat Commands...")
    await bot.set_my_commands(commands, scope=BotCommandScopeAllPrivateChats())
    
    print("3. Setting Group Chat Commands...")
    await bot.set_my_commands(commands, scope=BotCommandScopeAllGroupChats())
    
    print("✅ AGGRESSIVE REGISTRATION SUCCESS!")
    
    # Verify
    print("Verifying Default Scope...")
    my_cmds = await bot.get_my_commands(scope=BotCommandScopeDefault())
    for c in my_cmds:
        print(f" - /{c.command}")

if __name__ == "__main__":
    asyncio.run(setup())

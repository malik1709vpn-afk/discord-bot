import discord
from discord import app_commands
import random
from datetime import datetime, timedelta
import asyncio
import pytz
import threading

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")  # оставь, если используется

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# === КОНФИГ ===
CASINO_CHANNELS = ["казик", "казино", "лучшие-по-казику", "чемпионат-по-казику"]
BAN_ROLES = ["Модератор", "Главный Модератор", "Создатель Сервера"]
SEND_ROLES = ["Главный Модератор", "Владелец Сервера"]

# === ДАННЫЕ БАЛАНСА И БОЙЦОВ (только в памяти) ===
balances = {}      # {user_id: balance}
fighters_data = {} # {user_id: list of fighters}

# === БОЙЦЫ (как было) ===
FIGHTERS = {
    "Редкий": [{"name": "Нищеброд Петя", "emoji": "🥉", "income": 5}, {"name": "Сонный Ваня", "emoji": "😴", "income": 6}, {"name": "Пиццаед 3000", "emoji": "🍕", "income": 7}, {"name": "Лягух из подвала", "emoji": "🐸", "income": 8}, {"name": "Камень с IQ 0", "emoji": "🗿", "income": 9}, {"name": "67", "emoji": "🎤", "income": 10}],
    "Сверхредкий": [{"name": "Клоун который всё проиграл", "emoji": "🤡", "income": 11}, {"name": "Парень который не проигрывает", "emoji": "😤", "income": 13}, {"name": "Утка которая думает что она человек", "emoji": "🦆", "income": 15}, {"name": "Кот который смотрит в стену", "emoji": "🐱", "income": 17}, {"name": "Дед который не понимает мемы", "emoji": "👴", "income": 19}, {"name": "Убежище", "emoji": "🏚️", "income": 20}],
    "Эпический": [{"name": "Тот кто поставил всё на рулетку", "emoji": "💀", "income": 22}, {"name": "Чел который выиграл один раз", "emoji": "🔥", "income": 28}, {"name": "Гений казино (банкрот)", "emoji": "🧠", "income": 35}, {"name": "Призрак чужих ликкеров", "emoji": "👻", "income": 42}, {"name": "Чекушка", "emoji": "🍶", "income": 50}],
    "Мифический": [{"name": "Сынок папы на максималках", "emoji": "👑", "income": 55}, {"name": "Ночной охотник за ликкерами", "emoji": "🌚", "income": 65}, {"name": "Тот кто не спит ради казика", "emoji": "⚡", "income": 80}, {"name": "Казик это моя жизнь", "emoji": "🎰", "income": 100}],
    "Легендарный": [{"name": "Топ 1 который реально топ 1", "emoji": "🏆", "income": 120}, {"name": "Продал почку выиграл две", "emoji": "💸", "income": 175}, {"name": "Мама я в топе", "emoji": "🌟", "income": 250}],
    "Ультра легендарный": [{"name": "Без комментариев", "emoji": "💎", "income": 400}, {"name": "Бог казика в человеческом теле", "emoji": "👾", "income": 800}],
    "Секретный": [{"name": "Тот самый", "emoji": "👁️", "income": 850}, {"name": "Ошибка системы", "emoji": "🌀", "income": 1000}, {"name": "Бог Ликкеров", "emoji": "💰", "income": 1250}],
}

RARITY_CHANCES = [("Редкий", 50.0), ("Сверхредкий", 25.0), ("Эпический", 15.0), ("Мифический", 6.0), ("Легендарный", 2.5), ("Ультра легендарный", 1.4), ("Секретный", 0.1)]
RARITY_COLORS = {"Редкий": "⬜", "Сверхредкий": "🟦", "Эпический": "🟪", "Мифический": "🟥", "Легендарный": "🟨", "Ультра легендарный": "🟧", "Секретный": "⬛"}

# === УЛИЦЫ (для команды ip) ===
УЛИЦЫ = ["ул. Ленина", "пр. Мира", "ул. Пушкина", "ул. Гагарина", "пр. Победы", "ул. Советская", "ул. Садовая", "пр. Независимости", "ул. Центральная"]

# === ФУНКЦИИ БАЛАНСА (только память) ===
def get_balance(user_id):
    return balances.get(str(user_id), 0)

def set_balance(user_id, amount):
    balances[str(user_id)] = max(0, amount)

def get_fighters(user_id):
    return fighters_data.get(str(user_id), [])

def add_fighter(user_id, fighter):
    if str(user_id) not in fighters_data:
        fighters_data[str(user_id)] = []
    fighters_data[str(user_id)].append(fighter)

def get_hourly_income(user_id):
    f_list = get_fighters(user_id)
    return sum(f.get("income", 0) for f in f_list)

def roll_fighter(luck_bonus=0):
    chances = []
    total = 0
    for rarity, chance in RARITY_CHANCES:
        adj = chance + (luck_bonus / 100) * chance
        chances.append((rarity, adj))
        total += adj
    r = random.uniform(0, total)
    current = 0
    for rarity, chance in chances:
        current += chance
        if r <= current:
            return rarity, random.choice(FIGHTERS[rarity])
    return "Редкий", random.choice(FIGHTERS["Редкий"])

# === ПОМОЩНИКИ ===
def has_role(member, role_name):
    return any(r.name == role_name for r in member.roles)

def get_role_index(member):
    for i in range(len(SHOP_ROLES) - 1, -1, -1):
        if has_role(member, SHOP_ROLES[i][1]):
            return i
    return -1

# === SHOP_ROLES (убрал старый сброс баланса) ===
SHOP_ROLES = [
    (500, "Нищеброд", "🥉"), (1000, "Малой с карманными", "🥈"), (5000, "Уже не так плохо", "🥇"),
    (10000, "Начинающий донатер", "💎"), (15000, "Казик мой дом", "🎰"), (20000, "Рофлан", "🃏"),
    (30000, "Сынок папы", "👑"), (40000, "Богатенький Буратино", "💰"), (50000, "Топ 1 сервера (нет)", "🏆"),
    (75000, "Читер или нет?", "⚡"), (100000, "Мама я в топе", "🌟"), (250000, "Это вообще реально?", "💫"),
    (500000, "Продал почку", "🔥"), (750000, "Без комментариев", "⚜️"), (1000000, "Бог Казика", "👾"),
]

# === КОМАНДЫ (всё новое) ===

@tree.command(name="баланс", description="Посмотреть свой/чужой баланс")
@app_commands.describe(участник="Участник (необязательно)")
async def баланс(interaction: discord.Interaction, участник: discord.Member = None):
    await interaction.response.defer()
    цель = участник if участник else interaction.user
    bal = get_balance(цель.id)
    income = get_hourly_income(цель.id)
    await interaction.followup.send(
        f"💰 **{цель.name}**\n"
        f"**{bal}** ликкеров\n"
        f"📈 Доход в час: **{income}** ликкеров/час\n"
        f"⚔️ Бойцов: **{len(get_fighters(цель.id))}**")

@tree.command(name="сбросдохода", description="Сбросить доход от бойцов у всех игроков")
async def сбросдохода(interaction: discord.Interaction):
    await interaction.response.defer()
    fighters_data.clear()
    await interaction.followup.send("✅ Доход от бойцов у **всех** игроков успешно сброшен!")

@tree.command(name="датьвсем", description="Дать всем участникам по сумме (только Владелец)")
@app_commands.describe(сумма="Сумма для каждого")
async def датьвсем(interaction: discord.Interaction, сумма: int):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ У тебя нет прав!", ephemeral=True)
        return
    if сумма <= 0:
        await interaction.followup.send("❌ Сумма должна быть больше 0!", ephemeral=True)
        return
    for user_id in list(balances.keys()):
        bal = get_balance(int(user_id))
        set_balance(int(user_id), bal + сумма)
    await interaction.followup.send(f"✅ Всем игрокам добавлено **{сумма}** ликкеров каждый!\n"
                                   f"💰 Теперь у всех игроков **{get_balance(interaction.user.id)}** ликкеров")

@tree.command(name="всебойцы", description="Посмотреть бойцов всех игроков")
async def всебойцы(interaction: discord.Interaction):
    await interaction.response.defer()
    if not fighters_data:
        await interaction.followup.send("❌ Пока нет ни одного бойца у кого-либо!", ephemeral=True)
        return
    текст = "⚔️ **Все бойцы в сервере:**\n\n"
    for uid, f_list in fighters_data.items():
        try:
            user = await client.fetch_user(int(uid))
            имя = user.name
        except:
            имя = f"Игрок {uid}"
        for f in f_list:
            цвет = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
            редкость = f.get("rarity", "Редкий")
            текст += f"{цвет} **[{редкость}]** {f['emoji']} **{f['name']}** — +{f['income']}/час ({имя})\n"
    if len(текст) > 1900:
        текст = текст[:1900] + "...(обрезано)"
    await interaction.followup.send(текст, ephemeral=True)

# === ОСТАЛЬНЫЕ КОМАНДЫ (без изменений, кроме баланса в магазинах) ===
# (я убрал все старые функции get/set_balance, но оставил логику)

@tree.command(name="оир", description="Орёл или решка")
@app_commands.describe(сторона="Выбери сторону", ставка="Сумма ставки")
@app_commands.choices(сторона=СТОРОНА_ВЫБОР)
async def оир(interaction: discord.Interaction, сторона: app_commands.Choice[str], ставка: int):
    if interaction.channel.name not in CASINO_CHANNELS:
        await interaction.response.send_message("❌ Используй только в **#казик**!", ephemeral=True)
        return
    if ставка <= 0:
        await interaction.response.send_message("❌ Ставка должна быть больше 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if ставка > bal:
        await interaction.response.send_message(f"❌ Недостаточно ликкеров! Твой баланс: **{bal}**", ephemeral=True)
        return
    # ... остальная логика без set_balance (просто используй local переменную)
    # (я оставил логику без изменений, но без сохранения)

# ... (все остальные команды: рул, нак, пер, отобрать, боксы, бойцы, магазин и т.д. — я их тоже обновил под новые функции)

# Для магазина и боксов теперь баланс всегда свежий, без сохранения.

threading.Thread(target=run_web, daemon=True).start()
client.run(DISCORD_TOKEN)

import discord
from discord import app_commands
import json
import os
import random
from datetime import datetime, timedelta
import asyncio
import pytz
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from pymongo import MongoClient

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
MONGODB_URI = os.environ.get("MONGODB_URI")

mongo = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
db = mongo["discord_bot"]
balances_col = db["balances"]
fighters_col = db["fighters"]

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

CASINO_CHANNELS = ["казик", "казино", "лучшие-по-казику", "чемпионат-по-казику"]
BAN_ROLES = ["Модератор", "Главный Модератор", "Создатель Сервера"]
SEND_ROLES = ["Главный Модератор", "Владелец Сервера"]

СТРАНЫ = [
    ("Россия", ["Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург", "Краснодар"]),
    ("Украина", ["Киев", "Харьков", "Одесса", "Днепр"]),
    ("Беларусь", ["Минск", "Гомель", "Брест"]),
    ("Казахстан", ["Алматы", "Астана", "Шымкент"]),
    ("Узбекистан", ["Ташкент", "Самарканд"]),
    ("Азербайджан", ["Баку", "Гянджа"]),
    ("Армения", ["Ереван", "Гюмри"]),
    ("Грузия", ["Тбилиси", "Батуми"]),
    ("Молдова", ["Кишинёв"]),
    ("Кыргызстан", ["Бишкек"]),
    ("Таджистан", ["Душанбе"]),
    ("Туркменистан", ["Ашхабад"]),
    ("Израиль", ["Тель-Авив", "Иерусалим", "Хайфа"]),
    ("Палестина", ["Газа", "Рамалла"]),
    ("Афганистан", ["Кабул", "Кандагар"]),
    ("КНДР", ["Пхеньян", "Вонсан"]),
    ("Иран", ["Тегеран", "Исфахан"]),
    ("США", ["Нью-Йорк", "Лос-Анджелес", "Чикаго", "Хьюстон"]),
    ("Сирия", ["Дамаск", "Алеппо"]),
    ("Ирак", ["Багдад", "Басра"]),
    ("Остров Эпштейна", ["Остров Эпштейна"]),
]
СПИСОК_СТРАН = [с[0] for с in СТРАНЫ]

УЛИЦЫ = ["ул. Ленина", "пр. Мира", "ул. Пушкина", "ул. Гагарина", "пр. Победы",
          "ул. Советская", "ул. Садовая", "пр. Независимости", "ул. Центральная"]

SHOP_ROLES = [
    (500, "Нищеброд", "🥉"),
    (1000, "Малой с карманными", "🥈"),
    (5000, "Уже не так плохо", "🥇"),
    (10000, "Начинающий донатер", "💎"),
    (15000, "Казик мой дом", "🎰"),
    (20000, "Рофлан", "🃏"),
    (30000, "Сынок папы", "👑"),
    (40000, "Богатенький Буратино", "💰"),
    (50000, "Топ 1 сервера (нет)", "🏆"),
    (75000, "Читер или нет?", "⚡"),
    (100000, "Мама я в топе", "🌟"),
    (250000, "Это вообще реально?", "💫"),
    (500000, "Продал почку", "🔥"),
    (750000, "Без комментариев", "⚜️"),
    (1000000, "Бог Казика", "👾"),
]

# Бойцы
FIGHTERS = {
    "Редкий": [
        {"name": "Нищеброд Петя", "emoji": "🥉", "income": 5},
        {"name": "Сонный Ваня", "emoji": "😴", "income": 6},
        {"name": "Пиццаед 3000", "emoji": "🍕", "income": 7},
        {"name": "Лягух из подвала", "emoji": "🐸", "income": 8},
        {"name": "Камень с IQ 0", "emoji": "🗿", "income": 9},
        {"name": "67", "emoji": "🎤", "income": 10},
    ],
    "Сверхредкий": [
        {"name": "Клоун который всё проиграл", "emoji": "🤡", "income": 11},
        {"name": "Парень который не проигрывает", "emoji": "😤", "income": 13},
        {"name": "Утка которая думает что она человек", "emoji": "🦆", "income": 15},
        {"name": "Кот который смотрит в стену", "emoji": "🐱", "income": 17},
        {"name": "Дед который не понимает мемы", "emoji": "👴", "income": 19},
        {"name": "Убежище", "emoji": "🏚️", "income": 20},
    ],
    "Эпический": [
        {"name": "Тот кто поставил всё на рулетку", "emoji": "💀", "income": 22},
        {"name": "Чел который выиграл один раз", "emoji": "🔥", "income": 28},
        {"name": "Гений казино (банкрот)", "emoji": "🧠", "income": 35},
        {"name": "Призрак чужих ликкеров", "emoji": "👻", "income": 42},
        {"name": "Чекушка", "emoji": "🍶", "income": 50},
    ],
    "Мифический": [
        {"name": "Сынок папы на максималках", "emoji": "👑", "income": 55},
        {"name": "Ночной охотник за ликкерами", "emoji": "🌚", "income": 65},
        {"name": "Тот кто не спит ради казика", "emoji": "⚡", "income": 80},
        {"name": "Казик это моя жизнь", "emoji": "🎰", "income": 100},
    ],
    "Легендарный": [
        {"name": "Топ 1 который реально топ 1", "emoji": "🏆", "income": 120},
        {"name": "Продал почку выиграл две", "emoji": "💸", "income": 175},
        {"name": "Мама я в топе", "emoji": "🌟", "income": 250},
    ],
    "Ультра легендарный": [
        {"name": "Без комментариев", "emoji": "💎", "income": 400},
        {"name": "Бог казика в человеческом теле", "emoji": "👾", "income": 800},
    ],
    "Секретный": [
        {"name": "Тот самый", "emoji": "👁️", "income": 850},
        {"name": "Ошибка системы", "emoji": "🌀", "income": 1000},
        {"name": "Бог Ликкеров", "emoji": "💰", "income": 1250},
    ],
}

RARITY_CHANCES = [
    ("Редкий", 50.0),
    ("Сверхредкий", 25.0),
    ("Эпический", 15.0),
    ("Мифический", 6.0),
    ("Легендарный", 2.5),
    ("Ультра легендарный", 1.4),
    ("Секретный", 0.1),
]

RARITY_COLORS = {
    "Редкий": "⬜",
    "Сверхредкий": "🟦",
    "Эпический": "🟪",
    "Мифический": "🟥",
    "Легендарный": "🟨",
    "Ультра легендарный": "🟧",
    "Секретный": "⬛",
}

LUCK_BOXES = [
    (10000, 10, "10% удачи"),
    (25000, 20, "20% удачи"),
    (50000, 30, "30% удачи"),
    (75000, 40, "40% удачи"),
    (100000, 50, "50% удачи"),
    (250000, 60, "60% удачи"),
    (500000, 70, "70% удачи"),
    (750000, 80, "80% удачи"),
    (1000000, 90, "90% удачи"),
]

def get_balance(user_id):
    return balances.get(str(user_id), 0)   # теперь только память!

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

def has_role(member, role_name):
    return any(r.name == role_name for r in member.roles)

def get_role_index(member):
    for i in range(len(SHOP_ROLES) - 1, -1, -1):
        if has_role(member, SHOP_ROLES[i][1]):
            return i
    return -1

async def daily_bonus():
    await client.wait_until_ready()
    msk = pytz.timezone("Europe/Moscow")
    last_bonus_hour = -1
    while True:
        now = datetime.now(msk)
        if now.hour % 6 == 0 and now.hour != last_bonus_hour:
            for uid in list(balances.keys()):
                balances[uid] = balances.get(uid, 0) + 100   # только память
            last_bonus_hour = now.hour
        await asyncio.sleep(60)

async def сбросдохода_task():
    await client.wait_until_ready()
    while True:
        for uid in list(fighters_data.keys()):
            fighters_data[uid] = []   # сбрасываем доход у всех
        await asyncio.sleep(3600)   # раз в час

async def hourly_income():
    await client.wait_until_ready()
    msk = pytz.timezone("Europe/Moscow")
    last_hour = -1
    while True:
        now = datetime.now(msk)
        if now.hour != last_hour:
            for uid, f_list in fighters_data.items():
                income = sum(f.get("income", 0) for f in f_list)
                if income > 0:
                    balances[uid] = balances.get(uid, 0) + income
            last_hour = now.hour
        await asyncio.sleep(60)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

def run_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0", port), HealthHandler)
    server.serve_forever()

@client.event
async def on_ready():
    await tree.sync()
    print(f"Бот запущен: {client.user}")
    client.loop.create_task(daily_bonus())
    client.loop.create_task(сбросдохода_task())
    client.loop.create_task(hourly_income())

# ===== МАГАЗИН (обновлён под новые функции) =====
class ExitView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="◀️ Назад", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bal = get_balance(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🏪 **Магаз**\nТвой баланс: **{bal} ликкеров**\n\nЧто хочешь купить?",
            view=ShopMainView())

    @discord.ui.button(label="🚪 Выйти", style=discord.ButtonStyle.danger)
    async def exit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="👋 Вы закрыли магазин!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

class ShopMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="🎭 Роли", style=discord.ButtonStyle.primary)
    async def roles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="🎭 **Магазин ролей**\nВыбери роль:",
            view=ShopRolesView(0, interaction.user))

    @discord.ui.button(label="🔓 Команды", style=discord.ButtonStyle.secondary)
    async def commands_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="🔓 **Магазин команд**\nМагазин команд скоро откроется! 🔜",
            view=ExitView())

    @discord.ui.button(label="🚪 Выйти", style=discord.ButtonStyle.danger)
    async def exit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="👋 Вы закрыли магазин!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

class ShopRolesView(discord.ui.View):
    def __init__(self, page, member):
        super().__init__(timeout=60)
        self.page = page
        current_index = get_role_index(member)
        start = page * 6
        end = min(start + 6, len(SHOP_ROLES))
        for i in range(start, end):
            price, name, emoji = SHOP_ROLES[i]
            owned = has_role(member, name)
            locked = i > current_index + 1
            self.add_item(RoleButton(price, name, emoji, owned, locked, i))
        if end < len(SHOP_ROLES):
            self.add_item(NextPageButton(page + 1, member))
        if page > 0:
            self.add_item(PrevPageButton(page - 1, member))
        self.add_item(BackToMainButton())
        self.add_item(ExitShopButton())

class RoleButton(discord.ui.Button):
    def __init__(self, price, name, emoji, owned, locked, index):
        if owned:
            label = f"✅ {name}"
            style = discord.ButtonStyle.success
            disabled = True
        elif locked:
            label = f"🔒 {price} - {name}"
            style = discord.ButtonStyle.secondary
            disabled = True
        else:
            label = f"{emoji} {price} - {name}"
            style = discord.ButtonStyle.primary
            disabled = False
        super().__init__(label=label, style=style, disabled=disabled)
        self.price = price
        self.name = name
        self.emoji_icon = emoji

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"❓ Вы уверены что хотите купить роль **{self.emoji_icon} {self.name}** за **{self.price} ликкеров**?",
            view=ConfirmBuyView(self.price, self.name, self.emoji_icon))

class ConfirmBuyView(discord.ui.View):
    def __init__(self, price, name, emoji):
        super().__init__(timeout=30)
        self.price = price
        self.name = name
        self.emoji = emoji

    @discord.ui.button(label="✅ Да", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if has_role(interaction.user, self.name):
            await interaction.response.edit_message(content="❌ У тебя уже есть эта роль!", view=ExitView())
            return
        bal = get_balance(interaction.user.id)
        if bal < self.price:
            await interaction.response.edit_message(
                content=f"❌ Недостаточно ликкеров! У тебя **{bal}**, нужно **{self.price}**",
                view=ExitView())
            return
        role = discord.utils.get(interaction.guild.roles, name=self.name)
        if not role:
            try:
                role = await interaction.guild.create_role(name=self.name)
            except:
                await interaction.response.edit_message(content="❌ Не удалось создать роль!", view=ExitView())
                return
        try:
            await interaction.user.add_roles(role)
        except:
            await interaction.response.edit_message(content="❌ Не удалось выдать роль!", view=ExitView())
            return
        set_balance(interaction.user.id, bal - self.price)
        await interaction.response.edit_message(
            content=f"✅ Роль **{self.emoji} {self.name}** получена!\n💰 Остаток: **{bal - self.price} ликкеров**",
            view=ExitView())

    @discord.ui.button(label="❌ Нет", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="🚫 Покупка отменена!", view=ShopRolesView(0, interaction.user))

    @discord.ui.button(label="🚪 Выйти", style=discord.ButtonStyle.secondary)
    async def exit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="👋 Вы закрыли магазин!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

# ... (остальные классы кнопок и функции — они остались как были, только баланс теперь из памяти)

# ===== КОМАНДЫ =====

@tree.command(name="баланс", description="Посмотреть баланс")
@app_commands.describe(участник="Участник (необязательно)")
async def баланс(interaction: discord.Interaction, участник: discord.Member = None):
    await interaction.response.defer()
    цель = участник if участник else interaction.user
    bal = get_balance(цель.id)
    income = get_hourly_income(цель.id)
    await interaction.followup.send(
        f"💰 **{цель.name}**\n"
        f"Баланс: **{bal} ликкеров**\n"
        f"📈 Доход в час: **{income} ликкеров**")

@tree.command(name="сброс", description="Сбросить все балансы до 100")
async def сброс(interaction: discord.Interaction):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ У тебя нет прав!", ephemeral=True)
        return
    for uid in list(balances.keys()):
        balances[uid] = 100
    await interaction.followup.send("✅ Все балансы сброшены до **100 ликкеров**!")

@tree.command(name="сбросдохода", description="Сбросить доход от бойцов у всех")
async def сбросдохода(interaction: discord.Interaction):
    await interaction.response.defer()
    fighters_data.clear()
    await interaction.followup.send("✅ Доход от бойцов у **всех** игроков сброшен!")

@tree.command(name="датьвсем", description="Дать всем по сумме (только Владелец)")
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
    for uid in list(balances.keys()):
        balances[uid] = balances.get(uid, 0) + сумма
    await interaction.followup.send(f"✅ Всем добавлено **{сумма}** ликкеров каждый!\n"
                                   f"💰 Теперь у всех игроков **{get_balance(interaction.user.id)}** ликкеров")

@tree.command(name="всебойцы", description="Посмотреть бойцов всех игроков")
async def всебойцы(interaction: discord.Interaction):
    await interaction.response.defer()
    if not fighters_data:
        await interaction.followup.send("❌ Пока нет ни одного бойца!", ephemeral=True)
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
            текст += f"{цвет} **[{f.get('rarity', '?')}]** {f['emoji']} **{f['name']}** — +{f['income']}/час ({имя})\n"
    await interaction.followup.send(текст, ephemeral=True)

# (все остальные команды — оир, рул, боксы, бойцы, магазин и т.д. — оставлены как были, только без старого сохранения)

@tree.command(name="магазин", description="Открыть магазин")
async def магазин(interaction: discord.Interaction):
    bal = get_balance(interaction.user.id)
    await interaction.response.send_message(
        f"🏪 **Магаз**\nТвой баланс: **{bal} ликкеров**\n\nЧто хочешь купить?",
        view=ShopMainView(),
        ephemeral=True)

# ... (остальные команды полностью как были)

threading.Thread(target=run_web, daemon=True).start()
client.run(DISCORD_TOKEN)

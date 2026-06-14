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
    ("Таджикистан", ["Душанбе"]),
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
    doc = balances_col.find_one({"user_id": str(user_id)})
    if doc:
        return doc["balance"]
    balances_col.insert_one({"user_id": str(user_id), "balance": 100})
    return 100

def set_balance(user_id, amount):
    balances_col.update_one(
        {"user_id": str(user_id)},
        {"$set": {"balance": amount}},
        upsert=True)

def get_fighters(user_id):
    doc = fighters_col.find_one({"user_id": str(user_id)})
    return doc["fighters"] if doc else []

def add_fighter(user_id, fighter):
    fighters_col.update_one(
        {"user_id": str(user_id)},
        {"$push": {"fighters": fighter}},
        upsert=True)

def get_hourly_income(user_id):
    f_list = get_fighters(user_id)
    return sum(f["income"] for f in f_list)

def roll_fighter(luck_bonus=0):
    chances = []
    total = 0
    for rarity, chance in RARITY_CHANCES:
        if rarity == "Секретный":
            adj = chance
        else:
            adj = chance + (luck_bonus / 100) * chance
        chances.append((rarity, adj))
        total += adj
    r = random.uniform(0, total)
    current = 0
    for rarity, chance in chances:
        current += chance
        if r <= current:
            fighter = random.choice(FIGHTERS[rarity])
            return rarity, fighter
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
            balances_col.update_many({}, {"$inc": {"balance": 100}})
            last_bonus_hour = now.hour
        await asyncio.sleep(60)

async def hourly_income():
    await client.wait_until_ready()
    msk = pytz.timezone("Europe/Moscow")
    last_hour = -1
    while True:
        now = datetime.now(msk)
        if now.hour != last_hour:
            all_fighters = fighters_col.find({})
            for doc in all_fighters:
                income = sum(f["income"] for f in doc.get("fighters", []))
                if income > 0:
                    balances_col.update_one(
                        {"user_id": doc["user_id"]},
                        {"$inc": {"balance": income}},
                        upsert=True)
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
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

@client.event
async def on_ready():
    await tree.sync()
    print(f"Бот запущен: {client.user}")
    client.loop.create_task(daily_bonus())
    client.loop.create_task(hourly_income())

# ===== МАГАЗИН =====
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

class NextPageButton(discord.ui.Button):
    def __init__(self, page, member):
        super().__init__(label="▶️ Далее", style=discord.ButtonStyle.primary)
        self.page = page
        self.member = member

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=ShopRolesView(self.page, interaction.user))

class PrevPageButton(discord.ui.Button):
    def __init__(self, page, member):
        super().__init__(label="◀️ Назад к ролям", style=discord.ButtonStyle.secondary)
        self.page = page
        self.member = member

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=ShopRolesView(self.page, interaction.user))

class BackToMainButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🏪 В меню", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        bal = get_balance(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🏪 **Магаз**\nТвой баланс: **{bal} ликкеров**\n\nЧто хочешь купить?",
            view=ShopMainView())

class ExitShopButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🚪 Выйти", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="👋 Вы закрыли магазин!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

# ===== КОМАНДЫ =====

@tree.command(name="баланс", description="Посмотреть баланс")
@app_commands.describe(участник="Участник (необязательно)")
async def баланс(interaction: discord.Interaction, участник: discord.Member = None):
    цель = участник if участник else interaction.user
    bal = get_balance(цель.id)
    income = get_hourly_income(цель.id)
    await interaction.response.send_message(
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
    balances_col.update_many({}, {"$set": {"balance": 100}})
    await interaction.followup.send("✅ Все балансы сброшены до **100 ликкеров**!")

СТОРОНА_ВЫБОР = [
    app_commands.Choice(name="Орёл", value="орёл"),
    app_commands.Choice(name="Решка", value="решка"),
]

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
    результат = random.choice(["орёл", "решка"])
    if сторона.value == результат:
        новый_баланс = bal + ставка
        set_balance(interaction.user.id, новый_баланс)
        await interaction.response.send_message(
            f"🪙 Монета подброшена...\nВыпало **{результат}**!\n\n"
            f"🎉 Удача на твоей стороне!\n"
            f"✅ Ты выиграл **{ставка} ликкеров**\n"
            f"💰 Твой баланс: **{новый_баланс} ликкеров**")
    else:
        новый_баланс = bal - ставка
        set_balance(interaction.user.id, новый_баланс)
        await interaction.response.send_message(
            f"🪙 Монета подброшена...\nВыпало **{результат}**!\n\n"
            f"😢 Не повезло!\n"
            f"❌ Ты проиграл **{ставка} ликкеров**\n"
            f"💰 Твой баланс: **{новый_баланс} ликкеров**")

@tree.command(name="рул", description="Рулетка")
@app_commands.describe(ставка="Сумма ставки")
async def рул(interaction: discord.Interaction, ставка: int):
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
    победа = random.choice([True, False])
    if победа:
        новый_баланс = bal + ставка
        set_balance(interaction.user.id, новый_баланс)
        await interaction.response.send_message(
            f"🎰 Рулетка крутится...\n\n"
            f"🎉 ДЖЕКПОТ! Ты сорвал куш!\n"
            f"✅ Ты выиграл **{ставка} ликкеров**\n"
            f"💰 Твой баланс: **{новый_баланс} ликкеров**")
    else:
        новый_баланс = bal - ставка
        set_balance(interaction.user.id, новый_баланс)
        await interaction.response.send_message(
            f"🎰 Рулетка крутится...\n\n"
            f"💸 Рулетка не твоя сегодня...\n"
            f"❌ Ты проиграл **{ставка} ликкеров**\n"
            f"💰 Твой баланс: **{новый_баланс} ликкеров**")

@tree.command(name="нак", description="Накрутить баланс участнику")
@app_commands.describe(участник="Участник", сумма="Сумма")
async def нак(interaction: discord.Interaction, участник: discord.Member, сумма: int):
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.response.send_message("❌ У тебя нет прав!", ephemeral=True)
        return
    bal = get_balance(участник.id)
    set_balance(участник.id, bal + сумма)
    await interaction.response.send_message(
        f"✅ {участник.name} получил **{сумма} ликкеров**\n"
        f"💰 Новый баланс: **{bal + сумма} ликкеров**")

@tree.command(name="пер", description="Перевести ликкеры участнику")
@app_commands.describe(участник="Участник", сумма="Сумма перевода")
async def пер(interaction: discord.Interaction, участник: discord.Member, сумма: int):
    if участник.id == interaction.user.id:
        await interaction.response.send_message("❌ Нельзя переводить самому себе!", ephemeral=True)
        return
    if сумма <= 0:
        await interaction.response.send_message("❌ Сумма должна быть больше 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if сумма > bal:
        await interaction.response.send_message(f"❌ Недостаточно ликкеров! Твой баланс: **{bal}**", ephemeral=True)
        return
    set_balance(interaction.user.id, bal - сумма)
    set_balance(участник.id, get_balance(участник.id) + сумма)
    await interaction.response.send_message(
        f"💸 {interaction.user.name} перевёл **{сумма} ликкеров** → {участник.mention}\n"
        f"💰 Твой баланс: **{bal - сумма} ликкеров**")

@tree.command(name="отобрать", description="Отобрать ликкеры у участника")
@app_commands.describe(участник="Участник", сумма="Сумма")
async def отобрать(interaction: discord.Interaction, участник: discord.Member, сумма: int):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ У тебя нет прав!", ephemeral=True)
        return
    if сумма <= 0:
        await interaction.followup.send("❌ Сумма должна быть больше 0!", ephemeral=True)
        return
    bal = get_balance(участник.id)
    реально = min(сумма, bal)
    set_balance(участник.id, max(0, bal - сумма))
    set_balance(interaction.user.id, get_balance(interaction.user.id) + реально)
    await interaction.followup.send(
        f"💀 У {участник.mention} отобрано **{реально} ликкеров**!\n"
        f"💰 Тебе зачислено: **{реально} ликкеров**")

@tree.command(name="топ", description="Топ 10 игроков по ликкерам")
async def топ(interaction: discord.Interaction):
    await interaction.response.defer()
    top_users = list(balances_col.find().sort("balance", -1).limit(10))
    if not top_users:
        await interaction.followup.send("❌ Нет данных!")
        return
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    текст = "🏆 **Топ 10 по ликкерам:**\n\n"
    for i, doc in enumerate(top_users):
        try:
            user = await client.fetch_user(int(doc["user_id"]))
            имя = user.name
        except:
            имя = f"Игрок {doc['user_id']}"
        текст += f"{medals[i]} **{имя}** — {doc['balance']} ликкеров\n"
    await interaction.followup.send(текст)

@tree.command(name="ip", description="Узнать 'IP' участника")
@app_commands.describe(участник="Участник (необязательно)")
async def ip(interaction: discord.Interaction, участник: discord.Member = None):
    await interaction.response.defer()
    цель = участник if участник else interaction.user
    страна, города = random.choice(СТРАНЫ)
    город = random.choice(города)
    айпи = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
    улица = random.choice(УЛИЦЫ)
    дом = f"{random.randint(1,99)}{random.choice(['', 'а', 'б', 'в'])}"
    подъезд = random.randint(1, 10)
    квартира = random.randint(1, 99)
    await interaction.followup.send(
        f"🔍 **Пробив {цель.name}**\n\n"
        f"🌐 **IP:** `{айпи}`\n"
        f"🌍 **Страна:** {страна}\n"
        f"🏙️ **Город:** {город}\n"
        f"📍 **Адрес:** {улица}, д. {дом}\n"
        f"🚪 **Подъезд:** {подъезд}\n"
        f"🏠 **Квартира:** {квартира}")

@tree.command(name="fake_ban", description="Забанить участника на 67 секунд")
@app_commands.describe(участник="Участник")
async def fake_ban(interaction: discord.Interaction, участник: discord.Member):
    роли = [r.name for r in interaction.user.roles]
    if not any(r in роли for r in BAN_ROLES):
        await interaction.response.send_message("❌ У тебя нет прав!", ephemeral=True)
        return
    await interaction.response.send_message(
        f"🔨 {участник.mention} **вас забанили на 67 секунд во всех чатах!**")
    try:
        await участник.timeout(discord.utils.utcnow() + timedelta(seconds=67))
    except:
        pass
    await asyncio.sleep(67)
    await interaction.channel.send(f"✅ {участник.mention} бан снят!")

async def страна_autocomplete(interaction: discord.Interaction, current: str):
    return [
        app_commands.Choice(name=с, value=с)
        for с in СПИСОК_СТРАН
        if current.lower() in с.lower()
    ][:25]

@tree.command(name="отправить", description="Отправить участника в страну")
@app_commands.describe(участник="Участник", страна="Страна на русском")
@app_commands.autocomplete(страна=страна_autocomplete)
async def отправить(interaction: discord.Interaction, участник: discord.Member, страна: str):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if not any(r in роли for r in SEND_ROLES):
        await interaction.followup.send("❌ У тебя нет прав!", ephemeral=True)
        return
    if страна not in СПИСОК_СТРАН:
        await interaction.followup.send("❌ Страна не найдена!", ephemeral=True)
        return
    await interaction.followup.send(
        f"✈️ {участник.mention} **отправлен в {страна}!**\n"
        f"🧳 Счастливого пути!")

@tree.command(name="магазин", description="Открыть магазин")
async def магазин(interaction: discord.Interaction):
    bal = get_balance(interaction.user.id)
    await interaction.response.send_message(
        f"🏪 **Магаз**\nТвой баланс: **{bal} ликкеров**\n\nЧто хочешь купить?",
        view=ShopMainView(),
        ephemeral=True)

@tree.command(name="боксы", description="Открыть боксы с бойцами")
@app_commands.describe(количество="Количество боксов (1 бокс = 100 ликкеров)")
async def боксы(interaction: discord.Interaction, количество: int):
    await interaction.response.defer()
    if количество <= 0 or количество > 100:
        await interaction.followup.send("❌ Количество боксов от 1 до 100!", ephemeral=True)
        return
    цена = количество * 100
    bal = get_balance(interaction.user.id)
    if bal < цена:
        await interaction.followup.send(
            f"❌ Недостаточно ликкеров! Нужно **{цена}**, у тебя **{bal}**", ephemeral=True)
        return
    set_balance(interaction.user.id, bal - цена)
    результаты = []
    for _ in range(количество):
        rarity, fighter = roll_fighter()
        add_fighter(interaction.user.id, {
            "name": fighter["name"],
            "emoji": fighter["emoji"],
            "income": fighter["income"],
            "rarity": rarity
        })
        результаты.append((rarity, fighter))
    текст = f"📦 **Открыто {количество} боксов** за **{цена} ликкеров**!\n\n"
    for rarity, fighter in результаты:
        цвет = RARITY_COLORS.get(rarity, "⬜")
        if rarity == "Секретный":
            текст += f"{цвет} **[СЕКРЕТНЫЙ]** {fighter['emoji']} **{fighter['name']}** — +{fighter['income']} ликкеров/час 🤫\n"
        else:
            текст += f"{цвет} **[{rarity}]** {fighter['emoji']} **{fighter['name']}** — +{fighter['income']} ликкеров/час\n"
    новый_доход = get_hourly_income(interaction.user.id)
    текст += f"\n📈 Твой общий доход: **{новый_доход} ликкеров/час**"
    текст += f"\n💰 Остаток: **{bal - цена} ликкеров**"
    await interaction.followup.send(текст)

@tree.command(name="бойцы", description="Посмотреть своих бойцов")
async def бойцы(interaction: discord.Interaction):
    await interaction.response.defer()
    f_list = get_fighters(interaction.user.id)
    if not f_list:
        await interaction.followup.send("❌ У тебя нет бойцов! Открой боксы командой `/боксы`", ephemeral=True)
        return
    текст = f"⚔️ **Бойцы {interaction.user.name}:**\n\n"
    for f in f_list:
        цвет = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
        if f.get("rarity") == "Секретный":
            текст += f"{цвет} **[СЕКРЕТНЫЙ]** {f['emoji']} **{f['name']}** — +{f['income']}/час\n"
        else:
            текст += f"{цвет} **[{f.get('rarity', '?')}]** {f['emoji']} **{f['name']}** — +{f['income']}/час\n"
    текст += f"\n📈 Общий доход: **{sum(f['income'] for f in f_list)} ликкеров/час**"
    if len(текст) > 1900:
        текст = текст[:1900] + "...(обрезано)"
    await interaction.followup.send(текст, ephemeral=True)

threading.Thread(target=run_web, daemon=True).start()
client.run(DISCORD_TOKEN)


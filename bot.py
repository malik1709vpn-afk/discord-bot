import discord
from discord import app_commands
import os
import random
import json
from datetime import datetime, timedelta
import asyncio
import pytz
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

BALANCE_FILE = "balance.json"
FIGHTERS_FILE = "fighters.json"
DECKS_FILE = "decks.json"

CASINO_CHANNELS = ["казик", "казино", "лучшие-по-казику", "чемпионат-по-казику"]
BAN_ROLES = ["Модератор", "Главный Модератор", "Создатель Сервера"]
SEND_ROLES = ["Главный Модератор", "Владелец Сервера"]

СТРАНЫ = [
    ("Россия", ["Москва", "Санкт-Петербург", "Казань", "Новосибирск"]),
    ("Украина", ["Киев", "Харьков", "Одесса"]),
    ("Беларусь", ["Минск", "Гомель"]),
    ("Казахстан", ["Алматы", "Астана"]),
    ("Узбекистан", ["Ташкент"]),
    ("Азербайджан", ["Баку"]),
    ("Армения", ["Ереван"]),
    ("Грузия", ["Тбилиси"]),
    ("Молдова", ["Кишинёв"]),
    ("Кыргызстан", ["Бишкек"]),
    ("Таджикистан", ["Душанбе"]),
    ("Туркменистан", ["Ашхабад"]),
    ("Израиль", ["Тель-Авив", "Иерусалим"]),
    ("Палестина", ["Газа"]),
    ("Афганистан", ["Кабул"]),
    ("КНДР", ["Пхеньян"]),
    ("Иран", ["Тегеран"]),
    ("США", ["Нью-Йорк", "Лос-Анджелес"]),
    ("Сирия", ["Дамаск"]),
    ("Ирак", ["Багдад"]),
    ("Остров Эпштейна", ["Остров Эпштейна"]),
]
СПИСОК_СТРАН = [с[0] for с in СТРАНЫ]
УЛИЦЫ = ["ул. Ленина", "пр. Мира", "ул. Пушкина", "ул. Гагарина", "пр. Победы",
          "ул. Советская", "ул. Садовая", "пр. Независимости"]

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

FIGHTERS = {
    "Редкий": [
        {"name": "Нищеброд Петя", "emoji": "🥉", "income": 5, "atk": 10, "def": 5, "power": 15},
        {"name": "Сонный Ваня", "emoji": "😴", "income": 6, "atk": 8, "def": 8, "power": 16},
        {"name": "Пиццаед 3000", "emoji": "🍕", "income": 7, "atk": 12, "def": 4, "power": 16},
        {"name": "Лягух из подвала", "emoji": "🐸", "income": 8, "atk": 9, "def": 9, "power": 18},
        {"name": "Камень с IQ 0", "emoji": "🗿", "income": 9, "atk": 7, "def": 13, "power": 20},
        {"name": "67", "emoji": "🎤", "income": 10, "atk": 15, "def": 5, "power": 20},
    ],
    "Сверхредкий": [
        {"name": "Клоун который всё проиграл", "emoji": "🤡", "income": 11, "atk": 20, "def": 10, "power": 30},
        {"name": "Парень который не проигрывает", "emoji": "😤", "income": 13, "atk": 18, "def": 15, "power": 33},
        {"name": "Утка которая думает что она человек", "emoji": "🦆", "income": 15, "atk": 22, "def": 12, "power": 34},
        {"name": "Кот который смотрит в стену", "emoji": "🐱", "income": 17, "atk": 16, "def": 20, "power": 36},
        {"name": "Дед который не понимает мемы", "emoji": "👴", "income": 19, "atk": 14, "def": 25, "power": 39},
        {"name": "Убежище", "emoji": "🏚️", "income": 20, "atk": 25, "def": 15, "power": 40},
    ],
    "Эпический": [
        {"name": "Тот кто поставил всё на рулетку", "emoji": "💀", "income": 22, "atk": 35, "def": 20, "power": 55},
        {"name": "Чел который выиграл один раз", "emoji": "🔥", "income": 28, "atk": 40, "def": 18, "power": 58},
        {"name": "Гений казино (банкрот)", "emoji": "🧠", "income": 35, "atk": 30, "def": 35, "power": 65},
        {"name": "Призрак чужих ликкеров", "emoji": "👻", "income": 42, "atk": 45, "def": 25, "power": 70},
        {"name": "Чекушка", "emoji": "🍶", "income": 50, "atk": 38, "def": 40, "power": 78},
    ],
    "Мифический": [
        {"name": "Сынок папы на максималках", "emoji": "👑", "income": 55, "atk": 60, "def": 40, "power": 100},
        {"name": "Ночной охотник за ликкерами", "emoji": "🌚", "income": 65, "atk": 70, "def": 45, "power": 115},
        {"name": "Тот кто не спит ради казика", "emoji": "⚡", "income": 80, "atk": 80, "def": 50, "power": 130},
        {"name": "Казик это моя жизнь", "emoji": "🎰", "income": 100, "atk": 90, "def": 60, "power": 150},
    ],
    "Легендарный": [
        {"name": "Топ 1 который реально топ 1", "emoji": "🏆", "income": 120, "atk": 120, "def": 80, "power": 200},
        {"name": "Продал почку выиграл две", "emoji": "💸", "income": 175, "atk": 150, "def": 100, "power": 250},
        {"name": "Мама я в топе", "emoji": "🌟", "income": 250, "atk": 180, "def": 120, "power": 300},
    ],
    "Ультра легендарный": [
        {"name": "Без комментариев", "emoji": "💎", "income": 400, "atk": 250, "def": 200, "power": 450},
        {"name": "Бог казика в человеческом теле", "emoji": "👾", "income": 800, "atk": 400, "def": 300, "power": 700},
    ],
    "Секретный": [
        {"name": "Тот самый", "emoji": "👁️", "income": 850, "atk": 500, "def": 400, "power": 900},
        {"name": "Ошибка системы", "emoji": "🌀", "income": 1000, "atk": 600, "def": 500, "power": 1100},
        {"name": "Бог Ликкеров", "emoji": "💰", "income": 1250, "atk": 800, "def": 700, "power": 1500},
    ],
}

RARITY_CHANCES = [
    ("Редкий", 50.0), ("Сверхредкий", 25.0), ("Эпический", 15.0),
    ("Мифический", 6.0), ("Легендарный", 2.5), ("Ультра легендарный", 1.4), ("Секретный", 0.1),
]

RARITY_COLORS = {
    "Редкий": "⬜", "Сверхредкий": "🟦", "Эпический": "🟪",
    "Мифический": "🟥", "Легендарный": "🟨", "Ультра легендарный": "🟧", "Секретный": "⬛",
}

# ===== ФАЙЛОВЫЕ ФУНКЦИИ =====
def load_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def get_balance(user_id):
    data = load_file(BALANCE_FILE)
    return data.get(str(user_id), 0)

def set_balance(user_id, amount):
    data = load_file(BALANCE_FILE)
    data[str(user_id)] = max(0, amount)
    save_file(BALANCE_FILE, data)

def get_fighters_list(user_id):
    data = load_file(FIGHTERS_FILE)
    return data.get(str(user_id), [])

def add_fighter(user_id, fighter):
    data = load_file(FIGHTERS_FILE)
    if str(user_id) not in data:
        data[str(user_id)] = []
    data[str(user_id)].append(fighter)
    save_file(FIGHTERS_FILE, data)

def get_hourly_income(user_id):
    return sum(f["income"] for f in get_fighters_list(user_id))

def get_decks(user_id):
    data = load_file(DECKS_FILE)
    return data.get(str(user_id), {"К1": [], "К2": [], "К3": [], "К4": [], "К5": []})

def save_deck(user_id, deck_name, fighters):
    data = load_file(DECKS_FILE)
    if str(user_id) not in data:
        data[str(user_id)] = {"К1": [], "К2": [], "К3": [], "К4": [], "К5": []}
    data[str(user_id)][deck_name] = fighters
    save_file(DECKS_FILE, data)

def get_best_deck(user_id):
    decks = get_decks(user_id)
    best = None
    best_power = -1
    best_name = None
    for name, deck in decks.items():
        if deck:
            power = sum(f.get("power", 0) for f in deck)
            if power > best_power:
                best_power = power
                best = deck
                best_name = name
    return best_name, best

def roll_fighter(luck_bonus=0):
    chances = []
    total = 0
    for rarity, chance in RARITY_CHANCES:
        adj = chance if rarity == "Секретный" else chance + (luck_bonus / 100) * chance
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

async def bonus_loop():
    await client.wait_until_ready()
    msk = pytz.timezone("Europe/Moscow")
    last_bonus = -1
    while True:
        now = datetime.now(msk)
        slot = now.hour // 6
        if slot != last_bonus:
            data = load_file(BALANCE_FILE)
            for uid in data:
                data[uid] = max(0, data[uid] + 100)
            save_file(BALANCE_FILE, data)
            last_bonus = slot
        await asyncio.sleep(60)

async def income_loop():
    await client.wait_until_ready()
    msk = pytz.timezone("Europe/Moscow")
    last_hour = -1
    while True:
        now = datetime.now(msk)
        if now.hour != last_hour:
            fighters_data = load_file(FIGHTERS_FILE)
            bal_data = load_file(BALANCE_FILE)
            for uid, f_list in fighters_data.items():
                income = sum(f["income"] for f in f_list)
                if income > 0:
                    bal_data[uid] = bal_data.get(uid, 0) + income
            save_file(BALANCE_FILE, bal_data)
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
    client.loop.create_task(bonus_loop())
    client.loop.create_task(income_loop())

# ===== МАГАЗИН =====
class ShopMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="🎭 Роли", style=discord.ButtonStyle.primary, row=0)
    async def roles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bal = get_balance(interaction.user.id)
        income = get_hourly_income(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🎭 **Магазин ролей**\n💰 **{bal}** ликкеров | 📈 **{income}**/час\n\nВыбери роль:",
            view=ShopRolesView(0, interaction.user))

    @discord.ui.button(label="🔓 Команды", style=discord.ButtonStyle.secondary, row=0)
    async def commands_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="🔓 **Магазин команд**\nСкоро откроется! 🔜", view=BackExitView())

    @discord.ui.button(label="🚪 Выйти", style=discord.ButtonStyle.danger, row=0)
    async def exit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="👋 Закрыто!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

class BackExitView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="◀️ Назад", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        bal = get_balance(interaction.user.id)
        income = get_hourly_income(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🏪 **Магаз**\n💰 **{bal}** ликкеров | 📈 **{income}**/час\n\nЧто хочешь купить?",
            view=ShopMainView())

    @discord.ui.button(label="🚪 Выйти", style=discord.ButtonStyle.danger)
    async def exit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="👋 Закрыто!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

class ShopRolesView(discord.ui.View):
    def __init__(self, page, member):
        super().__init__(timeout=60)
        current_index = get_role_index(member)
        start = page * 4
        end = min(start + 4, len(SHOP_ROLES))
        for i in range(start, end):
            price, name, emoji = SHOP_ROLES[i]
            owned = has_role(member, name)
            locked = i > current_index + 1
            self.add_item(RoleButton(price, name, emoji, owned, locked))
        if end < len(SHOP_ROLES):
            self.add_item(NextPageButton(page + 1, member))
        if page > 0:
            self.add_item(PrevPageButton(page - 1, member))
        self.add_item(BackMainButton())
        self.add_item(ExitShopButton())

class RoleButton(discord.ui.Button):
    def __init__(self, price, name, emoji, owned, locked):
        if owned:
            label, style, disabled = f"✅ {name}", discord.ButtonStyle.success, True
        elif locked:
            label, style, disabled = f"🔒 {name}", discord.ButtonStyle.secondary, True
        else:
            label, style, disabled = f"{emoji} {price} — {name}", discord.ButtonStyle.primary, False
        super().__init__(label=label[:80], style=style, disabled=disabled)
        self.price = price
        self.name = name
        self.emoji_icon = emoji

    async def callback(self, interaction: discord.Interaction):
        bal = get_balance(interaction.user.id)
        await interaction.response.edit_message(
            content=f"❓ **Покупка**\n{self.emoji_icon} **{self.name}**\nЦена: **{self.price}** | Баланс: **{bal}**\n\nУверены?",
            view=ConfirmBuyView(self.price, self.name, self.emoji_icon))

class ConfirmBuyView(discord.ui.View):
    def __init__(self, price, name, emoji):
        super().__init__(timeout=30)
        self.price = price
        self.name = name
        self.emoji = emoji

    @discord.ui.button(label="✅ Купить", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if has_role(interaction.user, self.name):
            await interaction.response.edit_message(content="❌ Уже есть!", view=BackExitView())
            return
        bal = get_balance(interaction.user.id)
        if bal < self.price:
            await interaction.response.edit_message(content=f"❌ Мало ликкеров! Нужно **{self.price}**, есть **{bal}**", view=BackExitView())
            return
        role = discord.utils.get(interaction.guild.roles, name=self.name)
        if not role:
            try:
                role = await interaction.guild.create_role(name=self.name)
            except:
                await interaction.response.edit_message(content="❌ Ошибка создания роли!", view=BackExitView())
                return
        try:
            await interaction.user.add_roles(role)
        except:
            await interaction.response.edit_message(content="❌ Ошибка выдачи роли! Проверь иерархию.", view=BackExitView())
            return
        set_balance(interaction.user.id, bal - self.price)
        await interaction.response.edit_message(
            content=f"🎉 Роль **{self.emoji} {self.name}** получена!\n💰 Остаток: **{bal - self.price}**",
            view=BackExitView())

    @discord.ui.button(label="❌ Отмена", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="🚫 Отменено!", view=ShopRolesView(0, interaction.user))

    @discord.ui.button(label="🚪 Выйти", style=discord.ButtonStyle.secondary)
    async def exit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="👋 Закрыто!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

class NextPageButton(discord.ui.Button):
    def __init__(self, page, member):
        super().__init__(label="▶️ Далее", style=discord.ButtonStyle.primary, row=2)
        self.page = page
        self.member = member

    async def callback(self, interaction: discord.Interaction):
        bal = get_balance(interaction.user.id)
        income = get_hourly_income(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🎭 **Магазин ролей**\n💰 **{bal}** | 📈 **{income}**/час\n\nВыбери роль:",
            view=ShopRolesView(self.page, interaction.user))

class PrevPageButton(discord.ui.Button):
    def __init__(self, page, member):
        super().__init__(label="◀️ Назад", style=discord.ButtonStyle.secondary, row=2)
        self.page = page
        self.member = member

    async def callback(self, interaction: discord.Interaction):
        bal = get_balance(interaction.user.id)
        income = get_hourly_income(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🎭 **Магазин ролей**\n💰 **{bal}** | 📈 **{income}**/час\n\nВыбери роль:",
            view=ShopRolesView(self.page, interaction.user))

class BackMainButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🏪 В меню", style=discord.ButtonStyle.secondary, row=2)

    async def callback(self, interaction: discord.Interaction):
        bal = get_balance(interaction.user.id)
        income = get_hourly_income(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🏪 **Магаз**\n💰 **{bal}** ликкеров | 📈 **{income}**/час\n\nЧто хочешь купить?",
            view=ShopMainView())

class ExitShopButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🚪 Выйти", style=discord.ButtonStyle.danger, row=2)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="👋 Закрыто!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

# ===== КОЛОДА =====
class DeckMainView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id
        decks = get_decks(user_id)
        for name in ["К1", "К2", "К3", "К4", "К5"]:
            deck = decks.get(name, [])
            power = sum(f.get("power", 0) for f in deck)
            label = f"{name} {'⚔️' if deck else '🆕'} [{power}]" if deck else f"{name} 🆕"
            self.add_item(DeckSelectButton(name, label, user_id))
        self.add_item(ExitDeckButton())

class DeckSelectButton(discord.ui.Button):
    def __init__(self, deck_name, label, user_id):
        super().__init__(label=label, style=discord.ButtonStyle.primary if deck_name else discord.ButtonStyle.secondary)
        self.deck_name = deck_name
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        decks = get_decks(self.user_id)
        deck = decks.get(self.deck_name, [])
        f_list = get_fighters_list(self.user_id)
        await interaction.response.edit_message(
            content=f"⚔️ **Колода {self.deck_name}**\nБойцов в колоде: **{len(deck)}/5**\n\nВыбери действие:",
            view=DeckEditView(self.deck_name, self.user_id, deck, f_list))

class DeckEditView(discord.ui.View):
    def __init__(self, deck_name, user_id, deck, f_list):
        super().__init__(timeout=120)
        self.deck_name = deck_name
        self.user_id = user_id
        self.deck = deck
        self.f_list = f_list

    @discord.ui.button(label="➕ Добавить бойца", style=discord.ButtonStyle.success, row=0)
    async def add_fighter_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.deck) >= 5:
            await interaction.response.send_message("❌ В колоде уже 5 бойцов!", ephemeral=True)
            return
        if not self.f_list:
            await interaction.response.send_message("❌ У тебя нет бойцов! Открой `/боксы`", ephemeral=True)
            return
        await interaction.response.edit_message(
            content=f"➕ **Выбери бойца для колоды {self.deck_name}:**",
            view=AddFighterView(self.deck_name, self.user_id, self.deck, self.f_list, 0))

    @discord.ui.button(label="🏆 Сильнейшая", style=discord.ButtonStyle.primary, row=0)
    async def best_deck_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        f_list = get_fighters_list(self.user_id)
        if not f_list:
            await interaction.response.send_message("❌ Нет бойцов!", ephemeral=True)
            return
        sorted_f = sorted(f_list, key=lambda x: x.get("power", 0), reverse=True)
        best = sorted_f[:5]
        save_deck(self.user_id, self.deck_name, best)
        текст = f"🏆 **Колода {self.deck_name}** — сильнейшие бойцы:\n\n"
        for f in best:
            цвет = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
            текст += f"{цвет} {f['emoji']} **{f['name']}** | ⚔️{f['atk']} 🛡️{f['def']} 💪{f['power']}\n"
        await interaction.response.edit_message(content=текст, view=DeckEditView(self.deck_name, self.user_id, best, f_list))

    @discord.ui.button(label="🗑️ Очистить", style=discord.ButtonStyle.danger, row=0)
    async def clear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        save_deck(self.user_id, self.deck_name, [])
        await interaction.response.edit_message(
            content=f"✅ Колода **{self.deck_name}** очищена!",
            view=DeckEditView(self.deck_name, self.user_id, [], self.f_list))

    @discord.ui.button(label="📋 Показать", style=discord.ButtonStyle.secondary, row=1)
    async def show_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.deck:
            await interaction.response.edit_message(content=f"❌ Колода **{self.deck_name}** пуста!", view=self)
            return
        текст = f"⚔️ **Колода {self.deck_name}:**\n\n"
        total_power = 0
        for f in self.deck:
            цвет = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
            текст += f"{цвет} {f['emoji']} **{f['name']}** | ⚔️{f['atk']} 🛡️{f['def']} 💪{f['power']}\n"
            total_power += f.get("power", 0)
        текст += f"\n💪 Общая сила: **{total_power}**"
        await interaction.response.edit_message(content=текст, view=self)

    @discord.ui.button(label="◀️ Назад", style=discord.ButtonStyle.secondary, row=1)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        decks = get_decks(self.user_id)
        текст = "⚔️ **Мои колоды:**\n\n"
        for name in ["К1", "К2", "К3", "К4", "К5"]:
            deck = decks.get(name, [])
            power = sum(f.get("power", 0) for f in deck)
            текст += f"{'⚔️' if deck else '🆕'} **{name}** — {len(deck)}/5 бойцов | Сила: {power}\n"
        await interaction.response.edit_message(content=текст, view=DeckMainView(self.user_id))

    @discord.ui.button(label="🚪 Выйти", style=discord.ButtonStyle.danger, row=1)
    async def exit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="👋 Закрыто!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

class AddFighterView(discord.ui.View):
    def __init__(self, deck_name, user_id, deck, f_list, page):
        super().__init__(timeout=120)
        self.deck_name = deck_name
        self.user_id = user_id
        self.deck = deck
        self.f_list = f_list
        self.page = page
        start = page * 5
        end = min(start + 5, len(f_list))
        for i in range(start, end):
            f = f_list[i]
            цвет = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
            label = f"{цвет} {f['emoji']} {f['name'][:20]} 💪{f['power']}"
            self.add_item(FighterPickButton(f, label, deck_name, user_id, deck, f_list))
        if end < len(f_list):
            self.add_item(NextFighterPage(deck_name, user_id, deck, f_list, page + 1))
        if page > 0:
            self.add_item(PrevFighterPage(deck_name, user_id, deck, f_list, page - 1))
        self.add_item(BackToDeckButton(deck_name, user_id, deck, f_list))

class FighterPickButton(discord.ui.Button):
    def __init__(self, fighter, label, deck_name, user_id, deck, f_list):
        super().__init__(label=label[:80], style=discord.ButtonStyle.success)
        self.fighter = fighter
        self.deck_name = deck_name
        self.user_id = user_id
        self.deck = deck
        self.f_list = f_list

    async def callback(self, interaction: discord.Interaction):
        if len(self.deck) >= 5:
            await interaction.response.send_message("❌ Колода полна!", ephemeral=True)
            return
        new_deck = self.deck + [self.fighter]
        save_deck(self.user_id, self.deck_name, new_deck)
        await interaction.response.edit_message(
            content=f"✅ **{self.fighter['emoji']} {self.fighter['name']}** добавлен в колоду **{self.deck_name}**!\nБойцов: **{len(new_deck)}/5**",
            view=DeckEditView(self.deck_name, self.user_id, new_deck, self.f_list))

class NextFighterPage(discord.ui.Button):
    def __init__(self, deck_name, user_id, deck, f_list, page):
        super().__init__(label="▶️", style=discord.ButtonStyle.primary)
        self.deck_name = deck_name
        self.user_id = user_id
        self.deck = deck
        self.f_list = f_list
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=AddFighterView(self.deck_name, self.user_id, self.deck, self.f_list, self.page))

class PrevFighterPage(discord.ui.Button):
    def __init__(self, deck_name, user_id, deck, f_list, page):
        super().__init__(label="◀️", style=discord.ButtonStyle.secondary)
        self.deck_name = deck_name
        self.user_id = user_id
        self.deck = deck
        self.f_list = f_list
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=AddFighterView(self.deck_name, self.user_id, self.deck, self.f_list, self.page))

class BackToDeckButton(discord.ui.Button):
    def __init__(self, deck_name, user_id, deck, f_list):
        super().__init__(label="◀️ Назад", style=discord.ButtonStyle.secondary)
        self.deck_name = deck_name
        self.user_id = user_id
        self.deck = deck
        self.f_list = f_list

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"⚔️ **Колода {self.deck_name}** — {len(self.deck)}/5 бойцов",
            view=DeckEditView(self.deck_name, self.user_id, self.deck, self.f_list))

class ExitDeckButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🚪 Выйти", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="👋 Закрыто!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

# ===== БОЙ =====
class BattleDeckView(discord.ui.View):
    def __init__(self, opponent: discord.Member):
        super().__init__(timeout=60)
        self.opponent = opponent
        for name in ["К1", "К2", "К3", "К4", "К5"]:
            self.add_item(BattleDeckButton(name, opponent))
        self.add_item(CancelBattleButton())

class BattleDeckButton(discord.ui.Button):
    def __init__(self, deck_name, opponent):
        super().__init__(label=deck_name, style=discord.ButtonStyle.primary)
        self.deck_name = deck_name
        self.opponent = opponent

    async def callback(self, interaction: discord.Interaction):
        my_decks = get_decks(interaction.user.id)
        my_deck = my_decks.get(self.deck_name, [])
        if not my_deck:
            await interaction.response.edit_message(
                content=f"❌ Колода **{self.deck_name}** пуста! Выбери другую.", view=BattleDeckView(self.opponent))
            return
        opp_deck_name, opp_deck = get_best_deck(self.opponent.id)
        if not opp_deck:
            await interaction.response.edit_message(
                content=f"❌ У **{self.opponent.name}** нет колод! Бой невозможен.", view=None)
            return
        my_power = sum(f.get("power", 0) for f in my_deck)
        opp_power = sum(f.get("power", 0) for f in opp_deck)
        my_atk = sum(f.get("atk", 0) for f in my_deck)
        opp_atk = sum(f.get("atk", 0) for f in opp_deck)
        my_def = sum(f.get("def", 0) for f in my_deck)
        opp_def = sum(f.get("def", 0) for f in opp_deck)
        my_score = my_power + random.randint(-20, 20)
        opp_score = opp_power + random.randint(-20, 20)
        winner = interaction.user if my_score >= opp_score else self.opponent
        текст = (
            f"⚔️ **БОЙ НАЧИНАЕТСЯ!**\n\n"
            f"**{interaction.user.name}** (Колода {self.deck_name})\n"
            f"⚔️ Атака: {my_atk} | 🛡️ Защита: {my_def} | 💪 Сила: {my_power}\n\n"
            f"**VS**\n\n"
            f"**{self.opponent.name}** (Колода {opp_deck_name})\n"
            f"⚔️ Атака: {opp_atk} | 🛡️ Защита: {opp_def} | 💪 Сила: {opp_power}\n\n"
            f"{'🏆 **ПОБЕДИТЕЛЬ: ' + winner.name + '**! 🎉' if winner == interaction.user else '💀 **ПОРАЖЕНИЕ!** ' + self.opponent.name + ' победил!'}"
        )
        await interaction.response.edit_message(content=текст, view=None)

class CancelBattleButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="❌ Отмена", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="❌ Бой отменён!", view=None)

# ===== КОМАНДЫ =====

@tree.command(name="баланс", description="Посмотреть баланс")
@app_commands.describe(участник="Участник (необязательно)")
async def баланс(interaction: discord.Interaction, участник: discord.Member = None):
    await interaction.response.defer()
    цель = участник if участник else interaction.user
    bal = get_balance(цель.id)
    income = get_hourly_income(цель.id)
    f_count = len(get_fighters_list(цель.id))
    await interaction.followup.send(
        f"┌─────────────────────┐\n"
        f"        💰 **{цель.name}**\n"
        f"└─────────────────────┘\n"
        f"💵 **{bal}** ликкеров\n"
        f"📈 Доход: **{income}**/час\n"
        f"⚔️ Бойцов: **{f_count}**")

@tree.command(name="сброс", description="Сбросить все балансы до 0")
async def сброс(interaction: discord.Interaction):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    save_file(BALANCE_FILE, {})
    await interaction.followup.send("✅ Все балансы сброшены до **0**!")

@tree.command(name="сбросдохода", description="Сбросить всех бойцов у всех")
async def сбросдохода(interaction: discord.Interaction):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    save_file(FIGHTERS_FILE, {})
    await interaction.followup.send("✅ Все бойцы сброшены!")

@tree.command(name="датьвсем", description="Дать всем участникам ликкеры")
@app_commands.describe(сумма="Сумма для каждого")
async def датьвсем(interaction: discord.Interaction, сумма: int):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    if сумма <= 0:
        await interaction.followup.send("❌ Сумма > 0!", ephemeral=True)
        return
    count = 0
    for member in interaction.guild.members:
        if not member.bot:
            set_balance(member.id, get_balance(member.id) + сумма)
            count += 1
    await interaction.followup.send(f"✅ **{count}** участникам выдано по **{сумма} ликкеров**!")

СТОРОНА_ВЫБОР = [
    app_commands.Choice(name="Орёл", value="орёл"),
    app_commands.Choice(name="Решка", value="решка"),
]

@tree.command(name="оир", description="Орёл или решка")
@app_commands.describe(сторона="Выбери сторону", ставка="Сумма ставки")
@app_commands.choices(сторона=СТОРОНА_ВЫБОР)
async def оир(interaction: discord.Interaction, сторона: app_commands.Choice[str], ставка: int):
    if interaction.channel.name not in CASINO_CHANNELS:
        await interaction.response.send_message("❌ Только в **#казик**!", ephemeral=True)
        return
    if ставка <= 0:
        await interaction.response.send_message("❌ Ставка > 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if ставка > bal:
        await interaction.response.send_message(f"❌ Мало ликкеров! Баланс: **{bal}**", ephemeral=True)
        return
    результат = random.choice(["орёл", "решка"])
    if сторона.value == результат:
        new_bal = bal + ставка
        set_balance(interaction.user.id, new_bal)
        await interaction.response.send_message(
            f"🪙 Выпало **{результат}**!\n🎉 Выиграл **{ставка}** ликкеров!\n💰 Баланс: **{new_bal}**")
    else:
        new_bal = bal - ставка
        set_balance(interaction.user.id, new_bal)
        await interaction.response.send_message(
            f"🪙 Выпало **{результат}**!\n😢 Проиграл **{ставка}** ликкеров!\n💰 Баланс: **{new_bal}**")

@tree.command(name="рул", description="Рулетка")
@app_commands.describe(ставка="Сумма ставки")
async def рул(interaction: discord.Interaction, ставка: int):
    if interaction.channel.name not in CASINO_CHANNELS:
        await interaction.response.send_message("❌ Только в **#казик**!", ephemeral=True)
        return
    if ставка <= 0:
        await interaction.response.send_message("❌ Ставка > 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if ставка > bal:
        await interaction.response.send_message(f"❌ Мало ликкеров! Баланс: **{bal}**", ephemeral=True)
        return
    победа = random.choice([True, False])
    if победа:
        new_bal = bal + ставка
        set_balance(interaction.user.id, new_bal)
        await interaction.response.send_message(
            f"🎰 ДЖЕКПОТ!\n✅ Выиграл **{ставка}** ликкеров!\n💰 Баланс: **{new_bal}**")
    else:
        new_bal = bal - ставка
        set_balance(interaction.user.id, new_bal)
        await interaction.response.send_message(
            f"🎰 Не повезло...\n❌ Проиграл **{ставка}** ликкеров!\n💰 Баланс: **{new_bal}**")

@tree.command(name="мн", description="Множитель — ставка с умножением")
@app_commands.describe(ставка="Сумма ставки")
async def мн(interaction: discord.Interaction, ставка: int):
    if interaction.channel.name not in CASINO_CHANNELS:
        await interaction.response.send_message("❌ Только в **#казик**!", ephemeral=True)
        return
    if ставка <= 0:
        await interaction.response.send_message("❌ Ставка > 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if ставка > bal:
        await interaction.response.send_message(f"❌ Мало ликкеров! Баланс: **{bal}**", ephemeral=True)
        return
    победа = random.choice([True, False])
    множитель = round(random.uniform(1.1, 2.0), 2)
    if победа:
        выигрыш = int(ставка * множитель)
        new_bal = bal + выигрыш
        set_balance(interaction.user.id, new_bal)
        await interaction.response.send_message(
            f"🎲 **Множитель:** x{множитель}\n\n"
            f"🎉 ВЫИГРЫШ!\n"
            f"✅ **{ставка}** × {множитель} = **{выигрыш}** ликкеров!\n"
            f"💰 Баланс: **{new_bal}**")
    else:
        потеря = int(ставка * множитель)
        new_bal = max(0, bal - потеря)
        set_balance(interaction.user.id, new_bal)
        await interaction.response.send_message(
            f"🎲 **Множитель:** x{множитель}\n\n"
            f"💀 ПРОИГРЫШ!\n"
            f"❌ **{ставка}** × {множитель} = **{потеря}** ликкеров потеряно!\n"
            f"💰 Баланс: **{new_bal}**")

@tree.command(name="нак", description="Накрутить баланс участнику")
@app_commands.describe(участник="Участник", сумма="Сумма")
async def нак(interaction: discord.Interaction, участник: discord.Member, сумма: int):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    bal = get_balance(участник.id)
    set_balance(участник.id, bal + сумма)
    await interaction.followup.send(f"✅ {участник.mention} получил **{сумма}** ликкеров\n💰 Баланс: **{bal + сумма}**")

@tree.command(name="пер", description="Перевести ликкеры")
@app_commands.describe(участник="Участник", сумма="Сумма")
async def пер(interaction: discord.Interaction, участник: discord.Member, сумма: int):
    await interaction.response.defer()
    if участник.id == interaction.user.id:
        await interaction.followup.send("❌ Себе нельзя!", ephemeral=True)
        return
    if сумма <= 0:
        await interaction.followup.send("❌ Сумма > 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if сумма > bal:
        await interaction.followup.send(f"❌ Мало ликкеров! Баланс: **{bal}**", ephemeral=True)
        return
    set_balance(interaction.user.id, bal - сумма)
    set_balance(участник.id, get_balance(участник.id) + сумма)
    await interaction.followup.send(f"💸 **{interaction.user.name}** → {участник.mention}\n**{сумма}** ликкеров\n💰 Твой баланс: **{bal - сумма}**")

@tree.command(name="отобрать", description="Отобрать ликкеры")
@app_commands.describe(участник="Участник", сумма="Сумма")
async def отобрать(interaction: discord.Interaction, участник: discord.Member, сумма: int):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    if сумма <= 0:
        await interaction.followup.send("❌ Сумма > 0!", ephemeral=True)
        return
    bal = get_balance(участник.id)
    реально = min(сумма, bal)
    set_balance(участник.id, bal - реально)
    set_balance(interaction.user.id, get_balance(interaction.user.id) + реально)
    await interaction.followup.send(f"💀 У {участник.mention} отобрано **{реально}** ликкеров!\n💰 Тебе: **{реально}**")

@tree.command(name="топ", description="Топ 10 по ликкерам")
async def топ(interaction: discord.Interaction):
    await interaction.response.defer()
    data = load_file(BALANCE_FILE)
    if not data:
        await interaction.followup.send("❌ Нет данных!")
        return
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    текст = "🏆 **Топ 10 по ликкерам:**\n\n"
    for i, (uid, bal) in enumerate(sorted_data):
        try:
            user = await client.fetch_user(int(uid))
            имя = user.name
        except:
            имя = f"Игрок {uid}"
        текст += f"{medals[i]} **{имя}** — {bal} ликкеров\n"
    await interaction.followup.send(текст)

@tree.command(name="ip", description="Узнать IP участника")
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

@tree.command(name="fake_ban", description="Бан на 67 секунд")
@app_commands.describe(участник="Участник")
async def fake_ban(interaction: discord.Interaction, участник: discord.Member):
    роли = [r.name for r in interaction.user.roles]
    if not any(r in роли for r in BAN_ROLES):
        await interaction.response.send_message("❌ Нет прав!", ephemeral=True)
        return
    await interaction.response.send_message(f"🔨 {участник.mention} **забанен на 67 секунд!**")
    try:
        await участник.timeout(discord.utils.utcnow() + timedelta(seconds=67))
    except:
        pass
    await asyncio.sleep(67)
    await interaction.channel.send(f"✅ {участник.mention} бан снят!")

async def страна_autocomplete(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=с, value=с) for с in СПИСОК_СТРАН if current.lower() in с.lower()][:25]

@tree.command(name="отправить", description="Отправить участника в страну")
@app_commands.describe(участник="Участник", страна="Страна")
@app_commands.autocomplete(страна=страна_autocomplete)
async def отправить(interaction: discord.Interaction, участник: discord.Member, страна: str):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if not any(r in роли for r in SEND_ROLES):
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    if страна not in СПИСОК_СТРАН:
        await interaction.followup.send("❌ Страна не найдена!", ephemeral=True)
        return
    await interaction.followup.send(f"✈️ {участник.mention} **отправлен в {страна}!**\n🧳 Счастливого пути!")

@tree.command(name="магазин", description="Открыть магазин")
async def магазин(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    bal = get_balance(interaction.user.id)
    income = get_hourly_income(interaction.user.id)
    await interaction.followup.send(
        f"🏪 **Магаз**\n💰 **{bal}** ликкеров | 📈 **{income}**/час\n\nЧто хочешь купить?",
        view=ShopMainView(), ephemeral=True)

@tree.command(name="боксы", description="Открыть боксы")
@app_commands.describe(количество="Количество (1 = 100 ликкеров)")
async def боксы(interaction: discord.Interaction, количество: int):
    await interaction.response.defer()
    if количество <= 0 or количество > 100:
        await interaction.followup.send("❌ От 1 до 100!", ephemeral=True)
        return
    цена = количество * 100
    bal = get_balance(interaction.user.id)
    if bal < цена:
        await interaction.followup.send(f"❌ Нужно **{цена}**, есть **{bal}**", ephemeral=True)
        return
    set_balance(interaction.user.id, bal - цена)
    результаты = []
    for _ in range(количество):
        rarity, fighter = roll_fighter()
        f = {**fighter, "rarity": rarity}
        add_fighter(interaction.user.id, f)
        результаты.append((rarity, fighter))
    текст = f"📦 **{количество} боксов** за **{цена}** ликкеров!\n\n"
    for rarity, fighter in результаты:
        цвет = RARITY_COLORS.get(rarity, "⬜")
        if rarity == "Секретный":
            текст += f"{цвет} **[СЕКРЕТНЫЙ]** {fighter['emoji']} **{fighter['name']}** +{fighter['income']}/час 🤫\n"
        else:
            текст += f"{цвет} **[{rarity}]** {fighter['emoji']} **{fighter['name']}** +{fighter['income']}/час\n"
    текст += f"\n📈 Доход: **{get_hourly_income(interaction.user.id)}**/час\n💰 Остаток: **{bal - цена}**"
    if len(текст) > 1900:
        текст = текст[:1900] + "..."
    await interaction.followup.send(текст)

@tree.command(name="бойцы", description="Мои бойцы")
async def бойцы(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    f_list = get_fighters_list(interaction.user.id)
    if not f_list:
        await interaction.followup.send("❌ Нет бойцов! Открой `/боксы`", ephemeral=True)
        return
    текст = f"⚔️ **Бойцы {interaction.user.name}:**\n\n"
    for f in f_list:
        цвет = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
        if f.get("rarity") == "Секретный":
            текст += f"{цвет} **[СЕКРЕТНЫЙ]** {f['emoji']} **{f['name']}** +{f['income']}/час | ⚔️{f['atk']} 🛡️{f['def']} 💪{f['power']}\n"
        else:
            текст += f"{цвет} **[{f.get('rarity','?')}]** {f['emoji']} **{f['name']}** +{f['income']}/час | ⚔️{f['atk']} 🛡️{f['def']} 💪{f['power']}\n"
    текст += f"\n📈 Доход: **{sum(f['income'] for f in f_list)}**/час"
    if len(текст) > 1900:
        текст = текст[:1900] + "..."
    await interaction.followup.send(текст, ephemeral=True)

@tree.command(name="всебойцы", description="Все возможные бойцы")
async def всебойцы(interaction: discord.Interaction):
    await interaction.response.defer()
    текст = "⚔️ **Все бойцы:**\n\n"
    for rarity, fighters in FIGHTERS.items():
        if rarity == "Секретный":
            continue
        цвет = RARITY_COLORS.get(rarity, "⬜")
        текст += f"{цвет} **{rarity}:**\n"
        for f in fighters:
            текст += f"  {f['emoji']} {f['name']} | +{f['income']}/час | ⚔️{f['atk']} 🛡️{f['def']} 💪{f['power']}\n"
        текст += "\n"
    текст += "⬛ **Секретный:** ???"
    if len(текст) > 1900:
        текст = текст[:1900] + "..."
    await interaction.followup.send(текст)

@tree.command(name="колода", description="Управление колодами бойцов")
async def колода(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    decks = get_decks(interaction.user.id)
    текст = "⚔️ **Мои колоды:**\n\n"
    for name in ["К1", "К2", "К3", "К4", "К5"]:
        deck = decks.get(name, [])
        power = sum(f.get("power", 0) for f in deck)
        текст += f"{'⚔️' if deck else '🆕'} **{name}** — {len(deck)}/5 бойцов | Сила: {power}\n"
    await interaction.followup.send(текст, view=DeckMainView(interaction.user.id), ephemeral=True)

@tree.command(name="бой", description="Бой с участником")
@app_commands.describe(участник="Участник для боя")
async def бой(interaction: discord.Interaction, участник: discord.Member):
    await interaction.response.defer(ephemeral=True)
    if участник.id == interaction.user.id:
        await interaction.followup.send("❌ Нельзя сражаться с собой!", ephemeral=True)
        return
    my_f = get_fighters_list(interaction.user.id)
    if not my_f:
        await interaction.followup.send("❌ У тебя нет бойцов! Открой `/боксы`", ephemeral=True)
        return
    opp_deck_name, opp_deck = get_best_deck(участник.id)
    if not opp_deck:
        await interaction.followup.send(f"❌ У **{участник.name}** нет колод! Бой невозможен.", ephemeral=True)
        return
    my_decks = get_decks(interaction.user.id)
    has_any = any(my_decks.get(n) for n in ["К1", "К2", "К3", "К4", "К5"])
    if not has_any:
        await interaction.followup.send("❌ У тебя нет колод! Создай колоду через `/колода`", ephemeral=True)
        return
    await interaction.followup.send(
        f"⚔️ **Бой против {участник.name}!**\nВыбери колоду для боя:",
        view=BattleDeckView(участник), ephemeral=True)

threading.Thread(target=run_web, daemon=True).start()
client.run(DISCORD_TOKEN)

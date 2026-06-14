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

# MongoDB подключение
mongo = MongoClient(MONGODB_URI)
db = mongo["discord_bot"]
balances_col = db["balances"]

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

CASINO_CHANNELS = ["казик", "казино", "лучшие-по-казику", "чемпионат-по-казику"]

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

УЛИЦЫ = ["ул. Ленина", "пр. Мира", "ул. Пушкина", "ул. Гагарина", "пр. Победы",
          "ул. Советская", "ул. Садовая", "пр. Независимости", "ул. Центральная"]

BAN_ROLES = ["Модератор", "Главный Модератор", "Создатель Сервера"]
SEND_ROLES = ["Главный Модератор", "Владелец Сервера"]

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
    while True:
        now = datetime.now(msk)
        seconds_until_midnight = ((24 - now.hour - 1) * 3600 +
                                   (60 - now.minute - 1) * 60 +
                                   (60 - now.second))
        await asyncio.sleep(seconds_until_midnight)
        balances_col.update_many({}, {"$inc": {"balance": 100}})
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
        self.member = member
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
        self.add_item(BackToMainButton(member))
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
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view = ConfirmBuyView(self.price, self.name, self.emoji_icon, self.index)
        await interaction.response.edit_message(
            content=f"❓ Вы уверены что хотите купить роль **{self.emoji_icon} {self.name}** за **{self.price} ликкеров**?",
            view=view)

class ConfirmBuyView(discord.ui.View):
    def __init__(self, price, name, emoji, index):
        super().__init__(timeout=30)
        self.price = price
        self.name = name
        self.emoji = emoji
        self.index = index

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
            await interaction.response.edit_message(content="❌ Не удалось выдать роль! Проверь иерархию ролей.", view=ExitView())
            return
        set_balance(interaction.user.id, bal - self.price)
        await interaction.response.edit_message(
            content=f"✅ Роль **{self.emoji} {self.name}** получена!\n💰 Остаток: **{bal - self.price} ликкеров**",
            view=ExitView())

    @discord.ui.button(label="❌ Нет", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            content="🚫 Покупка отменена!",
            view=ShopRolesView(0, interaction.user))

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
        super().__init__(label="◀️ Назад", style=discord.ButtonStyle.secondary)
        self.page = page
        self.member = member

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=ShopRolesView(self.page, interaction.user))

class BackToMainButton(discord.ui.Button):
    def __init__(self, member):
        super().__init__(label="🏪 В меню", style=discord.ButtonStyle.secondary)
        self.member = member

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

@tree.command(name="баланс", description="Посмотреть свой баланс")
async def баланс(interaction: discord.Interaction):
    bal = get_balance(interaction.user.id)
    await interaction.response.send_message(f"💰 {interaction.user.name}, твой баланс: **{bal} ликкеров**", ephemeral=True)

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
    новый_баланс = bal + сумма
    set_balance(участник.id, новый_баланс)
    await interaction.response.send_message(
        f"✅ Готово! {участник.name} получил **{сумма} ликкеров**\n"
        f"💰 Новый баланс: **{новый_баланс} ликкеров**")

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

СПИСОК_СТРАН = [с[0] for с in СТРАНЫ]

@tree.command(name="отправить", description="Отправить участника в страну")
@app_commands.describe(участник="Участник", страна="Страна на русском")
async def отправить(interaction: discord.Interaction, участник: discord.Member, страна: str):
    роли = [r.name for r in interaction.user.roles]
    if not any(r in роли for r in SEND_ROLES):
        await interaction.response.send_message("❌ У тебя нет прав!", ephemeral=True)
        return
    страна_норм = страна.strip().capitalize()
    if страна_норм not in СПИСОК_СТРАН:
        список = ", ".join(СПИСОК_СТРАН)
        await interaction.response.send_message(
            f"❌ Страна не найдена! Доступные страны:\n{список}", ephemeral=True)
        return
    await interaction.response.send_message(
        f"✈️ {участник.mention} **отправлен в {страна_норм}!**\n"
        f"🧳 Счастливого пути!")

@tree.command(name="отобрать", description="Отобрать ликкеры у участника")
@app_commands.describe(участник="Участник", сумма="Сумма")
async def отобрать(interaction: discord.Interaction, участник: discord.Member, сумма: int):
    роли = [r.name for r in interaction.user.roles]
    if "Создатель Сервера" not in роли:
        await interaction.response.send_message("❌ У тебя нет прав!", ephemeral=True)
        return
    if сумма <= 0:
        await interaction.response.send_message("❌ Сумма должна быть больше 0!", ephemeral=True)
        return
    bal = get_balance(участник.id)
    новый_баланс = max(0, bal - сумма)
    set_balance(участник.id, новый_баланс)
    await interaction.response.send_message(
        f"💀 У {участник.mention} отобрано **{сумма} ликкеров**!\n"
        f"💰 Новый баланс: **{новый_баланс} ликкеров**")

@tree.command(name="топ", description="Топ 10 игроков по ликкерам")
async def топ(interaction: discord.Interaction):
    await interaction.response.defer()
    top_users = list(balances_col.find().sort("balance", -1).limit(10))
    if not top_users:
        await interaction.followup.send("❌ Нет данных!", ephemeral=True)
        return
    текст = "🏆 **Топ 10 по ликкерам:**\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, doc in enumerate(top_users):
        try:
            user = await client.fetch_user(int(doc["user_id"]))
            имя = user.name
        except:
            имя = f"Пользователь {doc['user_id']}"
        текст += f"{medals[i]} **{имя}** — {doc['balance']} ликкеров\n"
    await interaction.followup.send(текст)

@tree.command(name="магазин", description="Открыть магазин")
async def магазин(interaction: discord.Interaction):
    bal = get_balance(interaction.user.id)
    await interaction.response.send_message(
        f"🏪 **Магаз**\nТвой баланс: **{bal} ликкеров**\n\nЧто хочешь купить?",
        view=ShopMainView(),
        ephemeral=True)

threading.Thread(target=run_web, daemon=True).start()
client.run(DISCORD_TOKEN)


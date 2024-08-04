import disnake
from disnake.ext import commands
import sqlite3

# Конфигурация бота
TOKEN = 'MTI2OTY3MjMxNzc3NzIxNTU2OQ.GU1BpP.MKhCuwAkCS6z4OoulKcdsuZynEoNJOdldO7Tk8'
GUILD_ID = 1058916300090527754  # ID вашего сервера
CHANNEL_ID = 1269672537416142970  # ID канала, где будет отправляться select menu
NOTIFY_CHANNEL_ID = 1269672502553214978  # ID канала для уведомлений

# Подключение к базе данных SQLite
conn = sqlite3.connect('bot_database.db')
c = conn.cursor()

# Создание таблицы, если её нет
c.execute('''CREATE TABLE IF NOT EXISTS items
             (id INTEGER PRIMARY KEY, value TEXT UNIQUE)''')
conn.commit()

# Инициализация бота с необходимыми намерениями
intents = disnake.Intents.default()
intents.message_content = True  # Включаем намерение message_content
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} is ready!')

# Команда для добавления значения в базу данных
@bot.slash_command(description="Add an item to the database")
async def add(inter: disnake.ApplicationCommandInteraction, value: str):
    c.execute("INSERT OR IGNORE INTO items (value) VALUES (?)", (value,))
    conn.commit()
    await inter.response.send_message(f'Value "{value}" added to the database.', ephemeral=True)

# Команда для удаления значения из базы данных
@bot.slash_command(description="Remove an item from the database")
async def remove(inter: disnake.ApplicationCommandInteraction, value: str):
    c.execute("DELETE FROM items WHERE value = ?", (value,))
    conn.commit()
    await inter.response.send_message(f'Value "{value}" removed from the database.', ephemeral=True)

# Класс для кнопок и select menu
class SelectMenuView(disnake.ui.View):
    def __init__(self):
        super().__init__()
        self.selected_value = None
        self.select_menu = SelectMenu(self)
        self.add_item(self.select_menu)

    @disnake.ui.button(label="Занять", style=disnake.ButtonStyle.danger)
    async def occupy_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if self.selected_value:
            user_id = inter.author.id
            await inter.response.send_message(f'Вы заняли "{self.selected_value}".', ephemeral=True)
            notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
            await notify_channel.send(f'<@{user_id}> занял {self.selected_value}')
        else:
            await inter.response.send_message('Пожалуйста, выберите значение из меню.', ephemeral=True)

    @disnake.ui.button(label="Освободить", style=disnake.ButtonStyle.success)
    async def release_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if self.selected_value:
            user_id = inter.author.id
            await inter.response.send_message(f'Вы освободили "{self.selected_value}".', ephemeral=True)
            notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
            await notify_channel.send(f'<@{user_id}> освободил {self.selected_value}')
        else:
            await inter.response.send_message('Пожалуйста, выберите значение из меню.', ephemeral=True)

class SelectMenu(disnake.ui.Select):
    def __init__(self, view):
        self.custom_view = view
        c.execute("SELECT value FROM items")
        items = c.fetchall()
        options = [disnake.SelectOption(label=item[0], value=item[0]) for item in items]
        super().__init__(placeholder="Выберите значение...", min_values=1, max_values=1, options=options)

    async def callback(self, inter: disnake.MessageInteraction):
        self.custom_view.selected_value = self.values[0]
        await inter.response.send_message(f'Вы выбрали "{self.custom_view.selected_value}".', ephemeral=True)

# Команда для отправки select menu
@bot.slash_command(description="Send a select menu")
async def send_select_menu(inter: disnake.ApplicationCommandInteraction):
    view = SelectMenuView()
    await inter.channel.send("Выберите значение и нажмите на кнопку:", view=view)

# Запуск бота
bot.run(TOKEN)
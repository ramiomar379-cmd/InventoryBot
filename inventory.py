import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import datetime

load_dotenv()
TOKEN = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# الإعدادات
NORMAL_CHANNELS = [1526668395406430308, 1526668405619560468, 1526668402947653823, 1526668398719926362]
DOUBLE_CHANNEL = 1526668405619560468
ALLOWED_CHANNEL_ID = 1526668730673664010 
ALLOWED_OFFICER_IDS = [1526668395406430308, 1526668405619560468, 1526668402947653823, 1526668398719926362]
ID_COMMAND_CHANNEL = 1526667964038910093

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'البوت جاهز ✅ {bot.user}')

@bot.tree.command(name="check", description="جرد الضباط")
async def check(interaction: discord.Interaction):
    await interaction.response.defer()
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {}
    for channel_id in NORMAL_CHANNELS:
        channel = bot.get_channel(channel_id)
        if not channel: continue
        async for message in channel.history(after=eight_days_ago, limit=None):
            if message.author.bot: continue
            weight = 2 if message.channel.id == DOUBLE_CHANNEL else 1
            stats[message.author.name] = stats.get(message.author.name, 0) + weight
    report = "\n".join([f"{name}: {score} نقطة" for name, score in stats.items()])
    await interaction.followup.send(f"تقرير الجرد:\n{report}")

@bot.tree.command(name="arrest_check", description="جرد وحدة إلقاء القبض")
async def arrest_check(interaction: discord.Interaction):
    if interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message("هذا الأمر يعمل فقط في روم إلقاء القبض.", ephemeral=True)
        return
    await interaction.response.defer()
    stats = {}
    channel = bot.get_channel(ALLOWED_CHANNEL_ID)
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    async for message in channel.history(after=eight_days_ago, limit=None):
        for member in message.mentions:
            if member.id in ALLOWED_OFFICER_IDS:
                stats[member.name] = stats.get(member.name, 0) + 1
    report = "\n".join([f"{name}: {count} عملية قبض" for name, count in stats.items()])
    await interaction.followup.send(f"تقرير وحدة إلقاء القبض:\n{report}")

@bot.command(name="id")
async def id_command(ctx, user_id: int):
    if ctx.channel.id != ID_COMMAND_CHANNEL:
        return
    member = ctx.guild.get_member(user_id)
    if member:
        await ctx.send(f"الشخص المقصود هو: {member.mention}")
    else:
        await ctx.send("عذراً، لم أجد شخصاً يحمل هذا الأيدي في السيرفر.")

bot.run(TOKEN)

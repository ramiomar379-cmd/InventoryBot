import discord
from discord.ext import commands
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# الإعدادات الجديدة
NORMAL_CHANNELS = [1526668339391365170, 1526668345448075284, 1526668348262187188]
DOUBLE_CHANNEL = 1526668342444949696
ALLOWED_CHANNEL_ID = 1526668727657955418

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'✅ بوت الجرد جاهز: {bot.user}')

@bot.tree.command(name="check", description="جرد الصور للضباط")
async def inventory(interaction: discord.Interaction):
    # شرط الروم
    if interaction.channel.id != ALLOWED_CHANNEL_ID:
        await interaction.response.send_message(f"❌ هذا الأمر يعمل فقط في روم خاص بالجرد.", ephemeral=True)
        return

    await interaction.response.send_message("⏳ جاري الجرد...")
    
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {} # سنحفظ فيه ID المستخدم ليتم عمل منشن له

    for channel_id in NORMAL_CHANNELS + [DOUBLE_CHANNEL]:
        channel = bot.get_channel(channel_id)
        if not channel: continue
        
        async for message in channel.history(after=eight_days_ago, limit=None):
            if message.attachments and message.author:
                weight = 2 if message.channel.id == DOUBLE_CHANNEL else 1
                stats[message.author.id] = stats.get(message.author.id, 0) + weight

    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    
    msg = "**📊 تقرير الجرد (منشن):**\n\n"
    for user_id, count in sorted_stats:
        msg += f"👤 <@{user_id}>: {count} صورة\n"
    
    await interaction.edit_original_response(content=msg if sorted_stats else "❌ لا توجد بيانات في آخر 8 أيام.")

bot.run(TOKEN)

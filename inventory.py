import discord
from discord.ext import commands
import os
import datetime

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv('TOKEN')

# الـ IDs الخاصة بك
FRIND_CHANNEL_ID = 1526667955616743514
FRIND_ROLE_ID = 1526667395484225669
OFFICERS_CHANNEL_ID = 1526668727657955418
OFFICERS_ROLE_ID = 1526667395484225670 
ARREST_CHANNEL_ID = 1526668730673664010
ARREST_ROLE_ID = 1526667395484225672

async def send_report(interaction, title, stats, total_days):
    if not stats:
        await interaction.edit_original_response(content=f"📊 **{title} (آخر {total_days} أيام):**\n\nلا يوجد نشاط مسجل.")
        return

    # ترتيب النتائج من الأكثر نشاطاً للأقل
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    report_lines = [f"• {interaction.guild.get_member(uid).mention}: **{count}** رسالة" for uid, count in sorted_stats if interaction.guild.get_member(uid)]
    
    report_text = "\n".join(report_lines)
    await interaction.edit_original_response(content=f"📊 **{title} (آخر {total_days} أيام):**\n\n{report_text}")

@bot.tree.command(name="frind", description="جرد نشاط الفريند")
async def frind_check(interaction: discord.Interaction):
    await interaction.response.send_message("🔍 جاري جرد نشاط الفريند...")
    channel = bot.get_channel(FRIND_CHANNEL_ID)
    stats = {}
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    
    async for msg in channel.history(after=eight_days_ago, limit=None):
        if any(role.id == FRIND_ROLE_ID for role in msg.author.roles):
            stats[msg.author.id] = stats.get(msg.author.id, 0) + 1
    
    await send_report(interaction, "تقرير نشاط الفريند", stats, 8)

@bot.tree.command(name="check_officers", description="جرد الضباط في الروم المخصص")
async def check_officers(interaction: discord.Interaction):
    await interaction.response.send_message("🔍 جاري جرد نشاط الضباط...")
    channel = bot.get_channel(OFFICERS_CHANNEL_ID)
    stats = {}
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    
    async for msg in channel.history(after=eight_days_ago, limit=None):
        if any(role.id == OFFICERS_ROLE_ID for role in msg.author.roles):
            stats[msg.author.id] = stats.get(msg.author.id, 0) + 1
            
    await send_report(interaction, "تقرير نشاط الضباط", stats, 8)

@bot.tree.command(name="check_arrests", description="جرد إلقاء القبض في الروم المخصص")
async def check_arrests(interaction: discord.Interaction):
    await interaction.response.send_message("🔍 جاري جرد عمليات القبض...")
    channel = bot.get_channel(ARREST_CHANNEL_ID)
    stats = {}
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    
    async for msg in channel.history(after=eight_days_ago, limit=None):
        if any(role.id == ARREST_ROLE_ID for role in msg.author.roles):
            stats[msg.author.id] = stats.get(msg.author.id, 0) + 1
            
    await send_report(interaction, "تقرير عمليات القبض", stats, 8)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"البوت جاهز: {bot.user}")

bot.run(TOKEN)

import discord
from discord.ext import commands
import os
import datetime
from flask import Flask
from threading import Thread

# 1. إعداد خادم الويب (لإبقاء البوت يعمل على Render)
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive!"
def run_server(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
Thread(target=run_server, daemon=True).start()

# 2. إعداد البوت
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# الإعدادات
OFFICER_CHANNELS = {1526668339391365170: 2, 1526668345448075284: 2, 1526668348262187188: 2, 1526668342444949696: 4}
ARREST_CHANNELS = {1526668398719926362: 6, 1526668402947653823: 8, 1526668405619560468: 5, 1526668409046171699: 4, 1526668395406430308: 4}

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"البوت جاهز ويعمل: {bot.user}")

# أمر ID التقليدي
@bot.command()
async def id(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"معلومات العضو: {member.name}", color=discord.Color.blue())
    embed.add_field(name="الاسم", value=member.mention, inline=True)
    embed.add_field(name="ID", value=member.id, inline=True)
    await ctx.send(embed=embed)

# دالة التنسيق
def format_report(title, stats, guild):
    if not stats: return f"📊 **{title}**\n\nلا يوجد نشاط مسجل."
    sorted_data = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    lines = [f"• {guild.get_member(uid).mention if guild.get_member(uid) else f'ID:{uid}'} | **{pts} نقطة**" for uid, pts in sorted_data]
    return f"📊 **{title} (آخر 8 أيام):**\n\n" + "\n".join(lines)

# أمر الجرد (الضباط - صور)
@bot.tree.command(name="check_officers", description="جرد نقاط الضباط")
async def check_officers(interaction: discord.Interaction):
    await interaction.response.send_message("جاري الجرد...")
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {}
    for cid, pts in OFFICER_CHANNELS.items():
        channel = bot.get_channel(cid)
        if channel:
            async for msg in channel.history(after=eight_days_ago, limit=None):
                if msg.attachments:
                    stats[msg.author.id] = stats.get(msg.author.id, 0) + pts
    await interaction.edit_original_response(content=format_report("ترتيب الضباط (حسب الصور)", stats, interaction.guild))

# أمر الجرد (القبض - منشن)
@bot.tree.command(name="check_arrests", description="جرد نقاط القبض")
async def check_arrests(interaction: discord.Interaction):
    await interaction.response.send_message("جاري الجرد...")
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {}
    for cid, pts in ARREST_CHANNELS.items():
        channel = bot.get_channel(cid)
        if channel:
            async for msg in channel.history(after=eight_days_ago, limit=None):
                if msg.mentions:
                    stats[msg.author.id] = stats.get(msg.author.id, 0) + pts
    await interaction.edit_original_response(content=format_report("ترتيب القبض (حسب المنشن)", stats, interaction.guild))

bot.run(os.getenv('TOKEN'))

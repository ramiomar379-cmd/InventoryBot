import discord
from discord.ext import commands
import os
import datetime
from flask import Flask
from threading import Thread

# تشغيل الخادم لمنع توقف البوت على Render
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive!"
def run_server(): app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
Thread(target=run_server, daemon=True).start()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# توزيعة القنوات والنقاط
# الضباط: الرومات والقيمة
OFFICER_CHANNELS = {
    1526668339391365170: 2, 1526668345448075284: 2, 
    1526668348262187188: 2, 1526668342444949696: 4 # الروم الأخير بـ 4 نقاط
}

# إلقاء القبض: الرومات والقيمة
ARREST_CHANNELS = {
    1526668398719926362: 6, # اعترافات
    1526668402947653823: 8, # إعدامات
    1526668405619560468: 5, # مداهمات
    1526668409046171699: 4, # أدلة
    1526668395406430308: 4  # قبض
}

async def calculate_points(target_channels):
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    points_board = {}

    for channel_id, points_per_msg in target_channels.items():
        channel = bot.get_channel(channel_id)
        if not channel: continue
        
        async for msg in channel.history(after=eight_days_ago, limit=None):
            if msg.author.bot: continue
            points_board[msg.author.id] = points_board.get(msg.author.id, 0) + points_per_msg
            
    return points_board

@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx):
    await bot.tree.sync(guild=ctx.guild)
    await ctx.send("✅ تمت المزامنة! الأوامر الآن جاهزة.")

@bot.tree.command(name="check_officers", description="جرد نقاط الضباط")
async def check_officers(interaction: discord.Interaction):
    await interaction.response.send_message("🔍 جاري حساب نقاط الضباط...")
    stats = await calculate_points(OFFICER_CHANNELS)
    report = "\n".join([f"• {interaction.guild.get_member(uid).mention}: **{pts}** نقطة" for uid, pts in sorted(stats.items(), key=lambda x: x[1], reverse=True) if interaction.guild.get_member(uid)])
    await interaction.edit_original_response(content=f"📊 **ترتيب نقاط الضباط (آخر 8 أيام):**\n\n{report}")

@bot.tree.command(name="check_arrests", description="جرد نقاط القبض")
async def check_arrests(interaction: discord.Interaction):
    await interaction.response.send_message("🔍 جاري حساب نقاط إلقاء القبض...")
    stats = await calculate_points(ARREST_CHANNELS)
    report = "\n".join([f"• {interaction.guild.get_member(uid).mention}: **{pts}** نقطة" for uid, pts in sorted(stats.items(), key=lambda x: x[1], reverse=True) if interaction.guild.get_member(uid)])
    await interaction.edit_original_response(content=f"📊 **ترتيب نقاط إلقاء القبض (آخر 8 أيام):**\n\n{report}")

bot.run(os.getenv('TOKEN'))

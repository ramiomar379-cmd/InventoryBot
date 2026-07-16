import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import datetime
from flask import Flask
from threading import Thread

# تشغيل الويب لـ Render
app = Flask(__name__)
@app.route('/')
def home():
    return "البوت يعمل!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run_web).start()

# إعدادات البوت
load_dotenv()
TOKEN = os.getenv('TOKEN')
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE_ID'))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'البوت جاهز ✅ {bot.user}')

# 1. أمر البحث بالنيك نيم (يستخدم !id)
@bot.command(name="id")
async def id_command(ctx, *, name: str):
    member = discord.utils.find(lambda m: name.lower() in m.display_name.lower(), ctx.guild.members)
    if member:
        await ctx.send(f"الشخص المقصود هو: {member.mention} (ID: {member.id})")
    else:
        await ctx.send("عذراً، لم أجد شخصاً بهذا الاسم.")

# 2. أمر الجرد (يستخدم !frind)
@bot.command(name="frind")
async def frind_check(ctx):
    # ملاحظة: تأكد من وضع الآيدي الصحيح للقناة هنا
    FRIEND_CHANNEL_ID = 1526667955616743514 
    FRIEND_ROLE_ID = 1526667395484225669
    
    channel = bot.get_channel(FRIEND_CHANNEL_ID)
    if not channel: return
    
    fourteen_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=14)
    stats = {}
    last_times = {}

    async for msg in channel.history(after=fourteen_days_ago, limit=None):
        role = discord.utils.get(msg.author.roles, id=FRIEND_ROLE_ID)
        if role:
            if msg.author.id not in stats:
                stats[msg.author.id] = {"count": 0, "hours": 0}
            stats[msg.author.id]["count"] += 1
            if msg.author.id in last_times:
                diff = (msg.created_at - last_times[msg.author.id]).total_seconds() / 3600
                if diff < 2: stats[msg.author.id]["hours"] += diff
            last_times[msg.author.id] = msg.created_at

    report = "\n".join([f"{ctx.guild.get_member(uid).display_name}: {s['count']} رسالة، {round(s['hours'], 2)} ساعة" 
                        for uid, s in stats.items() if ctx.guild.get_member(uid)])
    await ctx.send(f"تقرير نشاط الفريند:\n{report}" if report else "لا يوجد نشاط.")

# 3. أمر المزامنة (يستخدم !sync)
@bot.command()
async def sync(ctx):
    # التحقق من الرول
    role = discord.utils.get(ctx.author.roles, id=ADMIN_ROLE_ID)
    if role:
        await bot.tree.sync()
        await ctx.send("تمت مزامنة الأوامر بنجاح! ✅")
    else:
        await ctx.send("ليس لديك الرول المطلوب لاستخدام هذا الأمر.")

# 4. مثال لأمر يظهر في قائمة الـ /
@bot.tree.command(name="ping", description="قياس سرعة استجابة البوت")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"البوت يعمل! السرعة: {round(bot.latency * 1000)}ms")

bot.run(TOKEN)

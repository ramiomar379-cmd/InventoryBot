import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import datetime
from flask import Flask
from threading import Thread

# --- تشغيل الويب لضمان عمل البوت على Render ---
app = Flask(__name__)
@app.route('/')
def home():
    return "البوت يعمل!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run_web).start()

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
# إعدادات الفريند الجديدة
FRIEND_ROLE_ID = 1526667395484225669
FRIEND_CHANNEL_ID = 1526667955616743514

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'البوت جاهز ✅ {bot.user}')

# --- الأوامر الأصلية (check, arrest_check) تبقى كما هي ---

@bot.command(name="id")
async def id_command(ctx, *, name_or_id: str):
    if ctx.channel.id != ID_COMMAND_CHANNEL: return
    
    # محاولة البحث بالاسم أو الأيدي
    member = None
    if name_or_id.isdigit():
        member = ctx.guild.get_member(int(name_or_id))
    
    if not member:
        member = discord.utils.get(ctx.guild.members, nick=name_or_id)
    if not member:
        member = discord.utils.get(ctx.guild.members, name=name_or_id)
        
    if member:
        await ctx.send(f"الشخص المقصود هو: {member.mention} (ID: {member.id})")
    else:
        await ctx.send("عذراً، لم أجد شخصاً بهذا الاسم أو الأيدي.")

@bot.command(name="frind")
async def frind_check(ctx):
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
            
            # حساب الوقت
            if msg.author.id in last_times:
                diff = (msg.created_at - last_times[msg.author.id]).total_seconds() / 3600
                if diff < 2: # نحسب فقط الفواصل الزمنية المعقولة للنشاط
                    stats[msg.author.id]["hours"] += diff
            
            last_times[msg.author.id] = msg.created_at

    report = "\n".join([f"{ctx.guild.get_member(uid).display_name}: {s['count']} رسالة، {round(s['hours'], 2)} ساعة" 
                        for uid, s in stats.items() if ctx.guild.get_member(uid)])
    await ctx.send(f"تقرير نشاط الفريند (آخر 14 يوم):\n{report}" if report else "لا يوجد نشاط مسجل.")
@bot.command()
async def sync(ctx):
    if ctx.author.id == "1521418837378072656": # لتتأكد أنك أنت فقط من يستخدم الأمر
        await bot.tree.sync()
        await ctx.send("تمت مزامنة الأوامر بنجاح! يرجى الانتظار دقيقة.")
    else:
        await ctx.send("ليس لديك صلاحية استخدام هذا الأمر.")
        
bot.run(TOKEN)

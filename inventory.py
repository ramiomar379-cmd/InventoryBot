import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import datetime
import requests
from flask import Flask
from threading import Thread

# 1. إعداد خادم الويب (للعمل على Render)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_server, daemon=True).start()

# 2. إعداد البوت
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ==================== الإعدادات ====================
# ضَع هنا أرقام المعرفات (IDs) للرتب المسموح لها بإستخدام أمر mentions و count
ALLOWED_ROLE_IDS = [
    1527238059303899146,  # استبدل هذا الرقم بـ ID الرتبة الأولى
    1527238059303899146,   # استبدل هذا الرقم بـ ID الرتبة الثانية (يمكنك إضافة المزيد)
]

OFFICER_CHANNELS = {
    1526668339391365170: 2,
    1526668345448075284: 2,
    1526668348262187188: 2,
    1526668342444949696: 4
}

ARREST_CHANNELS = {
    1526668398719926362: 6,
    1526668402947653823: 8,
    1526668405619560468: 5,
    1526668409046171699: 4,
    1526668395406430308: 4
}
# ====================================================

# دالة للتحقق من امتلاك المستخدم لرتبة مسموح بها
def has_allowed_role(interaction: discord.Interaction) -> bool:
    if not ALLOWED_ROLE_IDS:
        return True
    user_role_ids = [role.id for role in interaction.user.roles]
    return any(role_id in user_role_ids for role_id in ALLOWED_ROLE_IDS)

# مهمة البقاء نشطاً (نكز الموقع كل دقيقة)
@tasks.loop(minutes=1)
async def keep_alive_task():
    try:
        requests.get("https://my-inventory-bot.onrender.com", timeout=5)
    except Exception:
        pass

@bot.event
async def on_ready():
    await bot.tree.sync()
    keep_alive_task.start()
    print(f"✅ تم تشغيل البوت بنجاح: {bot.user}")

# أمر ID للبحث بالاسم
@bot.command()
async def id(ctx, *, name: str):
    member = None
    for m in ctx.guild.members:
        if name.lower() in m.display_name.lower():
            member = m
            break

    if member:
        embed = discord.Embed(title=f"🔍 نتيجة البحث: {member.display_name}", color=discord.Color.blue())
        embed.add_field(name="الاسم الكامل", value=member.mention, inline=True)
        embed.add_field(name="User ID", value=f"`{member.id}`", inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ لم يتم العثور على أي شخص باسم: `{name}`")

# دالة تنسيق التقارير
def format_report(title, stats, guild, unit_name="نقطة"):
    if not stats:
        return f"📊 **{title}**\n\nلا يوجد نشاط مسجل في هذه الفترة."
    
    sorted_data = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    lines = []
    for rank, (uid, count) in enumerate(sorted_data, 1):
        member = guild.get_member(uid)
        name_str = member.mention if member else f"ID: `{uid}`"
        lines.append(f"`#{rank}` {name_str} ──── **{count}** {unit_name}")
        
    return f"📊 **{title}**\n\n" + "\n".join(lines)

# أمر الجرد (الضباط)
@bot.tree.command(name="check_officers", description="جرد نقاط الضباط")
async def check_officers(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ جاري جرد نقاط الضباط...")
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {}
    
    for cid, pts in OFFICER_CHANNELS.items():
        channel = bot.get_channel(cid)
        if channel:
            async for msg in channel.history(after=eight_days_ago, limit=None):
                if msg.attachments and not msg.author.bot:
                    stats[msg.author.id] = stats.get(msg.author.id, 0) + pts
                    
    await interaction.edit_original_response(content=format_report("ترتيب الضباط (حسب الصور)", stats, interaction.guild, "نقطة"))

# أمر الجرد (القبض)
@bot.tree.command(name="check_arrests", description="جرد نقاط القبض")
async def check_arrests(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ جاري جرد نقاط القبض...")
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {}
    
    for cid, pts in ARREST_CHANNELS.items():
        channel = bot.get_channel(cid)
        if channel:
            async for msg in channel.history(after=eight_days_ago, limit=None):
                if msg.mentions and not msg.author.bot:
                    stats[msg.author.id] = stats.get(msg.author.id, 0) + pts
                    
    await interaction.edit_original_response(content=format_report("ترتيب القبض (حسب المنشن)", stats, interaction.guild, "نقطة"))

# أمر /mentions الجديد
@bot.tree.command(name="mentions", description="حساب عدد المنشنات المرسلة من كل شخص في هذه القناة خلال مدة محددة")
@app_commands.describe(days="عدد الأيام المراد جرد المنشنات خلالها")
async def mentions(interaction: discord.Interaction, days: int):
    if not has_allowed_role(interaction):
        await interaction.response.send_message("❌ ليس لديك الصلاحية لاستخدام هذا الأمر.", ephemeral=True)
        return

    await interaction.response.send_message(f"⏳ جاري حساب المنشنات في هذه القناة لآخر {days} يوم/أيام...")
    start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    stats = {}

    async for msg in interaction.channel.history(after=start_date, limit=None):
        if msg.mentions and not msg.author.bot:
            stats[msg.author.id] = stats.get(msg.author.id, 0) + len(msg.mentions)

    report_title = f"إحصائيات المنشنات في قناة #{interaction.channel.name} (آخر {days} يوم)"
    await interaction.edit_original_response(content=format_report(report_title, stats, interaction.guild, "منشن"))

# أمر /count الجديد
@bot.tree.command(name="count", description="حساب عدد الرسائل لكل شخص في هذه القناة خلال مدة محددة")
@app_commands.describe(days="عدد الأيام المراد جرد الرسائل خلالها")
async def count(interaction: discord.Interaction, days: int):
    if not has_allowed_role(interaction):
        await interaction.response.send_message("❌ ليس لديك الصلاحية لاستخدام هذا الأمر.", ephemeral=True)
        return

    await interaction.response.send_message(f"⏳ جاري حساب عدد الرسائل في هذه القناة لآخر {days} يوم/أيام...")
    start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    stats = {}

    async for msg in interaction.channel.history(after=start_date, limit=None):
        if not msg.author.bot:
            stats[msg.author.id] = stats.get(msg.author.id, 0) + 1

    report_title = f"إحصائيات الرسائل في قناة #{interaction.channel.name} (آخر {days} يوم)"
    await interaction.edit_original_response(content=format_report(report_title, stats, interaction.guild, "رسالة"))

bot.run(os.getenv('TOKEN'))

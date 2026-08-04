import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import datetime
import requests
from flask import Flask
from threading import Thread

# ==========================================================
# 1. إعداد خادم الويب (للعمل على Render وإبقاء البوت نشطاً)
# ==========================================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_server():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

Thread(target=run_server, daemon=True).start()

# ==========================================================
# 2. إعداد البوت
# ==========================================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- الإعدادات العامة ----------
OFFICER_CHANNELS = {
    1526668339391365170: 2,
    1526668345448075284: 2,
    1526668348262187188: 2,
    1526668342444949696: 4,
}

ARREST_CHANNELS = {
    1526668398719926362: 6,
    1526668402947653823: 8,
    1526668405619560468: 5,
    1526668409046171699: 4,
    1526668395406430308: 4,
}

# ---------- آيدي الرتب المسموح لها باستخدام أوامر /mentions و /count ----------
# ضع هنا آيدي الرتب (Role IDs) المسموح لأصحابها استخدام هذين الأمرين، مفصولة بفاصلة
ALLOWED_ROLE_IDS = [
    1527238059303899146,  # <-- استبدل هذا برقم آيدي الرتبة الأولى
    1527238059303899146,  # <-- استبدل هذا برقم آيدي الرتبة الثانية (اختياري، احذف السطر إذا لم تحتجه)
]


def has_allowed_role(interaction: discord.Interaction) -> bool:
    """يتحقق فيما إذا كان المستخدم يملك إحدى الرتب المسموح لها باستخدام الأمر."""
    if not isinstance(interaction.user, discord.Member):
        return False
    user_role_ids = {role.id for role in interaction.user.roles}
    return any(rid in user_role_ids for rid in ALLOWED_ROLE_IDS)


# ==========================================================
# 3. مهمة البقاء نشطاً (نكز الموقع كل دقيقة)
# ==========================================================
@tasks.loop(minutes=1)
async def keep_alive_task():
    try:
        requests.get("https://my-inventory-bot.onrender.com")
    except Exception:
        pass


@bot.event
async def on_ready():
    await bot.tree.sync()
    keep_alive_task.start()
    print(f"✅ البوت جاهز ويعمل الآن باسم: {bot.user}")


# ==========================================================
# 4. أمر ID للبحث عن عضو بالاسم
# ==========================================================
@bot.command()
async def id(ctx, *, name: str):
    member = None
    for m in ctx.guild.members:
        if name.lower() in m.display_name.lower():
            member = m
            break

    if member:
        embed = discord.Embed(
            title=f"🔎 تم العثور على: {member.display_name}",
            color=discord.Color.green(),
        )
        embed.add_field(name="الاسم الكامل", value=member.mention, inline=True)
        embed.add_field(name="User ID", value=member.id, inline=True)
        embed.add_field(name="للنسخ", value=f"`{member.id}`", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ لم أجد أحداً بهذا الاسم: **{name}**")


# ==========================================================
# 5. دالة تنسيق تقارير الجرد
# ==========================================================
def format_report(title, stats, guild, unit="نقطة"):
    if not stats:
        return f"📊 **{title}**\n\nلا يوجد نشاط مسجل خلال هذه الفترة."

    sorted_data = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    lines = []
    for rank, (uid, value) in enumerate(sorted_data, start=1):
        member = guild.get_member(uid)
        member_text = member.mention if member else f"ID:{uid}"
        lines.append(f"**{rank}.** {member_text} | **{value} {unit}**")

    return f"📊 **{title}:**\n\n" + "\n".join(lines)


# ==========================================================
# 6. أمر الجرد (الضباط)
# ==========================================================
@bot.tree.command(name="check_officers", description="جرد نقاط الضباط خلال آخر 8 أيام")
async def check_officers(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ جاري الجرد، الرجاء الانتظار...")
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {}

    for cid, pts in OFFICER_CHANNELS.items():
        channel = bot.get_channel(cid)
        if channel:
            async for msg in channel.history(after=eight_days_ago, limit=None):
                if msg.attachments:
                    stats[msg.author.id] = stats.get(msg.author.id, 0) + pts

    await interaction.edit_original_response(
        content=format_report("ترتيب الضباط (حسب الصور) - آخر 8 أيام", stats, interaction.guild)
    )


# ==========================================================
# 7. أمر الجرد (القبض)
# ==========================================================
@bot.tree.command(name="check_arrests", description="جرد نقاط القبض خلال آخر 8 أيام")
async def check_arrests(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ جاري الجرد، الرجاء الانتظار...")
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {}

    for cid, pts in ARREST_CHANNELS.items():
        channel = bot.get_channel(cid)
        if channel:
            async for msg in channel.history(after=eight_days_ago, limit=None):
                if msg.mentions:
                    stats[msg.author.id] = stats.get(msg.author.id, 0) + pts

    await interaction.edit_original_response(
        content=format_report("ترتيب القبض (حسب المنشن) - آخر 8 أيام", stats, interaction.guild)
    )


# ==========================================================
# 8. أمر /mentions - حساب عدد المنشنات لكل شخص في نفس الروم
# ==========================================================
@bot.tree.command(name="mentions", description="حساب عدد المنشنات لكل شخص في هذا الروم خلال فترة محددة")
@app_commands.describe(days="عدد الأيام السابقة التي تريد حساب المنشنات خلالها")
async def mentions(interaction: discord.Interaction, days: app_commands.Range[int, 1, 365]):
    if not has_allowed_role(interaction):
        await interaction.response.send_message("❌ ليس لديك صلاحية استخدام هذا الأمر.", ephemeral=True)
        return

    await interaction.response.send_message(f"⏳ جاري حساب المنشنات خلال آخر {days} يوم...")
    since_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    stats = {}

    async for msg in interaction.channel.history(after=since_date, limit=None):
        if msg.mentions:
            # يتم احتساب كل عملية منشن على حدة (لو تم منشن نفس الشخص مرتين بنفس الرسالة تُحسب مرتين)
            for mentioned_user in msg.mentions:
                if mentioned_user.bot:
                    continue
                stats[mentioned_user.id] = stats.get(mentioned_user.id, 0) + 1

    await interaction.edit_original_response(
        content=format_report(f"عدد المنشنات في هذا الروم (آخر {days} يوم)", stats, interaction.guild, unit="منشن")
    )


# ==========================================================
# 9. أمر /count - حساب عدد الرسائل لكل شخص في نفس الروم
# ==========================================================
@bot.tree.command(name="count", description="حساب عدد الرسائل لكل شخص في هذا الروم خلال فترة محددة")
@app_commands.describe(days="عدد الأيام السابقة التي تريد حساب الرسائل خلالها")
async def count(interaction: discord.Interaction, days: app_commands.Range[int, 1, 365]):
    if not has_allowed_role(interaction):
        await interaction.response.send_message("❌ ليس لديك صلاحية استخدام هذا الأمر.", ephemeral=True)
        return

    await interaction.response.send_message(f"⏳ جاري حساب الرسائل خلال آخر {days} يوم...")
    since_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    stats = {}

    async for msg in interaction.channel.history(after=since_date, limit=None):
        if msg.author.bot:
            continue
        stats[msg.author.id] = stats.get(msg.author.id, 0) + 1

    await interaction.edit_original_response(
        content=format_report(f"عدد الرسائل في هذا الروم (آخر {days} يوم)", stats, interaction.guild, unit="رسالة")
    )


# ==========================================================
# 10. تشغيل البوت
# ==========================================================
bot.run(os.getenv('TOKEN'))

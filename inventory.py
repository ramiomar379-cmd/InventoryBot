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

# ---------------------------------- صلاحيات كاونت ومنشن ------------------------------
ALLOWED_ROLE_IDS = [
    1526667402325131414,  # ID الرتبة الأولى
    1526667402325131414,  # ID الرتبة الثانية
]
# -------------------------------------------------------------------------------------

# ---------------------------------- إعدادات المزامنة ----------------------------------
MAIN_GUILD_ID = 1441066070461911193       # ID السيرفر الأساسي
SECONDARY_GUILD_ID = 1526667305017413643  # ID سيرفر النيابة

ROLE_MAPPING = {
    1441072532219498629: 1526667652431347772,
    1441072529111519353: 1526667549956116642,
}
# -------------------------------------------------------------------------------------

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

def has_allowed_role(interaction: discord.Interaction) -> bool:
    if not ALLOWED_ROLE_IDS:
        return True
    user_role_ids = [role.id for role in interaction.user.roles]
    return any(role_id in user_role_ids for role_id in ALLOWED_ROLE_IDS)

async def sync_user_data(main_member: discord.Member, sec_member: discord.Member):
    try:
        target_nick = main_member.display_name
        if sec_member.display_name != target_nick:
            await sec_member.edit(nick=target_nick)
    except Exception as e:
        print(f"❌ تعذر تغيير اسم العضو {sec_member}: {e}")

    try:
        main_role_ids = [r.id for r in main_member.roles]
        roles_to_add = []
        roles_to_remove = []

        for main_role_id, sec_role_id in ROLE_MAPPING.items():
            sec_role = sec_member.guild.get_role(sec_role_id)
            if not sec_role:
                continue

            if main_role_id in main_role_ids:
                if sec_role not in sec_member.roles:
                    roles_to_add.append(sec_role)
            else:
                if sec_role in sec_member.roles:
                    roles_to_remove.append(sec_role)

        if roles_to_add:
            await sec_member.add_roles(*roles_to_add)
        if roles_to_remove:
            await sec_member.remove_roles(*roles_to_remove)
    except Exception as e:
        print(f"❌ تعذر تحديث رتب العضو {sec_member}: {e}")

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if after.guild.id != MAIN_GUILD_ID:
        return

    sec_guild = bot.get_guild(SECONDARY_GUILD_ID)
    if not sec_guild:
        return

    sec_member = sec_guild.get_member(after.id)
    if sec_member:
        await sync_user_data(after, sec_member)

@bot.event
async def on_member_join(member: discord.Member):
    if member.guild.id == SECONDARY_GUILD_ID:
        main_guild = bot.get_guild(MAIN_GUILD_ID)
        if main_guild:
            main_member = main_guild.get_member(member.id)
            if main_member:
                await sync_user_data(main_member, member)

@tasks.loop(minutes=1)
async def keep_alive_task():
    try:
        requests.get("https://al3dl-bot-test.onrender.com", timeout=5)
    except Exception:
        pass

@bot.event
async def on_ready():
    await bot.tree.sync()
    keep_alive_task.start()
    print(f"✅ تم تشغيل البوت بنجاح: {bot.user}")

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

@bot.tree.command(name="mentions", description="حساب عدد المنشنات المرسلة في فترة محددة")
@app_commands.describe(
    start_year="سنة بداية الجرد (مثال: 2026)",
    start_month="شهر بداية الجرد (1-12)",
    start_day="يوم بداية الجرد (1-31)",
    end_year="سنة نهاية الجرد (مثال: 2026)",
    end_month="شهر نهاية الجرد (1-12)",
    end_day="يوم نهاية الجرد (1-31)"
)
async def mentions(
    interaction: discord.Interaction,
    start_year: int, start_month: int, start_day: int,
    end_year: int, end_month: int, end_day: int
):
    if not has_allowed_role(interaction):
        await interaction.response.send_message("❌ ليس لديك الصلاحية لاستخدام هذا الأمر.", ephemeral=True)
        return

    try:
        start_date = datetime.datetime(start_year, start_month, start_day, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end_date = datetime.datetime(end_year, end_month, end_day, 23, 59, 59, tzinfo=datetime.timezone.utc)
    except ValueError:
        await interaction.response.send_message("❌ التاريخ الذي أدخلته غير صحيح!", ephemeral=True)
        return

    await interaction.response.send_message(f"⏳ جاري حساب المنشنات من `{start_day}/{start_month}/{start_year}` إلى `{end_day}/{end_month}/{end_year}`...")
    stats = {}

    async for msg in interaction.channel.history(after=start_date, before=end_date, limit=None):
        if msg.mentions and not msg.author.bot:
            stats[msg.author.id] = stats.get(msg.author.id, 0) + len(msg.mentions)

    report_title = f"منشنات قناة #{interaction.channel.name} ({start_day}/{start_month}/{start_year} - {end_day}/{end_month}/{end_year})"
    await interaction.edit_original_response(content=format_report(report_title, stats, interaction.guild, "منشن"))

@bot.tree.command(name="count", description="حساب عدد الرسائل لكل شخص في فترة محددة")
@app_commands.describe(
    start_year="سنة بداية الجرد (مثال: 2026)",
    start_month="شهر بداية الجرد (1-12)",
    start_day="يوم بداية الجرد (1-31)",
    end_year="سنة نهاية الجرد (مثال: 2026)",
    end_month="شهر نهاية الجرد (1-12)",
    end_day="يوم نهاية الجرد (1-31)"
)
async def count(
    interaction: discord.Interaction,
    start_year: int, start_month: int, start_day: int,
    end_year: int, end_month: int, end_day: int
):
    if not has_allowed_role(interaction):
        await interaction.response.send_message("❌ ليس لديك الصلاحية لاستخدام هذا الأمر.", ephemeral=True)
        return

    try:
        start_date = datetime.datetime(start_year, start_month, start_day, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end_date = datetime.datetime(end_year, end_month, end_day, 23, 59, 59, tzinfo=datetime.timezone.utc)
    except ValueError:
        await interaction.response.send_message("❌ التاريخ الذي أدخلته غير صحيح!", ephemeral=True)
        return

    await interaction.response.send_message(f"⏳ جاري حساب الرسائل من `{start_day}/{start_month}/{start_year}` إلى `{end_day}/{end_month}/{end_year}`...")
    stats = {}

    async for msg in interaction.channel.history(after=start_date, before=end_date, limit=None):
        if not msg.author.bot:
            stats[msg.author.id] = stats.get(msg.author.id, 0) + 1

    report_title = f"رسائل قناة #{interaction.channel.name} ({start_day}/{start_month}/{start_year} - {end_day}/{end_month}/{end_year})"
    await interaction.edit_original_response(content=format_report(report_title, stats, interaction.guild, "رسالة"))



# تفعيل البوت بأستخدام التوكن ليتحضن  الريندر

bot.run(os.getenv('TOKEN'))

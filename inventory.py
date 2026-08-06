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

# ---------------------------------- القنوات والرتب المحددة ------------------------------
MENTIONS_COUNT_ALLOWED_ROLE = 1526667402325131414
ADMIN_ROLE_ID = 1526667402325131414

# رومات اللوق الجديدة المطلوبة
LOG_SLASH_COMMANDS_CHANNEL_ID = 1526668615812907129  # لوق أوامر السلاش
LOG_SYNC_CHANNEL_ID = 1526668612398485584          # لوق المُزامنة
LOG_ATTENDANCE_CHANNEL_ID = 1534711951144390806    # لوق ورقة الحضور
LOG_ID_COMMAND_CHANNEL_ID = 1534715397570560071    # لوق أمر id

# جرد الضباط
OFFICERS_AUDIT_CHANNEL_ID = 1526668727657955418
OFFICERS_ALLOWED_ROLES = [
    1526667489147355146,
    1526667490287947776,
    1526667491353301093,
    1526667492590620865,
    1526667402325131414
]

# جرد الوحدة (القبض)
UNIT_AUDIT_CHANNEL_ID = 1526668730673664010
UNIT_ALLOWED_ROLES = [
    1526667440426188890,
    1526667441395208305,
    1526667402325131414,
    1526667535431504064,
    1526667536542863400
]

# قناة تسجيل الدخول والخروج (النيابة)
ATTENDANCE_CHANNEL_ID = 1526668199662452767
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

# ---------------- متغيرات نظام الحضور والانصراف ----------------
active_sessions = {}
offline_timers = {}
attendance_history = []
event_data = {"is_active": False, "start_time": None}

IMAGE_URL = "https://media.discordapp.net/attachments/1151101245537386609/1472578282963865670/Screenshot_7.png?ex=6a748565&is=6a7333e5&hm=cbe205704e37d40df6e535912e57cb27353d9305f879b2efd12961d384bac3b0&=&format=webp&quality=lossless&width=1280&height=281"
# ----------------------------------------------------------------

def has_role(interaction: discord.Interaction, allowed_roles: list) -> bool:
    user_role_ids = [role.id for role in interaction.user.roles]
    return any(role_id in user_role_ids for role_id in allowed_roles)

def has_single_role(interaction: discord.Interaction, role_id: int) -> bool:
    user_role_ids = [role.id for role in interaction.user.roles]
    return role_id in user_role_ids

# دالة إرسال التقرير الشامل لأوامر السلاش (مع النتيجة والرد)
async def send_slash_log(interaction: discord.Interaction, result_text: str, is_success: bool = True):
    try:
        log_channel = bot.get_channel(LOG_SLASH_COMMANDS_CHANNEL_ID)
        if log_channel:
            color = discord.Color.green() if is_success else discord.Color.red()
            status_title = "✅ تنفيذ أمر سلاش بنجاح" if is_success else "⚠️ فشل أو رفض أمر سلاش"
            
            embed = discord.Embed(title=status_title, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
            embed.add_field(name="👤 العضو", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
            embed.add_field(name="🛠️ الأمر", value=f"`/{interaction.command.name if interaction.command else 'Unknown'}`", inline=True)
            embed.add_field(name="📍 الروم", value=f"{interaction.channel.mention if interaction.channel else 'Unknown'}", inline=True)
            embed.add_field(name="💬 الرد / النتيجة الصادرة", value=f"```{result_text[:1000]}```", inline=False)
            
            await log_channel.send(embed=embed)
    except Exception as e:
        print(f"❌ خطأ في إرسال لوق أوامر السلاش: {e}")

# دالة إرسال لوق المُزامنة
async def send_sync_log(text: str):
    try:
        log_channel = bot.get_channel(LOG_SYNC_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="🔄 لوق المُزامنة", description=text, color=discord.Color.purple(), timestamp=datetime.datetime.now(datetime.timezone.utc))
            await log_channel.send(embed=embed)
    except Exception as e:
        print(f"❌ خطأ في إرسال لوق المُزامنة: {e}")

# دالة إرسال لوق ورقة الحضور
async def send_attendance_log(text: str, color=discord.Color.green()):
    try:
        log_channel = bot.get_channel(LOG_ATTENDANCE_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="📋 لوق ورقة الحضور", description=text, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
            await log_channel.send(embed=embed)
    except Exception as e:
        print(f"❌ خطأ في إرسال لوق ورقة الحضور: {e}")

# دالة إرسال لوق أمر id
async def send_id_log(text: str):
    try:
        log_channel = bot.get_channel(LOG_ID_COMMAND_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="🔍 لوق استخدام أمر id", description=text, color=discord.Color.blue(), timestamp=datetime.datetime.now(datetime.timezone.utc))
            await log_channel.send(embed=embed)
    except Exception as e:
        print(f"❌ خطأ في إرسال لوق أمر id: {e}")

async def sync_user_data(main_member: discord.Member, sec_member: discord.Member):
    changes = []
    try:
        target_nick = main_member.display_name
        if sec_member.display_name != target_nick:
            await sec_member.edit(nick=target_nick)
            changes.append(f"تم تغيير اللقب إلى: `{target_nick}`")
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
                    changes.append(f"إضافة رتبة: {sec_role.name}")
            else:
                if sec_role in sec_member.roles:
                    roles_to_remove.append(sec_role)
                    changes.append(f"إزالة رتبة: {sec_role.name}")

        if roles_to_add:
            await sec_member.add_roles(*roles_to_add)
        if roles_to_remove:
            await sec_member.remove_roles(*roles_to_remove)
            
        if changes:
            log_text = f"👤 العضو: {main_member.mention} (`{main_member.id}`)\n" + "\n".join(changes)
            await send_sync_log(log_text)
            
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

@tasks.loop(minutes=1)
async def check_offline_status():
    now = datetime.datetime.now(datetime.timezone.utc)
    for user_id, login_time in list(active_sessions.items()):
        guild = bot.get_guild(MAIN_GUILD_ID)
        if not guild:
            continue
            
        member = guild.get_member(user_id)
        if member and member.status == discord.Status.offline:
            if user_id not in offline_timers:
                offline_timers[user_id] = now
            elif (now - offline_timers[user_id]).total_seconds() >= 600:
                del active_sessions[user_id]
                del offline_timers[user_id]
                attendance_history.append({
                    "user_id": user_id,
                    "login": login_time,
                    "logout": now
                })
                try:
                    await member.send("⚠️ تم تسجيل خروجك تلقائياً من النظام بسبب بقائك في وضع (Offline) لأكثر من 10 دقائق.")
                except Exception:
                    pass
                await send_attendance_log(f"⚠️ تسجيل خروج تلقائي (أوفلاين) للمحامي: {member.mention} (`{member.id}`)", discord.Color.orange())
        else:
            if user_id in offline_timers:
                del offline_timers[user_id]

@check_offline_status.before_loop
async def before_check():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    await bot.tree.sync()
    keep_alive_task.start()
    check_offline_status.start()
    print(f"✅ تم تشغيل البوت بنجاح: {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.channel.id == ATTENDANCE_CHANNEL_ID:
        now = datetime.datetime.now(datetime.timezone.utc)
        
        if message.content.strip() == '-د':
            active_sessions[message.author.id] = now
            if message.author.id in offline_timers:
                del offline_timers[message.author.id]
                
            embed = discord.Embed(title="تسجيل 📋", color=0x00ff00)
            embed.description = f"المحامي : {message.author.mention}\n\nسجل دخول\n\nحياك الله 🌟"
            embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
            embed.set_image(url=IMAGE_URL) 
            embed.set_footer(text="تسجيل الدخول د\nتسجيل الخروج خ")
            
            await message.channel.send(embed=embed)
            await message.delete()
            await send_attendance_log(f"📥 تسجيل دخول المحامي: {message.author.mention} (`{message.author.id}`)", discord.Color.green())

        elif message.content.strip() == '-خ':
            if message.author.id in active_sessions:
                login_time = active_sessions.pop(message.author.id)
                if message.author.id in offline_timers:
                    del offline_timers[message.author.id]
                    
                attendance_history.append({
                    "user_id": message.author.id,
                    "login": login_time,
                    "logout": now
                })
                
                embed = discord.Embed(title="تسجيل 📋", color=0xff0000)
                embed.description = f"المحامي : {message.author.mention}\n\nسجل خروج\n\nموفق خير 🌟"
                embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
                embed.set_image(url=IMAGE_URL)
                embed.set_footer(text="تسجيل الدخول د\nتسجيل الخروج خ")
                
                await message.channel.send(embed=embed)
                await message.delete()
                
                duration = round((now - login_time).total_seconds() / 3600, 2)
                await send_attendance_log(f"📤 تسجيل خروج المحامي: {message.author.mention} (`{message.author.id}`)\n⏱️ مدة الجلسة: **{duration} ساعة**", discord.Color.red())

    await bot.process_commands(message)

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
        await send_id_log(f"👤 المستخدم: {ctx.author.mention} (`{ctx.author.id}`)\n🔍 البحث عن: `{name}`\n✅ النتيجة: تم العثور على العضو {member.mention} (`{member.id}`)")
    else:
        await ctx.send(f"❌ لم يتم العثور على أي شخص باسم: `{name}`")
        await send_id_log(f"👤 المستخدم: {ctx.author.mention} (`{ctx.author.id}`)\n🔍 البحث عن: `{name}`\n❌ النتيجة: لم يتم العثور على أي عضو بهذا الاسم.")

def format_report_as_embed(title, stats, guild, unit_name="نقطة", color=discord.Color.blue()):
    embed = discord.Embed(title=f"📊 {title}", color=color)
    
    if not stats:
        embed.description = "لا يوجد نشاط مسجل في هذه الفترة."
        return embed
    
    sorted_data = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    desc = ""
    for rank, (uid, count) in enumerate(sorted_data, 1):
        member = guild.get_member(uid)
        name_str = member.mention if member else f"ID: `{uid}`"
        desc += f"`#{rank}` {name_str} ──── **{count}** {unit_name}\n\n"
        
    embed.description = desc
    return embed

@bot.tree.command(name="check_officers", description="جرد نقاط الضباط")
@app_commands.checks.has_any_role(*OFFICERS_ALLOWED_ROLES)
async def check_officers(interaction: discord.Interaction):
    if interaction.channel_id != OFFICERS_AUDIT_CHANNEL_ID:
        msg = f"يمكن استخدام هذا الأمر فقط داخل الروم المخصصة: <#{OFFICERS_AUDIT_CHANNEL_ID}>"
        await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        await send_slash_log(interaction, msg, is_success=False)
        return

    await interaction.response.send_message("⏳ جاري جرد نقاط الضباط...", ephemeral=True)
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {}
    
    for cid, pts in OFFICER_CHANNELS.items():
        channel = bot.get_channel(cid)
        if channel:
            async for msg in channel.history(after=eight_days_ago, limit=None):
                if msg.attachments and not msg.author.bot:
                    stats[msg.author.id] = stats.get(msg.author.id, 0) + pts
                    
    embed_result = format_report_as_embed("ترتيب الضباط (حسب الصور)", stats, interaction.guild, "نقطة")
    await interaction.edit_original_response(content=None, embed=embed_result)
    await send_slash_log(interaction, f"تم جرد نقاط الضباط بنجاح وعرض القائمة.", is_success=True)

@bot.tree.command(name="check_arrests", description="جرد نقاط القبض")
@app_commands.checks.has_any_role(*UNIT_ALLOWED_ROLES)
async def check_arrests(interaction: discord.Interaction):
    if interaction.channel_id != UNIT_AUDIT_CHANNEL_ID:
        msg = f"يمكن استخدام هذا الأمر فقط داخل الروم المخصصة: <#{UNIT_AUDIT_CHANNEL_ID}>"
        await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        await send_slash_log(interaction, msg, is_success=False)
        return

    await interaction.response.send_message("⏳ جاري جرد نقاط القبض...", ephemeral=True)
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {}
    
    for cid, pts in ARREST_CHANNELS.items():
        channel = bot.get_channel(cid)
        if channel:
            async for msg in channel.history(after=eight_days_ago, limit=None):
                if msg.mentions and not msg.author.bot:
                    stats[msg.author.id] = stats.get(msg.author.id, 0) + pts
                    
    embed_result = format_report_as_embed("ترتيب القبض (حسب المنشن)", stats, interaction.guild, "نقطة", discord.Color.red())
    await interaction.edit_original_response(content=None, embed=embed_result)
    await send_slash_log(interaction, "تم جرد نقاط القبض بنجاح وعرض القائمة.", is_success=True)

@bot.tree.command(name="mentions", description="حساب عدد المنشنات المرسلة في فترة محددة")
@app_commands.checks.has_role(MENTIONS_COUNT_ALLOWED_ROLE)
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
    try:
        start_date = datetime.datetime(start_year, start_month, start_day, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end_date = datetime.datetime(end_year, end_month, end_day, 23, 59, 59, tzinfo=datetime.timezone.utc)
    except ValueError:
        msg = "التاريخ الذي أدخلته غير صحيح!"
        await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        await send_slash_log(interaction, msg, is_success=False)
        return

    await interaction.response.send_message(f"⏳ جاري حساب المنشنات من `{start_day}/{start_month}/{start_year}` إلى `{end_day}/{end_month}/{end_year}`...", ephemeral=True)
    stats = {}

    async for msg in interaction.channel.history(after=start_date, before=end_date, limit=None):
        if msg.mentions and not msg.author.bot:
            stats[msg.author.id] = stats.get(msg.author.id, 0) + len(msg.mentions)

    report_title = f"منشنات قناة #{interaction.channel.name} ({start_day}/{start_month} - {end_day}/{end_month})"
    embed_result = format_report_as_embed(report_title, stats, interaction.guild, "منشن", discord.Color.orange())
    await interaction.edit_original_response(content=None, embed=embed_result)
    await send_slash_log(interaction, f"تم حساب المنشنات بنجاح للفترة المحددة.", is_success=True)

@bot.tree.command(name="count", description="حساب عدد الرسائل لكل شخص في فترة محددة")
@app_commands.checks.has_role(MENTIONS_COUNT_ALLOWED_ROLE)
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
    try:
        start_date = datetime.datetime(start_year, start_month, start_day, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end_date = datetime.datetime(end_year, end_month, end_day, 23, 59, 59, tzinfo=datetime.timezone.utc)
    except ValueError:
        msg = "التاريخ الذي أدخلته غير صحيح!"
        await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        await send_slash_log(interaction, msg, is_success=False)
        return

    await interaction.response.send_message(f"⏳ جاري حساب الرسائل من `{start_day}/{start_month}/{start_year}` إلى `{end_day}/{end_month}/{end_year}`...", ephemeral=True)
    stats = {}

    async for msg in interaction.channel.history(after=start_date, before=end_date, limit=None):
        if not msg.author.bot:
            stats[msg.author.id] = stats.get(msg.author.id, 0) + 1

    report_title = f"رسائل قناة #{interaction.channel.name} ({start_day}/{start_month} - {end_day}/{end_month})"
    embed_result = format_report_as_embed(report_title, stats, interaction.guild, "رسالة", discord.Color.green())
    await interaction.edit_original_response(content=None, embed=embed_result)
    await send_slash_log(interaction, "تم حساب عدد الرسائل بنجاح.", is_success=True)

@bot.tree.command(name="الجرد_الأسبوعي", description="يجرد معدل الدخول والخروج للأسبوع الماضي")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def weekly_audit(interaction: discord.Interaction):
    now = datetime.datetime.now(datetime.timezone.utc)
    last_week = now - datetime.timedelta(days=7)
    
    users_stats = {}
    for record in attendance_history:
        if record["logout"] >= last_week:
            uid = record["user_id"]
            if uid not in users_stats:
                users_stats[uid] = 0
            users_stats[uid] += (record["logout"] - record["login"]).total_seconds()
            
    embed = discord.Embed(title="📊 الجرد الأسبوعي للمحامين", color=discord.Color.dark_blue())
    
    if not users_stats:
        embed.description = "لا توجد بيانات للأسبوع الماضي."
        await interaction.response.send_message(embed=embed)
        await send_slash_log(interaction, "الجرد الأسبوعي: لا توجد بيانات للأسبوع الماضي.", is_success=True)
        return

    desc = ""
    for uid, seconds in sorted(users_stats.items(), key=lambda x: x[1], reverse=True):
        member = interaction.guild.get_member(uid)
        name = member.mention if member else f"ID: {uid}"
        desc += f"👤 {name}\n⏳ إجمالي الوقت: **{round(seconds / 3600, 2)} ساعة**\n\n"

    embed.description = desc
    await interaction.response.send_message(embed=embed)
    await send_slash_log(interaction, "تم إرسال والجرد الأسبوعي بنجاح.", is_success=True)

@bot.tree.command(name="الإحصائيات_اليومية", description="قائمة بكل شخص سجل دخول وخروج اليوم")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def daily_stats(interaction: discord.Interaction):
    now = datetime.datetime.now(datetime.timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    embed = discord.Embed(title="📅 إحصائيات اليوم الحالي", color=discord.Color.teal())
    desc = ""
    found = False
    
    for record in attendance_history:
        if record["login"] >= today_start or record["logout"] >= today_start:
            found = True
            member = interaction.guild.get_member(record["user_id"])
            name = member.mention if member else f"ID: {record['user_id']}"
            t_in = record["login"].strftime("%H:%M")
            t_out = record["logout"].strftime("%H:%M")
            desc += f"👤 {name}\n📥 الدخول: `{t_in}`\n📤 الخروج: `{t_out}`\n\n"
            
    if not found:
        desc = "لم يقم أحد بتسجيل الدخول أو الخروج اليوم."
        
    embed.description = desc
    await interaction.response.send_message(embed=embed)
    await send_slash_log(interaction, "تم عرض الإحصائيات اليومية بنجاح.", is_success=True)

@bot.tree.command(name="قائمة_المتصدرين_الشهرية", description="أكثر الأشخاص تفاعلاً خلال آخر شهر")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def monthly_leaderboard(interaction: discord.Interaction):
    now = datetime.datetime.now(datetime.timezone.utc)
    last_month = now - datetime.timedelta(days=30)
    
    users_stats = {}
    for record in attendance_history:
        if record["logout"] >= last_month:
            uid = record["user_id"]
            if uid not in users_stats:
                users_stats[uid] = 0
            users_stats[uid] += (record["logout"] - record["login"]).total_seconds()

    embed = discord.Embed(title="🏆 قائمة المتصدرين الشهرية", color=discord.Color.gold())
    
    if not users_stats:
        embed.description = "لا توجد بيانات كافية."
        await interaction.response.send_message(embed=embed)
        await send_slash_log(interaction, "قائمة المتصدرين الشهرية: لا توجد بيانات كافية.", is_success=True)
        return

    desc = ""
    for rank, (uid, seconds) in enumerate(sorted(users_stats.items(), key=lambda x: x[1], reverse=True), 1):
        member = interaction.guild.get_member(uid)
        name = member.mention if member else f"ID: {uid}"
        desc += f"**المركز {rank}** 🏅\n👤 {name}\n⏱️ **{round(seconds / 3600, 2)} ساعة**\n\n"

    embed.description = desc
    await interaction.response.send_message(embed=embed)
    await send_slash_log(interaction, "تم عرض قائمة المتصدرين الشهرية بنجاح.", is_success=True)

@bot.tree.command(name="قائمة_المتصدرين", description="أكثر الأشخاص تفاعلاً بشكل كامل")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def all_time_leaderboard(interaction: discord.Interaction):
    users_stats = {}
    for record in attendance_history:
        uid = record["user_id"]
        if uid not in users_stats:
            users_stats[uid] = 0
        users_stats[uid] += (record["logout"] - record["login"]).total_seconds()

    embed = discord.Embed(title="👑 قائمة المتصدرين الشاملة", color=discord.Color.purple())
    
    if not users_stats:
        embed.description = "لا توجد بيانات مسجلة بعد."
        await interaction.response.send_message(embed=embed)
        await send_slash_log(interaction, "قائمة المتصدرين الشاملة: لا توجد بيانات مسجلة بعد.", is_success=True)
        return

    desc = ""
    for rank, (uid, seconds) in enumerate(sorted(users_stats.items(), key=lambda x: x[1], reverse=True), 1):
        member = interaction.guild.get_member(uid)
        name = member.mention if member else f"ID: {uid}"
        desc += f"**المركز {rank}** 🌟\n👤 {name}\n⏱️ **{round(seconds / 3600, 2)} ساعة**\n\n"

    embed.description = desc
    await interaction.response.send_message(embed=embed)
    await send_slash_log(interaction, "تم عرض قائمة المتصدرين الشاملة بنجاح.", is_success=True)

@bot.tree.command(name="بدأ_فعالية", description="يبدأ احتساب الساعات لفعالية جديدة")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def start_event(interaction: discord.Interaction):
    event_data["is_active"] = True
    event_data["start_time"] = datetime.datetime.now(datetime.timezone.utc)
    
    embed = discord.Embed(
        title="✅ تم بدء الفعالية بنجاح!", 
        description="سيتم الآن احتساب ساعات التفاعل بشكل منفصل حتى يتم إنهاء الفعالية.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)
    await send_slash_log(interaction, "تم بدء الفعالية بنجاح.", is_success=True)

@bot.tree.command(name="انهاء_الفعالية", description="ينهي الفعالية ويعرض قائمة المتصدرين الخاصة بها")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def end_event(interaction: discord.Interaction):
    if not event_data["is_active"]:
        msg = "لا توجد فعالية نشطة حالياً لإنهائها."
        await interaction.response.send_message(f"⚠️ {msg}", ephemeral=True)
        await send_slash_log(interaction, msg, is_success=False)
        return

    start_time = event_data["start_time"]
    
    users_stats = {}
    for record in attendance_history:
        if record["logout"] >= start_time:
            uid = record["user_id"]
            if uid not in users_stats:
                users_stats[uid] = 0
            log_start = max(record["login"], start_time)
            users_stats[uid] += (record["logout"] - log_start).total_seconds()

    embed = discord.Embed(title="🎉 نتائج الفعالية الخاصة", color=discord.Color.magenta())
    
    if not users_stats:
        embed.description = "انتهت الفعالية ولم يقم أحد بتسجيل الدخول خلالها."
    else:
        desc = ""
        for rank, (uid, seconds) in enumerate(sorted(users_stats.items(), key=lambda x: x[1], reverse=True), 1):
            member = interaction.guild.get_member(uid)
            name = member.mention if member else f"ID: {uid}"
            desc += f"**المركز {rank}** 🎁\n👤 {name}\n⏱️ **{round(seconds / 3600, 2)} ساعة**\n\n"
        embed.description = desc

    event_data["is_active"] = False
    event_data["start_time"] = None
    
    await interaction.response.send_message(embed=embed)
    await send_slash_log(interaction, "تم إنهاء الفعالية وعرض النتائج بنجاح.", is_success=True)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, (app_commands.errors.MissingRole, app_commands.errors.MissingAnyRole)):
        msg = "ليس لديك الصلاحية لاستخدام هذا الأمر."
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        await send_slash_log(interaction, f"فشل بسبب نقص الصلاحيات: {msg}", is_success=False)
    else:
        err_msg = str(error)
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ حدث خطأ أثناء تنفيذ الأمر.", ephemeral=True)
        await send_slash_log(interaction, f"خطأ تقني: {err_msg}", is_success=False)
        print(f"خطأ في أمر السلاش: {error}")

# تشغيل البوت
bot.run(os.getenv('TOKEN'))

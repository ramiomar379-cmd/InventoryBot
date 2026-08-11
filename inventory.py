import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
import io
import datetime
from flask import Flask
from threading import Thread[cite: 5]

# ==========================================
# ⚙️ إعدادات البوت والـ Flask
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()[cite: 5]

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================================
# 📊 المتغيرات القابلة للتعديل
# ==========================================
ADMIN_ROLE_ID = 123456789012345678
MENTIONS_COUNT_ALLOWED_ROLE = 123456789012345678
UNIT_ALLOWED_ROLES = [123456789012345678]
OFFICERS_ALLOWED_ROLES = [123456789012345678]
LEADERS_ROLES = [123456789012345678]

UNIT_AUDIT_CHANNEL_ID = 123456789012345678
OFFICERS_AUDIT_CHANNEL_ID = 123456789012345678
GENERAL_CUSTOM_LOG_ID = 123456789012345678

ARREST_CHANNELS = {123456789012345678: 1}
OFFICER_CHANNELS = {123456789012345678: 1}

SQUADS_DATA = {
    "eco": {"name": "وحدة E.C.O"},
    "air": {"name": "كتيبة الطيران"},
    "unit": {"name": "وحدة إلقاء القبض"}
}

attendance_history = []
event_data = {"is_active": False, "start_time": None}

# ==========================================
# 🛠️ الدوال المساعدة
# ==========================================
def has_single_role(interaction: discord.Interaction, role_id: int) -> bool:
    return any(role.id == role_id for role in interaction.user.roles)

def has_role(interaction: discord.Interaction, role_ids: list) -> bool:
    return any(role.id in role_ids for role in interaction.user.roles)

def format_report_as_embed(title, stats, guild, unit_name, color=discord.Color.blue()):
    embed = discord.Embed(title=title, color=color)
    if not stats:
        embed.description = "لا توجد بيانات مسجلة."
        return embed
    desc = ""
    for rank, (uid, count) in enumerate(sorted(stats.items(), key=lambda x: x[1], reverse=True), 1):
        member = guild.get_member(uid)
        name = member.mention if member else f"ID: {uid}"
        desc += f"**#{rank}** {name} ── **{count} {unit_name}**\n"
    embed.description = desc
    return embed

# ==========================================
# 📝 UI والتقديمات للكتائب
# ==========================================
class AdminApplicationReviewView(discord.ui.View):[cite: 10]
    def __init__(self, applicant: discord.Member, unit: str):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.unit = unit

    @discord.ui.button(label="تم قبوله نهائيًا مُبارك له", style=discord.ButtonStyle.success)
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)[cite: 10]
        if not any(role.id in LEADERS_ROLES for role in interaction.user.roles):[cite: 10]
            return await interaction.followup.send("❌ ليس لديك صلاحية القبول.", ephemeral=True)[cite: 10]
            
        await interaction.followup.send("**⚠️ أرفق صورة خلال دقيقتين للتأكيد (أرسل الصورة هنا في الشات)**", ephemeral=True)[cite: 10]
        def check(m): return m.author == interaction.user and m.channel == interaction.channel and m.attachments[cite: 10]
        try:
            msg = await bot.wait_for('message', check=check, timeout=120.0)[cite: 10]
        except asyncio.TimeoutError:[cite: 10]
            return await interaction.followup.send("❌ انتهى الوقت ولم يتم إرسال الصورة.", ephemeral=True)[cite: 10]

        final_msg = (
            f"مُبارك قبولك في كتيبة بشكل كامل {{ {SQUADS_DATA[self.unit]['name']} }} "
            f"يُرجى التشييك علئ كافة رومات الكتيبة المذكورة إعلاه لفهم النظام والقوانين المعتمدة .\n\n"
            f"{self.applicant.mention}"
        )[cite: 10]
        
        try:
            await self.applicant.send(content=final_msg)[cite: 10]
            if msg.attachments:[cite: 10]
                await self.applicant.send(content=msg.attachments[0].url)[cite: 10]
            await interaction.channel.send(f"✅ تم قبول {self.applicant.mention} وإرسال النتيجة لخاصه بنجاح.")[cite: 10]
        except discord.Forbidden:[cite: 10]
            await interaction.channel.send(f"⚠️ العضو {self.applicant.mention} مقفل الخاص!\n{final_msg}")[cite: 10]
            if msg.attachments:[cite: 10]
                await interaction.channel.send(content=msg.attachments[0].url)[cite: 10]
        
        roles_to_give = []
        if self.unit == "eco": roles_to_give = [1526667532340170952, 1526667580444774490][cite: 10]
        elif self.unit == "air": roles_to_give = [1534969565933600818, 1526667562413326376, 1526667579274559628][cite: 10]
        elif self.unit == "unit": roles_to_give = [1526667577055641681, 1526667549956116642, 1526667548878307410, 1526667547817283725][cite: 10]
        
        for r_id in roles_to_give:[cite: 10]
            r = interaction.guild.get_role(r_id)[cite: 10]
            if r:[cite: 10]
                try: await self.applicant.add_roles(r)[cite: 10]
                except: pass[cite: 10]
                
        for child in self.children: child.disabled = True[cite: 10]
        await interaction.message.edit(view=self)[cite: 10]

    @discord.ui.button(label="للأسف لم يتم قبوله", style=discord.ButtonStyle.danger)
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)[cite: 10]
        if not any(role.id in LEADERS_ROLES for role in interaction.user.roles):[cite: 10]
            return await interaction.followup.send("❌ ليس لديك صلاحية الرفض.", ephemeral=True)[cite: 10]
            
        await interaction.followup.send("**⚠️ أرفق صورة خلال دقيقتين للتأكيد (أرسل الصورة هنا في الشات)**", ephemeral=True)[cite: 10]
        def check(m): return m.author == interaction.user and m.channel == interaction.channel and m.attachments[cite: 10]
        try:
            msg = await bot.wait_for('message', check=check, timeout=120.0)[cite: 10]
        except asyncio.TimeoutError:[cite: 10]
            return await interaction.followup.send("❌ انتهى الوقت ولم يتم إرسال الصورة.", ephemeral=True)[cite: 10]

        rej_msg = (
            f"للأسف لم يتم قبولك في كتيبة ( {SQUADS_DATA[self.unit]['name']} ) "
            f"يُرجئ أعادة المحاولة مرة أخرئ .\n\n"
            f"{self.applicant.mention}"
        )[cite: 10]
        
        try:
            await self.applicant.send(content=rej_msg)[cite: 10]
            if msg.attachments:[cite: 10]
                await self.applicant.send(content=msg.attachments[0].url)[cite: 10]
            await interaction.channel.send(f"✅ تم إبلاغ {self.applicant.mention} بالرفض عبر الخاص.")[cite: 10]
        except discord.Forbidden:[cite: 10]
            await interaction.channel.send(f"⚠️ العضو {self.applicant.mention} مقفل الخاص!\n{rej_msg}")[cite: 10]
            if msg.attachments:[cite: 10]
                await interaction.channel.send(content=msg.attachments[0].url)[cite: 10]

        for child in self.children: child.disabled = True[cite: 10]
        await interaction.message.edit(view=self)[cite: 10]

# ==========================================
# 🛑 أوامر البريفكس (!)
# ==========================================
@bot.command()[cite: 6]
async def id(ctx, *, name: str):
    member = None
    for m in ctx.guild.members:[cite: 6]
        if name.lower() in m.display_name.lower():[cite: 6]
            member = m[cite: 6]
            break[cite: 6]

    if member:[cite: 6]
        embed = discord.Embed(title=f"🔍 نتيجة البحث: {member.display_name}", color=discord.Color.blue())[cite: 6]
        embed.add_field(name="الاسم الكامل", value=member.mention, inline=True)[cite: 6]
        embed.add_field(name="User ID", value=f"`{member.id}`", inline=True)[cite: 6]
        await ctx.send(embed=embed)[cite: 6]
    else:
        await ctx.send(f"❌ لم يتم العثور على أي شخص باسم: `{name}`")[cite: 6]

@bot.command(name="مسح", aliases=["clear"])[cite: 7]
@commands.has_permissions(manage_messages=True)[cite: 7]
async def clear_messages(ctx, amount: int = 10):
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)[cite: 7]
        confirm_msg = await ctx.send(f"✅ **تم مسح {len(deleted)-1} رسالة بنجاح.**")[cite: 7]
        await asyncio.sleep(3)[cite: 7]
        await confirm_msg.delete()[cite: 7]
        
        log_channel = bot.get_channel(GENERAL_CUSTOM_LOG_ID)[cite: 7]
        if log_channel:[cite: 7]
            embed = discord.Embed(
                title="🗑️ لوق مسح رسائل", 
                description=f"الشخص: {ctx.author.mention}\nالروم: {ctx.channel.mention}\nالعدد: {len(deleted)-1}", 
                color=discord.Color.red(), 
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )[cite: 7]
            await log_channel.send(embed=embed)[cite: 7]
    except Exception:[cite: 7]
        await ctx.send("❌ **حدث خطأ أثناء مسح الرسائل، تأكد من صلاحية Manage Messages!**")[cite: 7]

# ==========================================
# ⚡ أوامر السلاش (Slash Commands)
# ==========================================
@bot.tree.command(name="mentions", description="حساب عدد المنشنات المرسلة في فترة محددة")[cite: 2]
async def mentions(interaction: discord.Interaction, start_year: int, start_month: int, start_day: int, end_year: int, end_month: int, end_day: int):
    if not has_single_role(interaction, MENTIONS_COUNT_ALLOWED_ROLE):[cite: 2]
        return await interaction.response.send_message("❌ ليس لديك الصلاحية لاستخدام هذا الأمر.", ephemeral=True)[cite: 2]

    try:
        start_date = datetime.datetime(start_year, start_month, start_day, 0, 0, 0, tzinfo=datetime.timezone.utc)[cite: 2]
        end_date = datetime.datetime(end_year, end_month, end_day, 23, 59, 59, tzinfo=datetime.timezone.utc)[cite: 2]
    except ValueError:[cite: 2]
        return await interaction.response.send_message("❌ التاريخ الذي أدخلته غير صحيح!", ephemeral=True)[cite: 2]

    await interaction.response.send_message(f"⏳ جاري حساب المنشنات...", ephemeral=True)[cite: 2]
    stats = {}[cite: 2]

    async for msg in interaction.channel.history(after=start_date, before=end_date, limit=None):[cite: 2]
        if msg.mentions and not msg.author.bot:[cite: 2]
            stats[msg.author.id] = stats.get(msg.author.id, 0) + len(msg.mentions)[cite: 2]

    embed_result = format_report_as_embed(f"منشنات #{interaction.channel.name}", stats, interaction.guild, "منشن", discord.Color.orange())[cite: 2]
    await interaction.edit_original_response(content=None, embed=embed_result)[cite: 2]

@bot.tree.command(name="count", description="حساب عدد الرسائل لكل شخص في فترة محددة")[cite: 14]
async def count(interaction: discord.Interaction, start_year: int, start_month: int, start_day: int, end_year: int, end_month: int, end_day: int):
    if not has_single_role(interaction, MENTIONS_COUNT_ALLOWED_ROLE):[cite: 14]
        return await interaction.response.send_message("❌ ليس لديك الصلاحية لاستخدام هذا الأمر.", ephemeral=True)[cite: 14]

    try:
        start_date = datetime.datetime(start_year, start_month, start_day, 0, 0, 0, tzinfo=datetime.timezone.utc)[cite: 14]
        end_date = datetime.datetime(end_year, end_month, end_day, 23, 59, 59, tzinfo=datetime.timezone.utc)[cite: 14]
    except ValueError:[cite: 14]
        return await interaction.response.send_message("❌ التاريخ أدخل بشكل خاطئ!", ephemeral=True)[cite: 14]

    await interaction.response.send_message(f"⏳ جاري حساب الرسائل...", ephemeral=True)[cite: 14]
    stats = {}[cite: 14]

    async for msg in interaction.channel.history(after=start_date, before=end_date, limit=None):[cite: 14]
        if not msg.author.bot:[cite: 14]
            stats[msg.author.id] = stats.get(msg.author.id, 0) + 1[cite: 14]

    embed_result = format_report_as_embed(f"رسائل #{interaction.channel.name}", stats, interaction.guild, "رسالة", discord.Color.green())[cite: 14]
    await interaction.edit_original_response(content=None, embed=embed_result)[cite: 14]

@bot.tree.command(name="check_arrests", description="جرد نقاط القبض")[cite: 12]
async def check_arrests(interaction: discord.Interaction):
    if not has_role(interaction, UNIT_ALLOWED_ROLES):[cite: 12]
        return await interaction.response.send_message("❌ ليس لديك الصلاحية.", ephemeral=True)[cite: 12]

    if interaction.channel_id != UNIT_AUDIT_CHANNEL_ID:[cite: 12]
        return await interaction.response.send_message(f"❌ استخدم الأمر داخل الروم المخصصة: <#{UNIT_AUDIT_CHANNEL_ID}>", ephemeral=True)[cite: 12]

    await interaction.response.send_message("⏳ جاري جرد نقاط القبض...", ephemeral=True)[cite: 12]
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)[cite: 12]
    stats = {}[cite: 12]
    
    for cid, pts in ARREST_CHANNELS.items():[cite: 12]
        channel = bot.get_channel(cid)[cite: 12]
        if channel:[cite: 12]
            async for msg in channel.history(after=eight_days_ago, limit=None):[cite: 12]
                if msg.mentions and not msg.author.bot:[cite: 12]
                    stats[msg.author.id] = stats.get(msg.author.id, 0) + pts[cite: 12]
                    
    embed_result = format_report_as_embed("ترتيب القبض (حسب المنشن)", stats, interaction.guild, "نقطة", discord.Color.red())[cite: 12]
    await interaction.edit_original_response(content=None, embed=embed_result)[cite: 12]

@bot.tree.command(name="check_officers", description="جرد نقاط الضباط")[cite: 13]
async def check_officers(interaction: discord.Interaction):
    if not has_role(interaction, OFFICERS_ALLOWED_ROLES):[cite: 13]
        return await interaction.response.send_message("❌ ليس لديك الصلاحية.", ephemeral=True)[cite: 13]

    if interaction.channel_id != OFFICERS_AUDIT_CHANNEL_ID:[cite: 13]
        return await interaction.response.send_message(f"❌ استخدم الأمر داخل الروم المخصصة: <#{OFFICERS_AUDIT_CHANNEL_ID}>", ephemeral=True)[cite: 13]

    await interaction.response.send_message("⏳ جاري جرد نقاط الضباط...", ephemeral=True)[cite: 13]
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)[cite: 13]
    stats = {}[cite: 13]
    
    for cid, pts in OFFICER_CHANNELS.items():[cite: 13]
        channel = bot.get_channel(cid)[cite: 13]
        if channel:[cite: 13]
            async for msg in channel.history(after=eight_days_ago, limit=None):[cite: 13]
                if msg.attachments and not msg.author.bot:[cite: 13]
                    stats[msg.author.id] = stats.get(msg.author.id, 0) + pts[cite: 13]
                    
    embed_result = format_report_as_embed("ترتيب الضباط (حسب الصور)", stats, interaction.guild, "نقطة")[cite: 13]
    await interaction.edit_original_response(content=None, embed=embed_result)[cite: 13]

@bot.tree.command(name="الإحصائيات_اليومية", description="قائمة الحضور اليومي")[cite: 3]
async def daily_stats(interaction: discord.Interaction):
    if not has_single_role(interaction, ADMIN_ROLE_ID):[cite: 3]
        return await interaction.response.send_message("❌ ليس لديك الصلاحية.", ephemeral=True)[cite: 3]

    now = datetime.datetime.now(datetime.timezone.utc)[cite: 3]
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)[cite: 3]
    embed = discord.Embed(title="📅 إحصائيات اليوم", color=discord.Color.teal())[cite: 3]
    desc = ""[cite: 3]
    
    for record in attendance_history:[cite: 3]
        if record["login"] >= today_start or record["logout"] >= today_start:[cite: 3]
            member = interaction.guild.get_member(record["user_id"])[cite: 3]
            name = member.mention if member else f"ID: {record['user_id']}"[cite: 3]
            desc += f"👤 {name}\n📥 `{record['login'].strftime('%H:%M')}` ── 📤 `{record['logout'].strftime('%H:%M')}`\n\n"[cite: 3]
            
    embed.description = desc if desc else "لا يوجد سجلات اليوم."[cite: 3]
    await interaction.response.send_message(embed=embed)[cite: 3]

@bot.tree.command(name="الجرد_الأسبوعي", description="الجرد الأسبوعي للم ساعات")[cite: 4]
async def weekly_audit(interaction: discord.Interaction):
    if not has_single_role(interaction, ADMIN_ROLE_ID):[cite: 4]
        return await interaction.response.send_message("❌ ليس لديك الصلاحية.", ephemeral=True)[cite: 4]

    now = datetime.datetime.now(datetime.timezone.utc)[cite: 4]
    last_week = now - datetime.timedelta(days=7)[cite: 4]
    users_stats = {}[cite: 4]
    
    for record in attendance_history:[cite: 4]
        if record["logout"] >= last_week:[cite: 4]
            uid = record["user_id"][cite: 4]
            users_stats[uid] = users_stats.get(uid, 0) + (record["logout"] - record["login"]).total_seconds()[cite: 4]
            
    embed = discord.Embed(title="📊 الجرد الأسبوعي", color=discord.Color.dark_blue())[cite: 4]
    if not users_stats:[cite: 4]
        embed.description = "لا توجد بيانات للأسبوع الماضي."[cite: 4]
        return await interaction.response.send_message(embed=embed)[cite: 4]

    desc = ""[cite: 4]
    for uid, seconds in sorted(users_stats.items(), key=lambda x: x[1], reverse=True):[cite: 4]
        member = interaction.guild.get_member(uid)[cite: 4]
        name = member.mention if member else f"ID: {uid}"[cite: 4]
        desc += f"👤 {name}\n⏳ الوقت: **{round(seconds / 3600, 2)} ساعة**\n\n"[cite: 4]

    embed.description = desc[cite: 4]
    await interaction.response.send_message(embed=embed)[cite: 4]

@bot.tree.command(name="بدأ_فعالية", description="بدء احتساب ساعات فعالية")[cite: 9]
async def start_event(interaction: discord.Interaction):
    if not has_single_role(interaction, ADMIN_ROLE_ID):[cite: 9]
        return await interaction.response.send_message("❌ ليس لديك الصلاحية.", ephemeral=True)[cite: 9]

    event_data["is_active"] = True[cite: 9]
    event_data["start_time"] = datetime.datetime.now(datetime.timezone.utc)[cite: 9]
    await interaction.response.send_message("✅ تم بدء الفعالية وتفعيل العداد!")[cite: 9]

@bot.tree.command(name="انهاء_الفعالية", description="إنهاء الفعالية وعرض نتائجها")[cite: 8]
async def end_event(interaction: discord.Interaction):
    if not has_single_role(interaction, ADMIN_ROLE_ID):[cite: 8]
        return await interaction.response.send_message("❌ ليس لديك الصلاحية.", ephemeral=True)[cite: 8]

    if not event_data["is_active"]:[cite: 8]
        return await interaction.response.send_message("⚠️ لا توجد فعالية نشطة حالياً.", ephemeral=True)[cite: 8]

    start_time = event_data["start_time"][cite: 8]
    users_stats = {}[cite: 8]
    
    for record in attendance_history:[cite: 8]
        if record["logout"] >= start_time:[cite: 8]
            uid = record["user_id"][cite: 8]
            log_start = max(record["login"], start_time)[cite: 8]
            users_stats[uid] = users_stats.get(uid, 0) + (record["logout"] - log_start).total_seconds()[cite: 8]

    embed = discord.Embed(title="🎉 نتائج الفعالية", color=discord.Color.magenta())[cite: 8]
    desc = ""[cite: 8]
    for rank, (uid, seconds) in enumerate(sorted(users_stats.items(), key=lambda x: x[1], reverse=True), 1):[cite: 8]
        member = interaction.guild.get_member(uid)[cite: 8]
        name = member.mention if member else f"ID: {uid}"[cite: 8]
        desc += f"**#{rank}** 👤 {name} ── ⏱️ **{round(seconds / 3600, 2)} ساعة**\n"[cite: 8]
        
    embed.description = desc if desc else "لم يشارك أحد خلال وقت الفعالية."[cite: 8]
    event_data["is_active"] = False[cite: 8]
    event_data["start_time"] = None[cite: 8]
    await interaction.response.send_message(embed=embed)[cite: 8]

@bot.tree.command(name="قائمة_المتصدرين", description="المتصدرين التراكمي")[cite: 11]
async def all_time_leaderboard(interaction: discord.Interaction):
    if not has_single_role(interaction, ADMIN_ROLE_ID):[cite: 11]
        return await interaction.response.send_message("❌ ليس لديك الصلاحية.", ephemeral=True)[cite: 11]

    users_stats = {}[cite: 11]
    for record in attendance_history:[cite: 11]
        uid = record["user_id"][cite: 11]
        users_stats[uid] = users_stats.get(uid, 0) + (record["logout"] - record["login"]).total_seconds()[cite: 11]

    embed = discord.Embed(title="👑 المتصدرين الشاملين", color=discord.Color.purple())[cite: 11]
    desc = ""[cite: 11]
    for rank, (uid, seconds) in enumerate(sorted(users_stats.items(), key=lambda x: x[1], reverse=True), 1):[cite: 11]
        member = interaction.guild.get_member(uid)[cite: 11]
        name = member.mention if member else f"ID: {uid}"[cite: 11]
        desc += f"**#{rank}** 👤 {name} ── ⏱️ **{round(seconds / 3600, 2)} ساعة**\n"[cite: 11]

    embed.description = desc if desc else "لا توجد بيانات مسجلة."[cite: 11]
    await interaction.response.send_message(embed=embed)[cite: 11]

# ==========================================
# 🚀 التحديث والتسغيل
# ==========================================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ البوت شغال وسوى Sync لأوامر السلاش باسم {bot.user}")

keep_alive()[cite: 5]
bot.run(os.getenv("TOKEN"))

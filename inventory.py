import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import datetime
import asyncio
import requests
import json
import random
import io  # تمت الإضافة لضمان عمل نظام ملفات الـ PDF في البنك المركزي
from flask import Flask
from threading import Thread

# ==========================================
# 1. إعداد خادم الويب (للعمل على Render)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_server, daemon=True).start()

# ==========================================
# 2. إعداد البوت والنوايا (Intents)
# ==========================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================================
# 3. إعدادات الأيديات (القنوات والرتب)
# ==========================================
MENTIONS_COUNT_ALLOWED_ROLE = 1526667402325131414
ADMIN_ROLE_ID = 1526667402325131414
SUMMON_ALLOWED_ROLE_ID = 1527238059303899146
SQUAD_AUDIT_ROLES = [1526667439306178580, 1526957036561236141]
LEADERS_ROLES = [
    1526667440426188890, 1526667441395208305, 1535777419368071410,
    1526667442452168815, 1526667443454476328, 1535777723249729627,
    1526667445450838046, 1526667446503608341, 1526667447590191104, 1535777899649441923
]
LOG_SLASH_COMMANDS_CHANNEL_ID = 1526668615812907129  
LOG_SYNC_CHANNEL_ID = 1526668612398485584          
LOG_ATTENDANCE_CHANNEL_ID = 1534711951144390806    
LOG_ID_COMMAND_CHANNEL_ID = 1534715397570560071    
GENERAL_CUSTOM_LOG_ID = 1534943475945177338
APPLICATIONS_LOG_CHANNEL_ID = 1526668577971765449
SQUAD_AUDIT_TARGET_CHANNEL_ID = 1526668237809520710
EXTRA_AUDIT_LOG_CHANNEL_ID = 1526668577971765449
SUMMON_TARGET_CHANNEL_ID = 1534729850160545942
OFFICERS_AUDIT_CHANNEL_ID = 1526668727657955418
UNIT_AUDIT_CHANNEL_ID = 1526668730673664010
ATTENDANCE_CHANNEL_ID = 1526668199662452767
TARGET_CHANNELS_FOR_DIVIDER = [
    1534713004271079604, 1526668612398485584, 1526668615812907129,
    1534715397570560071, 1534711951144390806, 1526668510649122947,
    1526668448673828944, 1526668350846140599, 1526668314078740621,
    1526955624255066332, 1527751172029550713, 1526668199662452767,
    1526668203546382406, 1526668224140414986, 1528548590392180846,
    1527474093694390374, 1527464432618438778, 1526668041843249233,
    1526668648041681006, 1531025442390147262, 1534729850160545942
]
WEEKLY_WINNER_ROLE_ID = 1534965674840035419
MONTHLY_WINNER_ROLE_ID = 1526667494901809202
MAIN_GUILD_ID = 1441066070461911193      
SECONDARY_GUILD_ID = 1526667305017413643  

# ==========================================
# 4. إعدادات بيانات الكتائب ونقاطها
# ==========================================
SQUADS_DATA = {
    "unit": {
        "name": "وحدة إلقاء القبض",
        "role_id": 1526667549956116642,
        "channels": [1526668398719926362, 1526668402947653823, 1526668405619560468, 1526668409046171699, 1526668395406430308],
        "leaders": [1526667440426188890, 1526667441395208305]
    },
    "eco": {
        "name": "E.C.O",
        "role_id": 1526667532340170952,
        "channels": [1526668472702992514, 1526668479556489307, 1526668482349891784],
        "leaders": [1526667442452168815, 1526667443454476328]
    },
    "air": {
        "name": "الطيران",
        "role_id": 1534969565933600818,
        "channels": [1526668531486163135, 1526668535634460813],
        "leaders": [1526667445450838046, 1526667446503608341, 1526667447590191104]
    }
}
ROLE_MAPPING = {
    1441072532219498629: 1526667652431347772,
    1441072529111519353: 1526667549956116642,
}

IMAGE_URL = "https://media.discordapp.net/attachments/1151101245537386609/1472578282963865670/Screenshot_7.png"
DIVIDER_GIF_URL = "https://media.discordapp.net/attachments/1522904957391474759/1534717039459962950/49c865eae934de94.gif"
ACCEPT_FINAL_IMG = "https://media.discordapp.net/attachments/1526668577971765449/1535776350089252935/4.png"
ACCEPT_INITIAL_IMG = "https://media.discordapp.net/attachments/1526668577971765449/1535775643822727198/3.png"
MENU_IMAGE_URL = "https://media.discordapp.net/attachments/1526668577971765449/1536100000000000000/image_3ee0b6.png"

active_sessions = {}
offline_timers = {}
attendance_history = []
channel_previous_permissions = {}

# ==========================================
# 5. دوال حفظ البيانات
# ==========================================
DATA_FILE = "bot_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"weekly_audit": 1, "monthly_audit": 1, "time_adjustments": {}, "squad_points_adjustments": {"unit": 0, "eco": 0, "air": 0}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

bot_data = load_data()

# ==========================================
# 6. دوال مساعدة عامة
# ==========================================
def has_squad_audit_permission(interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator: return True
    return any(role_id in [role.id for role in interaction.user.roles] for role_id in SQUAD_AUDIT_ROLES)

def get_leaders_signatures(guild: discord.Guild) -> str:
    role = guild.get_role(1535725186957971458)
    if not role or not role.members: return "**لا يوجد مسؤولين بهذه الرتبة حالياً**"
    members = role.members
    sig_text = ""
    if len(members) >= 1: sig_text += f"الرتبة الأولى وهي مسؤول الكتائب اسمها\n{members[0].mention}\n\n"
    if len(members) >= 2: sig_text += f"الرتبة الثانية نائب مسؤول الكتائب\n{members[1].mention}\n"
    return sig_text

async def send_custom_log(title: str, description: str, color=discord.Color.blue(), channel_id=GENERAL_CUSTOM_LOG_ID):
    try:
        log_channel = bot.get_channel(channel_id)
        if log_channel:
            embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
            await log_channel.send(embed=embed)
    except: pass

async def sync_user_data(main_member: discord.Member, sec_member: discord.Member):
    changes = []
    try:
        target_nick = main_member.display_name
        if sec_member.display_name != target_nick:
            await sec_member.edit(nick=target_nick)
            changes.append(f"تغيير اللقب إلى: `{target_nick}`")
    except: pass
    try:
        main_role_ids = [r.id for r in main_member.roles]
        roles_to_add, roles_to_remove = [], []
        for main_role_id, sec_role_id in ROLE_MAPPING.items():
            sec_role = sec_member.guild.get_role(sec_role_id)
            if not sec_role: continue
            if main_role_id in main_role_ids:
                if sec_role not in sec_member.roles:
                    roles_to_add.append(sec_role)
                    changes.append(f"إضافة رتبة: {sec_role.name}")
            else:
                if sec_role in sec_member.roles:
                    roles_to_remove.append(sec_role)
                    changes.append(f"إزالة رتبة: {sec_role.name}")
        
        if roles_to_add: await sec_member.add_roles(*roles_to_add)
        if roles_to_remove: await sec_member.remove_roles(*roles_to_remove)
       
        if changes:
            await send_custom_log("🔄 لوق مزامنة عضو", f"العضو: {sec_member.mention}\nالتغييرات:\n- " + "\n- ".join(changes), channel_id=LOG_SYNC_CHANNEL_ID)
    except: pass

# ==========================================
# 7. الأحداث والمهام
# ==========================================
@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if after.guild.id != MAIN_GUILD_ID: return
    sec_guild = bot.get_guild(SECONDARY_GUILD_ID)
    if sec_guild:
        sec_member = sec_guild.get_member(after.id)
        if sec_member: await sync_user_data(after, sec_member)

@bot.event
async def on_member_join(member: discord.Member):
    if member.guild.id == SECONDARY_GUILD_ID:
        main_guild = bot.get_guild(MAIN_GUILD_ID)
        if main_guild:
            main_member = main_guild.get_member(member.id)
            if main_member: await sync_user_data(main_member, member)

@tasks.loop(minutes=1)
async def keep_alive_task():
    try: requests.get("https://al3dl-bot-test.onrender.com", timeout=5)
    except: pass

@tasks.loop(seconds=30)
async def check_offline_status():
    now = datetime.datetime.now(datetime.timezone.utc)
    for user_id, login_time in list(active_sessions.items()):
        guild = bot.get_guild(MAIN_GUILD_ID)
        if not guild: continue
        member = guild.get_member(user_id)
        if not member: continue
        if member.status in (discord.Status.offline, discord.Status.invisible):
            if user_id not in offline_timers:
                offline_timers[user_id] = now
            else:
                if (now - offline_timers[user_id]).total_seconds() >= 600:
                    del active_sessions[user_id]
                    del offline_timers[user_id]
                    attendance_history.append({"user_id": user_id, "login": login_time, "logout": now})
                    try: await member.send("**⚠️ تم تسجيل خروجك تلقائياً لمرور 10 دقائق أوفلاين.**")
                    except: pass

@check_offline_status.before_loop
async def before_check():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    bot.add_view(ApplicationMenuView())
    bot.add_view(BankControlPanel())  # لضمان عمل أزرار البنك دائماً بعد إعادة التشغيل
    await bot.tree.sync()
    keep_alive_task.start()
    check_offline_status.start()
    print(f"✅ تم تشغيل البوت بنجاح: {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot: return
   
    if message.content.startswith('!') or message.content.startswith('$'):
        if message.content.startswith('!id'):
            await send_custom_log("📌 أمر ID", f"الشخص: {message.author.mention}\nالأمر: `{message.content}`\nالروم: {message.channel.mention}", channel_id=LOG_ID_COMMAND_CHANNEL_ID)
        else:
            await send_custom_log("⚡ أمر عام", f"الشخص: {message.author.mention}\nالأمر: `{message.content}`\nالروم: {message.channel.mention}", channel_id=GENERAL_CUSTOM_LOG_ID)
    
    if message.channel.id in TARGET_CHANNELS_FOR_DIVIDER:
        if message.content != DIVIDER_GIF_URL and message.channel.id != ATTENDANCE_CHANNEL_ID:
            await message.channel.send(DIVIDER_GIF_URL)
           
    if message.content.strip() == "$سكر_عليهم_الروم_يامدير":
        if not message.author.guild_permissions.administrator: return
        await message.delete()
        guild, channel = message.guild, message.channel
        default_role = guild.default_role
        allowed_roles_list = []
        overwrite_dict = channel.overwrites
        ov = channel.overwrites_for(default_role)
        ov.send_messages = False
        await channel.set_permissions(default_role, overwrite=ov)
        for target, overwrite in overwrite_dict.items():
            if isinstance(target, discord.Role) and target.id != default_role.id:
                if overwrite.send_messages is True or (overwrite.send_messages is None and target.permissions.send_messages):
                    allowed_roles_list.append(target)
                    new_ov = channel.overwrites_for(target)
                    new_ov.send_messages = False
                    await channel.set_permissions(target, overwrite=new_ov)
        channel_previous_permissions[channel.id] = allowed_roles_list
        roles_str = " ".join([r.mention for r in allowed_roles_list]) if allowed_roles_list else "لا توجد"
        await channel.send(f"**🔒 تم إغلاق الروم:\n\nالرتب التي تم إغلاق الروم عليها:\n{roles_str}**")
    
    if message.content.strip() == "$أفتح_عليهم_الروم_يامدير":
        if not message.author.guild_permissions.administrator: return
        await message.delete()
        channel = message.channel
        ov = channel.overwrites_for(message.guild.default_role)
        ov.send_messages = None
        await channel.set_permissions(message.guild.default_role, overwrite=ov)
        for role in channel_previous_permissions.get(channel.id, []):
            ov2 = channel.overwrites_for(role)
            ov2.send_messages = True
            await channel.set_permissions(role, overwrite=ov2)
        await channel.send("**🔓 تم فتح الروم ورجعت الصلاحيات.**")
    
    if message.channel.id == ATTENDANCE_CHANNEL_ID:
        now = datetime.datetime.now(datetime.timezone.utc)
        if message.content.strip() == '-د':
            active_sessions[message.author.id] = now
            if message.author.id in offline_timers: del offline_timers[message.author.id]
            embed = discord.Embed(title="تسجيل", description=f"المحامي : {message.author.mention}\n\nسجل دخول\n\nحياك الله", color=0x00ff00)
            embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
            embed.set_image(url=IMAGE_URL)
            await message.channel.send(embed=embed)
            await message.channel.send(DIVIDER_GIF_URL)
            await message.delete()
            await send_custom_log("🟢 تسجيل دخول", f"العضو: {message.author.mention}", channel_id=LOG_ATTENDANCE_CHANNEL_ID)
           
        elif message.content.strip() == '-خ':
            if message.author.id in active_sessions:
                login_time = active_sessions.pop(message.author.id)
                if message.author.id in offline_timers: del offline_timers[message.author.id]
                attendance_history.append({"user_id": message.author.id, "login": login_time, "logout": now})
                embed = discord.Embed(title="تسجيل", description=f"المحامي : {message.author.mention}\n\nسجل خروج\n\nموفق خير", color=0xff0000)
                embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
                embed.set_image(url=IMAGE_URL)
                await message.channel.send(embed=embed)
                await message.channel.send(DIVIDER_GIF_URL)
                await message.delete()
                await send_custom_log("🔴 تسجيل خروج", f"العضو: {message.author.mention}", channel_id=LOG_ATTENDANCE_CHANNEL_ID)
    
    await bot.process_commands(message)

# ==========================================
# 8. الجرد الأسبوعي والشهري
# ==========================================
@bot.tree.command(name="جرد_الكتائب_الأسبوعي", description="إجراء جرد الكتائب الأسبوعي")
async def weekly_squad_audit(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if not has_squad_audit_permission(interaction):
        return await interaction.followup.send("**❌ عذراً، ليس لديك الصلاحية.**", ephemeral=True)
   
    await interaction.followup.send("**✅ تم بدء الجرد الأسبوعي، يُرجى الانتظار 20 دقيقة للنتيجة النهائية.**", ephemeral=True)
   
    target_channel = interaction.guild.get_channel(SQUAD_AUDIT_TARGET_CHANNEL_ID) or interaction.channel
    signatures = get_leaders_signatures(interaction.guild)
   
    initial_msg = (
        "**| ﷽ |\n\n"
        "السلام عليكم ورحمة الله وبركاته .\n"
        "والصلاة والسلام على أشرف الأنبياء والمرسلين .\n"
        "أسعد الله أوقاتكم بكل خير .\n\n"
        "تحية طيبة أما بعد :\n\n"
        "بإسمنا نحن قيادة الكتائب:\n\n"
        "`بــيـان قــيــادي قــادم بــعــد قلــيــل` \n\n"
        "فـمـا يـخـص إعــلــان كــتــيـبــة الــأســبوع \n\n"
        "سائلين الله التوفيق والسداد...\n\n"
        "يبلغ أمرنا هذا للجهات المختصة فور صدوره .\n\n"
        "التوقيع :\n\n"
        f"{signatures}\n\n"
        "[|| @everyone || -- || @here ||]**"
    )
    await target_channel.send(content=initial_msg)
   
    await asyncio.sleep(1200) # انتظار 20 دقيقة
    start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    squad_scores = {}
    for s_key, s_info in SQUADS_DATA.items():
        total_msgs = bot_data["squad_points_adjustments"].get(s_key, 0)
        for cid in s_info["channels"]:
            ch = bot.get_channel(cid)
            if ch:
                async for msg in ch.history(after=start_date, limit=None):
                    if not msg.author.bot: total_msgs += 1
        squad_scores[s_key] = total_msgs
       
    winner_key = max(squad_scores, key=squad_scores.get)
    winner_info = SQUADS_DATA[winner_key]
    winner_points = squad_scores[winner_key]
   
    winner_role_obj = interaction.guild.get_role(WEEKLY_WINNER_ROLE_ID)
    if winner_role_obj:
        for lead_id in winner_info["leaders"]:
            leader_member = interaction.guild.get_member(lead_id)
            if leader_member:
                try: await leader_member.add_roles(winner_role_obj)
                except: pass
               
    leaders_mentions = " و ".join([f"معالي <@{lid}>" for lid in winner_info["leaders"]])
    current_date = datetime.datetime.now().strftime("%Y/%m/%d")
    count = bot_data["weekly_audit"]
   
    final_msg = (
        "**| ﷽ |\n\n\n"
        f"الرقم: ({count})\n"
        f"التاريخ: ({current_date})\n\n"
        "السلام عليكم ورحمة الله وبركاته .\n"
        "أسعد الله أوقاتكم بكل خير .\n\n"
        "يسرنا الإعلان عن جرد الكتائب الأسبوعي\n\n"
        f"تُنصب كتيبة الأسبوع وهي : <@&{winner_info['role_id']}> .\n\n"
        f"الحاصلين على رتبة : <@&{WEEKLY_WINNER_ROLE_ID}>\n\n"
        f"وذلك بمعدل : ({winner_points}) نقطة .\n\n"
        f"مع كامل الشكر لـــ ({leaders_mentions}) علئ ما قدموه\n\n"
        "مُبارك لهم هذا التميز.\n\n"
        "التوقيع :\n\n"
        f"{signatures}\n\n"
        "[|| @everyone || -- || @here ||]**"
    )
    await target_channel.send(content=final_msg)
    bot_data["weekly_audit"] += 1
    save_data(bot_data)

@bot.tree.command(name="جرد_الكتائب_الشهري", description="إجراء جرد الكتائب الشهري")
async def monthly_squad_audit(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if not has_squad_audit_permission(interaction):
        return await interaction.followup.send("**❌ عذراً، ليس لديك الصلاحية.**", ephemeral=True)
       
    await interaction.followup.send("**✅ تم بدء الجرد الشهري، يُرجى الانتظار 20 دقيقة للنتيجة النهائية.**", ephemeral=True)
   
    target_channel = interaction.guild.get_channel(SQUAD_AUDIT_TARGET_CHANNEL_ID) or interaction.channel
    signatures = get_leaders_signatures(interaction.guild)
   
    initial_msg = (
        "**| ﷽ |\n\n"
        "بإسمنا نحن قيادة الكتائب:\n\n"
        "`بــيـان قــيــادي قــادم بــعــد قلــيــل` \n\n"
        "فـمـا يـخـص إعــلــان كــتــيـبــة الــشــهــر \n\n"
        "التوقيع :\n\n"
        f"{signatures}\n\n"
        "[|| @everyone || -- || @here ||]**"
    )
    await target_channel.send(content=initial_msg)
   
    await asyncio.sleep(1200)
    start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    squad_scores = {}
    for s_key, s_info in SQUADS_DATA.items():
        total_msgs = bot_data["squad_points_adjustments"].get(s_key, 0)
        for cid in s_info["channels"]:
            ch = bot.get_channel(cid)
            if ch:
                async for msg in ch.history(after=start_date, limit=None):
                    if not msg.author.bot: total_msgs += 1
        squad_scores[s_key] = total_msgs
       
    winner_key = max(squad_scores, key=squad_scores.get)
    winner_info = SQUADS_DATA[winner_key]
    winner_points = squad_scores[winner_key]
   
    winner_role_obj = interaction.guild.get_role(MONTHLY_WINNER_ROLE_ID)
    if winner_role_obj:
        for lead_id in winner_info["leaders"]:
            leader_member = interaction.guild.get_member(lead_id)
            if leader_member:
                try: await leader_member.add_roles(winner_role_obj)
                except: pass
               
    leaders_mentions = " و ".join([f"معالي <@{lid}>" for lid in winner_info["leaders"]])
    current_date = datetime.datetime.now().strftime("%Y/%m/%d")
    count = bot_data["monthly_audit"]
   
    final_msg = (
        "**| ﷽ |\n\n\n"
        f"الرقم: ({count})\n"
        f"التاريخ: ({current_date})\n\n"
        "يسرنا الإعلان عن جرد الكتائب الشهري\n\n"
        f"تُنصب كتيبة الشهر وهي : <@&{winner_info['role_id']}> .\n\n"
        f"الحاصلين على رتبة : <@&{MONTHLY_WINNER_ROLE_ID}>\n\n"
        f"وذلك بمعدل : ({winner_points}) نقطة .\n\n"
        f"مع كامل الشكر لـــ ({leaders_mentions}) علئ ما قدموه\n\n"
        "مُبارك لهم هذا التميز.\n\n"
        "التوقيع :\n\n"
        f"{signatures}\n\n"
        "[|| @everyone || -- || @here ||]**"
    )
    await target_channel.send(content=final_msg)
    bot_data["monthly_audit"] += 1
    save_data(bot_data)

# ==========================================
# 9. التقديم للكتائب (المنيو والمودال)
# ==========================================
class AdminApplicationReviewView(discord.ui.View):
    def __init__(self, applicant: discord.Member, unit: str):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.unit = unit

    @discord.ui.button(label="تم قبوله نهائيًا مُبارك له", style=discord.ButtonStyle.success)
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not any(role.id in LEADERS_ROLES for role in interaction.user.roles):
            return await interaction.followup.send("❌ ليس لديك صلاحية القبول.", ephemeral=True)
           
        await interaction.followup.send("**⚠️ أرفق صورة خلال دقيقتين للتأكيد (أرسل الصورة هنا في الشات)**", ephemeral=True)
        def check(m): return m.author == interaction.user and m.channel == interaction.channel and m.attachments
        try: msg = await bot.wait_for('message', check=check, timeout=120.0)
        except asyncio.TimeoutError:
            return await interaction.followup.send("❌ انتهى الوقت ولم يتم إرسال الصورة، أعد الضغط على الزر.", ephemeral=True)
            
        final_msg = (
            f"مُبارك قبولك في كتيبة بشكل كامل {{ {SQUADS_DATA[self.unit]['name']} }} يُرجى التشييك علئ كافة رومات الكتيبة المذكورة إعلاه لفهم النظام والقوانين المعتمدة .\n\n"
            f"{self.applicant.mention}"
        )
        await interaction.channel.send(content=final_msg)
        await interaction.channel.send(ACCEPT_FINAL_IMG)
       
        roles_to_give = []
        if self.unit == "eco": roles_to_give = [1526667532340170952, 1526667580444774490]
        elif self.unit == "air": roles_to_give = [1534969565933600818, 1526667562413326376, 1526667579274559628]
        elif self.unit == "unit": roles_to_give = [1526667577055641681, 1526667549956116642, 1526667548878307410, 1526667547817283725]
       
        for r_id in roles_to_give:
            r = interaction.guild.get_role(r_id)
            if r:
                try: await self.applicant.add_roles(r)
                except: pass
               
        for child in self.children: child.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="للأسف لم يتم قبوله", style=discord.ButtonStyle.danger)
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not any(role.id in LEADERS_ROLES for role in interaction.user.roles):
            return await interaction.followup.send("❌ ليس لديك صلاحية الرفض.", ephemeral=True)
           
        await interaction.followup.send("**⚠️ أرفق صورة خلال دقيقتين للتأكيد (أرسل الصورة هنا في الشات)**", ephemeral=True)
        def check(m): return m.author == interaction.user and m.channel == interaction.channel and m.attachments
        try: msg = await bot.wait_for('message', check=check, timeout=120.0)
        except asyncio.TimeoutError:
            return await interaction.followup.send("❌ انتهى الوقت ولم يتم إرسال الصورة، أعد الضغط على الزر.", ephemeral=True)
            
        rej_msg = f"للأسف لم يتم قبولك في كتيبة ( {SQUADS_DATA[self.unit]['name']} ) يُرجئ أعادة المحاولة مرة أخرئ .\n\n{self.applicant.mention}"
        await interaction.channel.send(content=rej_msg)
        for child in self.children: child.disabled = True
        await interaction.message.edit(view=self)

class ApplicationModal(discord.ui.Modal):
    def __init__(self, unit_key: str, unit_name: str):
        super().__init__(title=f"التقديم على {unit_name}")
        self.unit_key = unit_key
        self.unit_name = unit_name

    name = discord.ui.TextInput(label="الإسم", required=True)
    age = discord.ui.TextInput(label="العُمر (16 فما فوق)", required=True)
    exp = discord.ui.TextInput(label="الخبرات", style=discord.TextStyle.paragraph, required=True)
    hours = discord.ui.TextInput(label="ساعات التواجد (4 فما فوق)", required=True)
    rank = discord.ui.TextInput(label="رتبتك بضباط (ضابط محكمة فما فوق)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try: age_val = int(self.age.value)
        except: age_val = 0
        try: hours_val = int(self.hours.value)
        except: hours_val = 0
       
        if self.exp.value.strip() == "كلشيء":
            return await interaction.followup.send("❌ يُمنع كتابة 'كلشيء' في خانة الخبرات. تم رفض التقديم.", ephemeral=True)
        if age_val < 16 or hours_val < 4:
            return await interaction.followup.send("❌ تم رفض التقديم لعدم استيفاء الشروط الأساسية (العمر أو الساعات).", ephemeral=True)
           
        admin_channel = interaction.guild.get_channel(APPLICATIONS_LOG_CHANNEL_ID)
        if admin_channel:
            data_str = f"**الاسم:** {self.name.value}\n**العمر:** {self.age.value}\n**الخبرات:** {self.exp.value}\n**الساعات:** {self.hours.value}\n**الرتبة:** {self.rank.value}"
            embed = discord.Embed(title=f"تقديم جديد: {self.unit_name}", description=data_str, color=discord.Color.blue())
            view = AdminApplicationReviewView(applicant=interaction.user, unit=self.unit_key)
            await admin_channel.send(content="||@here|| تقديم جديد يحتاج مراجعتكم:", embed=embed, view=view)
           
            try: await interaction.user.send(f"مُبارك قبولك المبدئي في {{ {self.unit_name} }}\n{ACCEPT_INITIAL_IMG}")
            except: pass
        await interaction.followup.send("✅ تم إرسال تقديمك بنجاح. سيتم مراجعته من الإدارة.", ephemeral=True)

class ApplicationMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="التقديم على وحدة إلقاء القبض 🕵️", style=discord.ButtonStyle.danger, custom_id="app_btn_unit")
    async def btn_unit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal("unit", "وحدة إلقاء القبض"))

    @discord.ui.button(label="التقديم على كتيبة E.C.O ⚡", style=discord.ButtonStyle.success, custom_id="app_btn_eco")
    async def btn_eco(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal("eco", "E.C.O"))

    @discord.ui.button(label="التقديم على كتيبة الطيران 🚁", style=discord.ButtonStyle.primary, custom_id="app_btn_air")
    async def btn_air(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal("air", "الطيران"))

@bot.tree.command(name="إستدعاء_التقديم_علئ_الكتائب", description="يستدعي منيو التقديم للكتائب")
async def summon_applications(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ هذا الأمر للأدمن فقط.", ephemeral=True)
   
    embed = discord.Embed(title="نظام تقديم كتائب وزارة العدل", description="للتقديم اختار أحد الكتائب التالية:", color=discord.Color.dark_grey())
    embed.set_image(url=MENU_IMAGE_URL)
    view = ApplicationMenuView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ تم استدعاء المنيو بنجاح.", ephemeral=True)

# ==========================================
# 10. أوامر إضافة وخصم الساعات والنقاط
# ==========================================
@bot.tree.command(name="إضافة_ساعات", description="يضيف ساعات للشخص عبر المنشن")
@app_commands.describe(user="الشخص", hours="ساعات", minutes="دقائق", seconds="ثواني")
async def add_hours(interaction: discord.Interaction, user: discord.Member, hours: int = 0, minutes: int = 0, seconds: int = 0):
    await interaction.response.defer(ephemeral=False)
    if ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles] and not interaction.user.guild_permissions.administrator:
        return await interaction.followup.send("❌ ليس لديك صلاحية.", ephemeral=True)
   
    total_seconds = (hours * 3600) + (minutes * 60) + seconds
    bot_data["time_adjustments"][str(user.id)] = bot_data["time_adjustments"].get(str(user.id), 0) + total_seconds
    save_data(bot_data)
    await interaction.followup.send(f"✅ تم إضافة `{hours}س و {minutes}د و {seconds}ث` لـ {user.mention}.")

@bot.tree.command(name="خصم_ساعات_ورقة_حضور", description="يخصم ساعات للشخص عبر المنشن")
@app_commands.describe(user="الشخص", hours="ساعات", minutes="دقائق", seconds="ثواني")
async def sub_hours(interaction: discord.Interaction, user: discord.Member, hours: int = 0, minutes: int = 0, seconds: int = 0):
    await interaction.response.defer(ephemeral=False)
    if ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles] and not interaction.user.guild_permissions.administrator:
        return await interaction.followup.send("❌ ليس لديك صلاحية.", ephemeral=True)
   
    total_seconds = (hours * 3600) + (minutes * 60) + seconds
    bot_data["time_adjustments"][str(user.id)] = bot_data["time_adjustments"].get(str(user.id), 0) - total_seconds
    save_data(bot_data)
    await interaction.followup.send(f"✅ تم خصم `{hours}س و {minutes}د و {seconds}ث` من {user.mention}.")

@bot.tree.command(name="إضافة_نقاط_كتيبة", description="يضيف نقاط للكتيبة في الجرد")
@app_commands.choices(squad=[
    app_commands.Choice(name="وحدة إلقاء القبض", value="unit"),
    app_commands.Choice(name="E.C.O", value="eco"),
    app_commands.Choice(name="الطيران", value="air")
])
async def add_points(interaction: discord.Interaction, squad: app_commands.Choice[str], points: int):
    await interaction.response.defer(ephemeral=False)
    if not has_squad_audit_permission(interaction): return await interaction.followup.send("❌ ليس لديك صلاحية.", ephemeral=True)
   
    bot_data["squad_points_adjustments"][squad.value] += points
    save_data(bot_data)
    await interaction.followup.send(f"✅ تم إضافة `{points}` نقطة لكتيبة {squad.name}.")

@bot.tree.command(name="خصم_نقاط_للكتائب", description="يخصم نقاط من الكتيبة في الجرد")
@app_commands.choices(squad=[
    app_commands.Choice(name="وحدة إلقاء القبض", value="unit"),
    app_commands.Choice(name="E.C.O", value="eco"),
    app_commands.Choice(name="الطيران", value="air")
])
async def sub_points(interaction: discord.Interaction, squad: app_commands.Choice[str], points: int):
    await interaction.response.defer(ephemeral=False)
    if not has_squad_audit_permission(interaction): return await interaction.followup.send("❌ ليس لديك صلاحية.", ephemeral=True)
   
    bot_data["squad_points_adjustments"][squad.value] -= points
    save_data(bot_data)
    await interaction.followup.send(f"✅ تم خصم `{points}` نقطة من كتيبة {squad.name}.")

# ==========================================
# 11. الجرد الأسبوعي للحضور
# ==========================================
@bot.tree.command(name="الجرد_الأسبوعي", description="يجرد معدل الدخول والخروج للأسبوع الماضي")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def attendance_weekly_audit(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    last_week = now - datetime.timedelta(days=7)
    users_stats = {}
    for record in attendance_history:
        if record["logout"] >= last_week:
            uid = record["user_id"]
            users_stats[uid] = users_stats.get(uid, 0) + (record["logout"] - record["login"]).total_seconds()
           
    for uid_str, adj in bot_data["time_adjustments"].items():
        uid = int(uid_str)
        if uid in users_stats: users_stats[uid] += adj
        else: users_stats[uid] = adj
           
    embed = discord.Embed(title="الجرد الأسبوعي للمحامين", color=discord.Color.dark_blue())
    if not users_stats:
        embed.description = "**لا توجد بيانات للأسبوع الماضي.**"
        return await interaction.followup.send(embed=embed)
       
    desc = ""
    for uid, seconds in sorted(users_stats.items(), key=lambda x: x[1], reverse=True):
        if seconds <= 0: continue
        member = interaction.guild.get_member(uid)
        name = member.mention if member else f"ID: {uid}"
        desc += f"{name}\nإجمالي الوقت: **{round(seconds / 3600, 2)} ساعة**\n\n"
       
    embed.description = desc
    await interaction.followup.send(embed=embed)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    msg = "**❌ حدث خطأ أو ليس لديك الصلاحية لاستخدام الأمر.**"
    try:
        if not interaction.response.is_done(): await interaction.response.send_message(msg, ephemeral=True)
        else: await interaction.followup.send(msg, ephemeral=True)
    except: pass

# ==========================================
# 12. أمر مسح الرسائل (!مسح)
# ==========================================
@bot.command(name="مسح", aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 10):
    try:
        # amount + 1 عشان يمسح رسالة الأمر نفسها مع العدد المطلوب
        deleted = await ctx.channel.purge(limit=amount + 1)
       
        # رسالة تأكيد تنحذف تلقائياً بعد 3 ثواني
        confirm_msg = await ctx.send(f"✅ **تم مسح {len(deleted)-1} رسالة بنجاح بواسطة {ctx.author.mention}.**")
        await asyncio.sleep(3)
        await confirm_msg.delete()
       
        # تسجيل الحدث في لوق الأوامر
        await send_custom_log(
            "🗑️ لوق مسح رسائل",
            f"الشخص: {ctx.author.mention}\nالروم: {ctx.channel.mention}\nالعدد: {len(deleted)-1}",
            channel_id=GENERAL_CUSTOM_LOG_ID,
            color=discord.Color.red()
        )
    except Exception as e:
        await ctx.send("❌ **حدث خطأ أثناء محاولة مسح الرسائل. تأكد من إعطاء البوت صلاحيات Manage Messages!**")

@clear_messages.error
async def clear_messages_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        msg = await ctx.send("❌ **عذراً، ما عندك صلاحية (Manage Messages) عشان تستخدم هذا الأمر!**")
        await asyncio.sleep(3)
        await msg.delete()
       
# ==========================================
# 13. نظام البنك المركزي (لوحة التحكم والتعميمات)
# ==========================================
class RemovePenaltyModal(discord.ui.Modal, title='إزالة مخالفة ورفع التعميم'):
    msg_id = discord.ui.TextInput(label='آيدي رسالة التعميم (Message ID)', style=discord.TextStyle.short)
    reason = discord.ui.TextInput(label='سبب الإزالة ولماذا؟', style=discord.TextStyle.long)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channel = interaction.guild.get_channel(1536074561567727656)
        if not channel:
            return await interaction.followup.send("❌ **لم أتمكن من إيجاد روم التعميمات!**", ephemeral=True)
        try:
            target_msg = await channel.fetch_message(int(self.msg_id.value))
            if target_msg.embeds:
                embed = target_msg.embeds[0]
                embed.color = discord.Color.green()
                embed.title = "✅ | [مُنتهية] تعميم رسمي من البنك المركزي"
                await target_msg.edit(embed=embed)
           
            reply_msg = f"**✅ تم الإنتهاء ويتم إزالة التعميم.**\n**السبب:** {self.reason.value}\n**بواسطة:** {interaction.user.mention}"
            await target_msg.reply(reply_msg)
            await interaction.followup.send("✅ **تم إزالة التعميم وتحديث الرسالة بنجاح.**", ephemeral=True)
        except Exception as e:
            await interaction.followup.send("❌ **لم أتمكن من العثور على الرسالة، تأكد من نسخ الآيدي بشكل صحيح.**", ephemeral=True)

class IssuePenaltyModal(discord.ui.Modal, title='تحرير مخالفة عدم سداد'):
    name = discord.ui.TextInput(label='الإسم ( إن وجد )', required=False)
    player_id = discord.ui.TextInput(label='الإيدي (رقم الهوية)', required=True)
    amount = discord.ui.TextInput(label='المبلغ المطلوب', required=True)
    danger = discord.ui.TextInput(label='درجة الخطورة', required=True)
    squad = discord.ui.TextInput(label='الكتيبة الموجه لها', required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        # 1. طلب ملف الـ PDF
        await interaction.response.send_message("**✅ تم حفظ البيانات. الرجاء إرسال [ملف PDF واحد فقط] هنا الآن... معك دقيقتين.**", ephemeral=True)
       
        def check_pdf(m):
            # نتحقق إن المرسل هو نفس الشخص، وإن الرسالة تحتوي على مرفق واحد، وامتداده pdf
            return m.author == interaction.user and m.channel == interaction.channel and len(m.attachments) == 1 and m.attachments[0].filename.lower().endswith('.pdf')
           
        try:
            # انتظار رسالة الـ PDF
            pdf_msg = await bot.wait_for('message', timeout=120.0, check=check_pdf)
            pdf_attachment = pdf_msg.attachments[0]
           
            # 2. طلب كلمة المرور للملف
            await interaction.followup.send("**✅ ممتاز، تم استلام ملف الـ PDF. الرجاء كتابة [كلمة المرور] الخاصة بالملف الآن كرسالة... معك دقيقة واحدة.**", ephemeral=True)
           
            def check_password(m):
                # نتحقق إن المستخدم أرسل رسالة نصية (كلمة المرور)
                return m.author == interaction.user and m.channel == interaction.channel and m.content.strip() != ""
               
            try:
                # انتظار رسالة كلمة المرور
                pass_msg = await bot.wait_for('message', timeout=60.0, check=check_password)
                password = pass_msg.content.strip()
               
                target_channel = interaction.guild.get_channel(1536074561567727656)
               
                embed = discord.Embed(
                    title="🚨 | تعميم رسمي من البنك المركزي - وزارة العدل",
                    description="**تم إصدار مذكرة ملاحقة مالية بحق المذكور أدناه لعدم سداد المستحقات المالية.**",
                    color=discord.Color.red()
                )
                embed.add_field(name="👤 الإسم", value=f"**{self.name.value or 'غير معروف'}**", inline=True)
                embed.add_field(name="💳 الإيدي", value=f"**{self.player_id.value}**", inline=True)
                embed.add_field(name="💰 المبلغ", value=f"**{self.amount.value}**", inline=False)
                embed.add_field(name="⚠️ الخطورة", value=f"**{self.danger.value}**", inline=True)
                embed.add_field(name="🚓 الكتيبة الموجهة", value=f"**{self.squad.value}**", inline=True)
                embed.add_field(name="🔒 كلمة مرور الملف", value=f"**{password}**", inline=False)
                embed.set_footer(text=f"تم الإصدار بواسطة: {interaction.user.display_name}")
                
                # قراءة الملف من الديسكورد وتحويله لملف يمكن إعادة إرساله
                file_bytes = await pdf_attachment.read()
                uploaded_pdf = discord.File(fp=io.BytesIO(file_bytes), filename=pdf_attachment.filename)
                
                # إرسال التعميم مع الملف المرفق
                await target_channel.send(content="@here **🚨 تعميم مالي جديد!**", embed=embed, file=uploaded_pdf)
               
                await interaction.followup.send("✅ **تم إصدار التعميم وإرفاق ملف الـ PDF بنجاح!**", ephemeral=True)
               
                # تنظيف الشات بمسح رسالة الـ PDF ورسالة كلمة المرور
                try:
                    await pdf_msg.delete()
                    await pass_msg.delete()
                except:
                    pass
            except asyncio.TimeoutError:
                await interaction.followup.send("❌ **انتهى الوقت ولم تقم بكتابة كلمة المرور. أعد المحاولة من جديد.**", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ **انتهى الوقت أو أنك لم تقم بإرسال ملف بصيغة PDF. أعد المحاولة من جديد.**", ephemeral=True)

class BankControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="إزالة مُخالفة", style=discord.ButtonStyle.success, custom_id="remove_penalty", emoji="✅")
    async def remove_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemovePenaltyModal())

    @discord.ui.button(label="تحرير مُخالفة", style=discord.ButtonStyle.danger, custom_id="issue_penalty", emoji="🚨")
    async def issue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(IssuePenaltyModal())

@bot.tree.command(name="إستدعاء_تحرير_المخالفات", description="إرسال لوحة التحكم الخاصة بالبنك المركزي")
async def summon_bank_panel(interaction: discord.Interaction):
    if interaction.channel.id != 1526668039620395151:
        return await interaction.response.send_message("❌ **هذا الأمر مخصص لروم البنك فقط!**", ephemeral=True)
   
    embed = discord.Embed(
        title="🏦 | لوحة التحكم [ البنك المركزي - وزارة العدل ]",
        description="**استخدم الأزرار أدناه لإصدار أو إزالة التعميمات المالية الخاصة بالمطلوبين.**\nملاحظة: هذه اللوحة تعمل فقط للموظفين المعتمدين.",
        color=discord.Color.dark_theme()
    )
    embed.set_image(url="https://palsawa.com/uploads/images/2022/10/z43kV.jpg")
   
    await interaction.channel.send(embed=embed, view=BankControlPanel())
    await interaction.response.send_message("✅ **تم استدعاء اللوحة بنجاح.**", ephemeral=True)

# ==========================================
# 14. آمر ! id
# ==========================================

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
        await ctx.send(f"❌ لم يتم العثور على أي شخص بهذا الإيدي: `{name}`")

# ==========================================
# 15. منشن
# ==========================================

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
    if not has_single_role(interaction, MENTIONS_COUNT_ALLOWED_ROLE):
        await interaction.response.send_message("❌ ليس لديك الصلاحية لاستخدام هذا الأمر.", ephemeral=True)
        return

    try:
        start_date = datetime.datetime(start_year, start_month, start_day, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end_date = datetime.datetime(end_year, end_month, end_day, 23, 59, 59, tzinfo=datetime.timezone.utc)
    except ValueError:
        await interaction.response.send_message("❌ التاريخ الذي أدخلته غير صحيح!", ephemeral=True)
        return

    await interaction.response.send_message(f"⏳ جاري حساب المنشنات من `{start_day}/{start_month}/{start_year}` إلى `{end_day}/{end_month}/{end_year}`...", ephemeral=True)
    stats = {}

    async for msg in interaction.channel.history(after=start_date, before=end_date, limit=None):
        if msg.mentions and not msg.author.bot:
            stats[msg.author.id] = stats.get(msg.author.id, 0) + len(msg.mentions)

    report_title = f"منشنات قناة #{interaction.channel.name} ({start_day}/{start_month} - {end_day}/{end_month})"
    embed_result = format_report_as_embed(report_title, stats, interaction.guild, "منشن", discord.Color.orange())
    await interaction.edit_original_response(content=None, embed=embed_result)

# ==========================================
# 16. رسائل
# ==========================================

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
    if not has_single_role(interaction, MENTIONS_COUNT_ALLOWED_ROLE):
        await interaction.response.send_message("❌ ليس لديك الصلاحية لاستخدام هذا الأمر.", ephemeral=True)
        return

    try:
        start_date = datetime.datetime(start_year, start_month, start_day, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end_date = datetime.datetime(end_year, end_month, end_day, 23, 59, 59, tzinfo=datetime.timezone.utc)
    except ValueError:
        await interaction.response.send_message("❌ التاريخ الذي أدخلته غير صحيح!", ephemeral=True)
        return

    await interaction.response.send_message(f"⏳ جاري حساب الرسائل من `{start_day}/{start_month}/{start_year}` إلى `{end_day}/{end_month}/{end_year}`...", ephemeral=True)
    stats = {}

    async for msg in interaction.channel.history(after=start_date, before=end_date, limit=None):
        if not msg.author.bot:
            stats[msg.author.id] = stats.get(msg.author.id, 0) + 1

    report_title = f"رسائل قناة #{interaction.channel.name} ({start_day}/{start_month} - {end_day}/{end_month})"
    embed_result = format_report_as_embed(report_title, stats, interaction.guild, "رسالة", discord.Color.green())
    await interaction.edit_original_response(content=None, embed=embed_result)

# ==========================================
# 16. ضباط
 # ==========================================
@bot.tree.command(name="check_officers", description="جرد نقاط الضباط")
async def check_officers(interaction: discord.Interaction):
    if not has_role(interaction, OFFICERS_ALLOWED_ROLES):
        await interaction.response.send_message("❌ ليس لديك الصلاحية لاستخدام هذا الأمر.", ephemeral=True)
        return

    if interaction.channel_id != OFFICERS_AUDIT_CHANNEL_ID:
        await interaction.response.send_message(f"❌ يمكنك استخدام هذا الأمر فقط داخل الروم المخصصة: <#{OFFICERS_AUDIT_CHANNEL_ID}>", ephemeral=True)
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


# ==========================================
# 🚀 تشغيل السيرفر والبوت
# ==========================================
bot.run(os.getenv('TOKEN'))

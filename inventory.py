import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import datetime
import asyncio
import requests
import json
import random
import io
import logging
from pathlib import Path
from flask import Flask
from threading import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("justice_discord_bot")

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
intents = discord.Intents.none()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True
intents.presences = True
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
MAX_PDF_BYTES = 8 * 1024 * 1024

active_sessions = {}
offline_timers = {}
attendance_history = []
channel_previous_permissions = {}

# ==========================================
# 5. دوال حفظ البيانات
# ==========================================
DATA_FILE = Path(__file__).with_name("bot_data.json")


def default_bot_data():
    return {
        "weekly_audit": 1,
        "monthly_audit": 1,
        "time_adjustments": {},
        "squad_points_adjustments": {"unit": 0, "eco": 0, "air": 0},
        "active_sessions": {},
        "attendance_history": [],
        "channel_previous_permissions": {},
    }


def load_data():
    data = default_bot_data()
    if not DATA_FILE.exists():
        return data

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            loaded = json.load(file)
    except (OSError, json.JSONDecodeError):
        logger.exception("Could not load %s; starting with safe defaults.", DATA_FILE)
        return data

    if not isinstance(loaded, dict):
        logger.warning("Ignoring invalid data in %s.", DATA_FILE)
        return data

    for counter in ("weekly_audit", "monthly_audit"):
        if isinstance(loaded.get(counter), int) and loaded[counter] >= 1:
            data[counter] = loaded[counter]

    if isinstance(loaded.get("time_adjustments"), dict):
        migrated_adjustments = {}
        migration_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for user_id, raw_adjustments in loaded["time_adjustments"].items():
            if isinstance(raw_adjustments, (int, float)):
                # Compatibility with the old format; retain it for the next weekly audit only.
                migrated_adjustments[str(user_id)] = [{"seconds": raw_adjustments, "created_at": migration_time}]
            elif isinstance(raw_adjustments, list):
                migrated_adjustments[str(user_id)] = [
                    adjustment
                    for adjustment in raw_adjustments
                    if (
                        isinstance(adjustment, dict)
                        and isinstance(adjustment.get("seconds"), (int, float))
                        and isinstance(adjustment.get("created_at"), str)
                    )
                ]
        data["time_adjustments"] = migrated_adjustments

    if isinstance(loaded.get("squad_points_adjustments"), dict):
        for squad in data["squad_points_adjustments"]:
            points = loaded["squad_points_adjustments"].get(squad)
            if isinstance(points, (int, float)):
                data["squad_points_adjustments"][squad] = points

    if isinstance(loaded.get("active_sessions"), dict):
        data["active_sessions"] = loaded["active_sessions"]
    if isinstance(loaded.get("attendance_history"), list):
        data["attendance_history"] = loaded["attendance_history"]
    if isinstance(loaded.get("channel_previous_permissions"), dict):
        data["channel_previous_permissions"] = loaded["channel_previous_permissions"]
    return data

def save_data(data):
    data["active_sessions"] = {
        str(user_id): login_time.isoformat()
        for user_id, login_time in active_sessions.items()
    }
    data["attendance_history"] = [
        {
            "user_id": record["user_id"],
            "login": record["login"].isoformat(),
            "logout": record["logout"].isoformat(),
        }
        for record in attendance_history
    ]
    data["channel_previous_permissions"] = channel_previous_permissions

    temporary_file = DATA_FILE.with_suffix(".tmp")
    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        temporary_file.replace(DATA_FILE)
    except OSError:
        logger.exception("Could not save %s.", DATA_FILE)

bot_data = load_data()


def parse_timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        timestamp = datetime.datetime.fromisoformat(value)
    except ValueError:
        return None
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=datetime.timezone.utc)
    return timestamp.astimezone(datetime.timezone.utc)


for stored_user_id, stored_login_time in bot_data["active_sessions"].items():
    try:
        user_id = int(stored_user_id)
    except (TypeError, ValueError):
        continue
    login_time = parse_timestamp(stored_login_time)
    if login_time:
        active_sessions[user_id] = login_time

for stored_record in bot_data["attendance_history"]:
    if not isinstance(stored_record, dict):
        continue
    try:
        user_id = int(stored_record["user_id"])
    except (KeyError, TypeError, ValueError):
        continue
    login_time = parse_timestamp(stored_record.get("login"))
    logout_time = parse_timestamp(stored_record.get("logout"))
    if login_time and logout_time and logout_time >= login_time:
        attendance_history.append({"user_id": user_id, "login": login_time, "logout": logout_time})

channel_previous_permissions = bot_data["channel_previous_permissions"]
views_registered = False
commands_synced = False

# ==========================================
# 6. دوال مساعدة عامة
# ==========================================
def has_squad_audit_permission(interaction: discord.Interaction) -> bool:
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        return False
    if interaction.user.guild_permissions.administrator: return True
    return any(role_id in [role.id for role in interaction.user.roles] for role_id in SQUAD_AUDIT_ROLES)


def is_administrator(interaction: discord.Interaction) -> bool:
    return (
        interaction.guild is not None
        and isinstance(interaction.user, discord.Member)
        and interaction.user.guild_permissions.administrator
    )


async def require_administrator(interaction: discord.Interaction) -> bool:
    if is_administrator(interaction):
        return True

    message = "❌ هذه العملية متاحة فقط لمن يمتلك صلاحية Administrator."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)
    return False

def get_leaders_signatures(guild: discord.Guild) -> str:
    role = guild.get_role(1535725186957971458)
    if not role or not role.members: return "**لا يوجد مسؤولين بهذه الرتبة حالياً**"
    members = role.members
    sig_text = ""
    if len(members) >= 1: sig_text += f"الرتبة الأولى وهي مسؤول الكتائب اسمها\n{members[0].mention}\n\n"
    if len(members) >= 2: sig_text += f"الرتبة الثانية نائب مسؤول الكتائب\n{members[1].mention}\n"
    return sig_text


async def assign_winner_role(guild: discord.Guild, role_id: int, leader_ids: list[int]):
    """Keep a winner role exclusive to the leaders of the current winner."""
    winner_role = guild.get_role(role_id)
    if winner_role is None:
        logger.warning("Winner role %s was not found in guild %s.", role_id, guild.id)
        return

    for member in list(winner_role.members):
        if member.id not in leader_ids:
            try:
                await member.remove_roles(winner_role, reason="Winner role reassigned")
            except discord.DiscordException:
                logger.exception("Could not remove winner role from member %s.", member.id)

    for leader_id in leader_ids:
        member = guild.get_member(leader_id)
        if member and winner_role not in member.roles:
            try:
                await member.add_roles(winner_role, reason="Current audit winner")
            except discord.DiscordException:
                logger.exception("Could not grant winner role to member %s.", leader_id)


def reset_squad_point_adjustments():
    bot_data["squad_points_adjustments"] = {squad: 0 for squad in SQUADS_DATA}


def valid_duration(hours: int, minutes: int, seconds: int) -> bool:
    return hours >= 0 and 0 <= minutes < 60 and 0 <= seconds < 60 and (hours + minutes + seconds) > 0


def record_time_adjustment(user_id: int, seconds: int):
    adjustments = bot_data["time_adjustments"].setdefault(str(user_id), [])
    adjustments.append(
        {
            "seconds": seconds,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
    )

async def send_custom_log(title: str, description: str, color=discord.Color.blue(), channel_id=GENERAL_CUSTOM_LOG_ID):
    try:
        log_channel = bot.get_channel(channel_id)
        if log_channel:
            embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
            await log_channel.send(embed=embed)
    except discord.DiscordException:
        logger.exception("Could not send log message to channel %s.", channel_id)

async def sync_user_data(main_member: discord.Member, sec_member: discord.Member):
    changes = []
    try:
        target_nick = main_member.display_name
        if sec_member.display_name != target_nick:
            await sec_member.edit(nick=target_nick)
            changes.append(f"تغيير اللقب إلى: `{target_nick}`")
    except discord.DiscordException:
        logger.exception("Could not sync nickname for member %s.", sec_member.id)
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
    except discord.DiscordException:
        logger.exception("Could not sync roles for member %s.", sec_member.id)

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
    try:
        await asyncio.to_thread(requests.get, "https://al3dl-bot-test.onrender.com", timeout=5)
    except requests.RequestException:
        logger.warning("Keep-alive request failed.")

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
                    active_sessions.pop(user_id, None)
                    offline_timers.pop(user_id, None)
                    attendance_history.append({"user_id": user_id, "login": login_time, "logout": now})
                    save_data(bot_data)
                    try:
                        await member.send("**⚠️ تم تسجيل خروجك تلقائياً لمرور 10 دقائق أوفلاين.**")
                    except discord.Forbidden:
                        pass
        else:
            offline_timers.pop(user_id, None)

@check_offline_status.before_loop
async def before_check():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    global views_registered, commands_synced
    if not views_registered:
        bot.add_view(ApplicationMenuView())
        bot.add_view(BankControlPanel())
        views_registered = True

    if not commands_synced:
        try:
            await bot.tree.sync()
            commands_synced = True
        except discord.HTTPException:
            logger.exception("Could not sync application commands.")

    if not keep_alive_task.is_running():
        keep_alive_task.start()
    if not check_offline_status.is_running():
        check_offline_status.start()
    print(f"✅ تم تشغيل البوت بنجاح: {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or message.guild is None:
        return
    
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
        previous_permissions = {}

        def remember_permission(target, target_type):
            key = f"{target_type}:{target.id}"
            previous_permissions[key] = {
                "type": target_type,
                "id": target.id,
                "send_messages": channel.overwrites_for(target).send_messages,
            }

        remember_permission(default_role, "role")
        for target in channel.overwrites:
            if target.id == default_role.id:
                continue
            if isinstance(target, discord.Role):
                remember_permission(target, "role")
            elif isinstance(target, discord.Member):
                remember_permission(target, "member")

        # Keep an exact, persistent snapshot so a restart cannot leave the channel locked.
        channel_previous_permissions[str(channel.id)] = previous_permissions
        save_data(bot_data)

        for permission_state in previous_permissions.values():
            target = (
                guild.get_role(permission_state["id"])
                if permission_state["type"] == "role"
                else guild.get_member(permission_state["id"])
            )
            if target is not None:
                overwrite = channel.overwrites_for(target)
                overwrite.send_messages = False
                await channel.set_permissions(target, overwrite=overwrite)

        await channel.send("**🔒 تم إغلاق الروم وحفظ صلاحياته السابقة لاستعادتها لاحقاً.**")

    if message.content.strip() == "$أفتح_عليهم_الروم_يامدير":
        if not message.author.guild_permissions.administrator: return
        await message.delete()
        guild, channel = message.guild, message.channel
        previous_permissions = channel_previous_permissions.pop(str(channel.id), None)
        if not isinstance(previous_permissions, dict):
            return await channel.send("**❌ لا توجد صلاحيات محفوظة لهذا الروم، لذلك لم أغيّر أي صلاحية.**")

        for permission_state in previous_permissions.values():
            target = (
                guild.get_role(permission_state.get("id"))
                if permission_state.get("type") == "role"
                else guild.get_member(permission_state.get("id"))
            )
            if target is None:
                continue
            overwrite = channel.overwrites_for(target)
            previous_value = permission_state.get("send_messages")
            overwrite.send_messages = previous_value if previous_value in (True, False, None) else None
            await channel.set_permissions(target, overwrite=overwrite)

        save_data(bot_data)
        await channel.send("**🔓 تم فتح الروم ورجعت الصلاحيات.**")

    if message.channel.id == ATTENDANCE_CHANNEL_ID:
        now = datetime.datetime.now(datetime.timezone.utc)
        if message.content.strip() == '-د':
            if message.author.id in active_sessions:
                await message.delete()
                return await message.channel.send(f"{message.author.mention} لديك تسجيل حضور مفتوح بالفعل.")
            active_sessions[message.author.id] = now
            offline_timers.pop(message.author.id, None)
            save_data(bot_data)
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
                offline_timers.pop(message.author.id, None)
                attendance_history.append({"user_id": message.author.id, "login": login_time, "logout": now})
                save_data(bot_data)
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
    
    await assign_winner_role(interaction.guild, WEEKLY_WINNER_ROLE_ID, winner_info["leaders"])
                
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
    reset_squad_point_adjustments()
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
    
    await assign_winner_role(interaction.guild, MONTHLY_WINNER_ROLE_ID, winner_info["leaders"])
                
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
    reset_squad_point_adjustments()
    save_data(bot_data)

# ==========================================
# 9. التقديم للكتائب (المنيو والمودال) - 5 خانات
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
                try:
                    await self.applicant.add_roles(r)
                except discord.DiscordException:
                    logger.exception("Could not grant application role %s to member %s.", r_id, self.applicant.id)
                
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

    # تم تصحيح الخانات لتكون 5 فقط (الحد الأقصى لديسكورد)
    name = discord.ui.TextInput(label="الإسم", required=True)
    age = discord.ui.TextInput(label="العُمر (16 فما فوق)", required=True)
    exp = discord.ui.TextInput(label="الخبرات", style=discord.TextStyle.paragraph, required=True)
    hours = discord.ui.TextInput(label="ساعات التواجد (4 فما فوق)", required=True)
    rank = discord.ui.TextInput(label="رتبتك بضباط (ضابط محكمة فما فوق)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            age_val = int(self.age.value)
        except ValueError:
            age_val = 0
        try:
            hours_val = int(self.hours.value)
        except ValueError:
            hours_val = 0
        
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
            
            try:
                await interaction.user.send(f"مُبارك قبولك المبدئي في {{ {self.unit_name} }}\n{ACCEPT_INITIAL_IMG}")
            except discord.Forbidden:
                pass

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
    if not valid_duration(hours, minutes, seconds):
        return await interaction.followup.send("❌ أدخل مدة موجبة، مع دقائق وثوانٍ بين 0 و59.", ephemeral=True)
    
    total_seconds = (hours * 3600) + (minutes * 60) + seconds
    record_time_adjustment(user.id, total_seconds)
    save_data(bot_data)
    await interaction.followup.send(f"✅ تم إضافة `{hours}س و {minutes}د و {seconds}ث` لـ {user.mention}.")

@bot.tree.command(name="خصم_ساعات_ورقة_حضور", description="يخصم ساعات للشخص عبر المنشن")
@app_commands.describe(user="الشخص", hours="ساعات", minutes="دقائق", seconds="ثواني")
async def sub_hours(interaction: discord.Interaction, user: discord.Member, hours: int = 0, minutes: int = 0, seconds: int = 0):
    await interaction.response.defer(ephemeral=False)
    if ADMIN_ROLE_ID not in [r.id for r in interaction.user.roles] and not interaction.user.guild_permissions.administrator:
        return await interaction.followup.send("❌ ليس لديك صلاحية.", ephemeral=True)
    if not valid_duration(hours, minutes, seconds):
        return await interaction.followup.send("❌ أدخل مدة موجبة، مع دقائق وثوانٍ بين 0 و59.", ephemeral=True)
    
    total_seconds = (hours * 3600) + (minutes * 60) + seconds
    record_time_adjustment(user.id, -total_seconds)
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
    if points <= 0:
        return await interaction.followup.send("❌ يجب أن تكون النقاط أكبر من صفر.", ephemeral=True)
    
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
    if points <= 0:
        return await interaction.followup.send("❌ يجب أن تكون النقاط أكبر من صفر.", ephemeral=True)
    
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
            session_start = max(record["login"], last_week)
            users_stats[uid] = users_stats.get(uid, 0) + (record["logout"] - session_start).total_seconds()

    # Include an open session up to the instant the report is requested.
    for uid, login_time in active_sessions.items():
        session_start = max(login_time, last_week)
        users_stats[uid] = users_stats.get(uid, 0) + (now - session_start).total_seconds()

    active_adjustments = {}
    for uid_str, adjustments in bot_data["time_adjustments"].items():
        try:
            uid = int(uid_str)
        except (TypeError, ValueError):
            continue
        if not isinstance(adjustments, list):
            continue
        for adjustment in adjustments:
            if not isinstance(adjustment, dict):
                continue
            created_at = parse_timestamp(adjustment.get("created_at"))
            seconds = adjustment.get("seconds")
            if created_at is None or not isinstance(seconds, (int, float)) or created_at < last_week:
                continue
            active_adjustments.setdefault(str(uid), []).append(adjustment)
            users_stats[uid] = users_stats.get(uid, 0) + seconds
    bot_data["time_adjustments"] = active_adjustments
    save_data(bot_data)

    embed = discord.Embed(title="الجرد الأسبوعي للمحامين", color=discord.Color.dark_blue())
    if not users_stats:
        embed.description = "**لا توجد بيانات للأسبوع الماضي.**"
        return await interaction.followup.send(embed=embed)

    entries = []
    for uid, seconds in sorted(users_stats.items(), key=lambda x: x[1], reverse=True):
        if seconds <= 0:
            continue
        member = interaction.guild.get_member(uid)
        name = member.mention if member else f"ID: {uid}"
        entries.append(f"{name}\nإجمالي الوقت: **{round(seconds / 3600, 2)} ساعة**\n\n")

    if not entries:
        embed.description = "**لا توجد ساعات موجبة للأسبوع الماضي.**"
        return await interaction.followup.send(embed=embed)

    pages, current_page = [], ""
    for entry in entries:
        if current_page and len(current_page) + len(entry) > 3800:
            pages.append(current_page)
            current_page = ""
        current_page += entry
    if current_page:
        pages.append(current_page)

    for index, page in enumerate(pages, start=1):
        report_embed = discord.Embed(
            title=f"الجرد الأسبوعي للمحامين ({index}/{len(pages)})",
            description=page,
            color=discord.Color.dark_blue(),
        )
        await interaction.followup.send(embed=report_embed)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    msg = "**❌ حدث خطأ أو ليس لديك الصلاحية لاستخدام الأمر.**"
    logger.error("Application command failed: %r", error)
    try:
        if not interaction.response.is_done(): await interaction.response.send_message(msg, ephemeral=True)
        else: await interaction.followup.send(msg, ephemeral=True)
    except discord.DiscordException:
        logger.exception("Could not send application-command error response.")

    # ==========================================
# أمر مسح الرسائل (!مسح)
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
    except discord.DiscordException:
        logger.exception("Could not purge messages in channel %s.", ctx.channel.id)
        await ctx.send("❌ **حدث خطأ أثناء محاولة مسح الرسائل. تأكد من إعطاء البوت صلاحيات Manage Messages!**")

@clear_messages.error
async def clear_messages_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        msg = await ctx.send("❌ **عذراً، ما عندك صلاحية (Manage Messages) عشان تستخدم هذا الأمر!**")
        await asyncio.sleep(3)
        await msg.delete()

        
# ==========================================
# 3. نظام البنك المركزي (لوحة التحكم والتعميمات)
# ==========================================
class RemovePenaltyModal(discord.ui.Modal, title='إزالة مخالفة ورفع التعميم'):
    msg_id = discord.ui.TextInput(label='آيدي رسالة التعميم (Message ID)', style=discord.TextStyle.short, max_length=30)
    reason = discord.ui.TextInput(label='سبب الإزالة ولماذا؟', style=discord.TextStyle.long, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        if not await require_administrator(interaction):
            return
        await interaction.response.defer(ephemeral=True)
        channel = interaction.guild.get_channel(1536074561567727656) 
        if not channel:
            return await interaction.followup.send("❌ **لم أتمكن من إيجاد روم التعميمات!**", ephemeral=True)

        try:
            target_msg = await channel.fetch_message(int(self.msg_id.value))
            if target_msg.author.id != bot.user.id or not target_msg.embeds:
                return await interaction.followup.send("❌ الرسالة ليست تعميماً صالحاً أرسله البوت.", ephemeral=True)

            embed = target_msg.embeds[0]
            embed.color = discord.Color.green()
            embed.title = "✅ | [مُنتهية] تعميم رسمي من البنك المركزي"
            await target_msg.edit(embed=embed)
            
            reply_msg = f"**✅ تم الإنتهاء ويتم إزالة التعميم.**\n**السبب:** {self.reason.value}\n**بواسطة:** {interaction.user.mention}"
            await target_msg.reply(reply_msg)
            await interaction.followup.send("✅ **تم إزالة التعميم وتحديث الرسالة بنجاح.**", ephemeral=True)
        except (ValueError, discord.NotFound, discord.Forbidden, discord.HTTPException):
            logger.exception("Could not close penalty notice.")
            await interaction.followup.send("❌ **لم أتمكن من العثور على الرسالة، تأكد من نسخ الآيدي بشكل صحيح.**", ephemeral=True)


class IssuePenaltyModal(discord.ui.Modal, title='تحرير مخالفة عدم سداد'):
    name = discord.ui.TextInput(label='الإسم ( إن وجد )', required=False, max_length=100)
    player_id = discord.ui.TextInput(label='الإيدي (رقم الهوية)', required=True, max_length=50)
    amount = discord.ui.TextInput(label='المبلغ المطلوب', required=True, max_length=50)
    danger = discord.ui.TextInput(label='درجة الخطورة', required=True, max_length=100)
    squad = discord.ui.TextInput(label='الكتيبة الموجه لها', required=True, max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        if not await require_administrator(interaction):
            return
        await interaction.response.send_message(
            "**✅ تم حفظ البيانات. أرسل الآن ملف PDF واحداً غير محمي بكلمة مرور خلال دقيقتين.**",
            ephemeral=True,
        )
        
        def check_pdf(m):
            if m.author != interaction.user or m.channel != interaction.channel or len(m.attachments) != 1:
                return False
            attachment = m.attachments[0]
            return (
                attachment.filename.lower().endswith(".pdf")
                and attachment.size <= MAX_PDF_BYTES
                and attachment.content_type in (None, "application/pdf")
            )
            
        try:
            pdf_msg = await bot.wait_for('message', timeout=120.0, check=check_pdf)
            pdf_attachment = pdf_msg.attachments[0]
            target_channel = interaction.guild.get_channel(1536074561567727656)
            if target_channel is None:
                return await interaction.followup.send("❌ **لم أتمكن من إيجاد روم التعميمات!**", ephemeral=True)

            embed = discord.Embed(
                title="🚨 | تعميم رسمي من البنك المركزي - وزارة العدل",
                description="**تم إصدار مذكرة ملاحقة مالية بحق المذكور أدناه لعدم سداد المستحقات المالية.**",
                color=discord.Color.red(),
            )
            embed.add_field(name="👤 الإسم", value=f"**{self.name.value or 'غير معروف'}**", inline=True)
            embed.add_field(name="💳 الإيدي", value=f"**{self.player_id.value}**", inline=True)
            embed.add_field(name="💰 المبلغ", value=f"**{self.amount.value}**", inline=False)
            embed.add_field(name="⚠️ الخطورة", value=f"**{self.danger.value}**", inline=True)
            embed.add_field(name="🚓 الكتيبة الموجهة", value=f"**{self.squad.value}**", inline=True)
            embed.set_footer(text=f"تم الإصدار بواسطة: {interaction.user.display_name}")

            file_bytes = await pdf_attachment.read()
            uploaded_pdf = discord.File(fp=io.BytesIO(file_bytes), filename=pdf_attachment.filename)
            await target_channel.send(content="@here **🚨 تعميم مالي جديد!**", embed=embed, file=uploaded_pdf)
            await interaction.followup.send("✅ **تم إصدار التعميم وإرفاق ملف الـ PDF بنجاح!**", ephemeral=True)

            try:
                await pdf_msg.delete()
            except discord.Forbidden:
                logger.warning("Could not delete the source PDF message.")

        except asyncio.TimeoutError:
            await interaction.followup.send("❌ **انتهى الوقت أو أنك لم تقم بإرسال ملف بصيغة PDF. أعد المحاولة من جديد.**", ephemeral=True)
        except discord.DiscordException:
            logger.exception("Could not issue penalty notice.")
            await interaction.followup.send("❌ **تعذر إصدار التعميم. تحقق من صلاحيات البوت وحجم الملف.**", ephemeral=True)


class BankControlPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="إزالة مُخالفة", style=discord.ButtonStyle.success, custom_id="remove_penalty", emoji="✅")
    async def remove_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await require_administrator(interaction):
            return
        await interaction.response.send_modal(RemovePenaltyModal())

    @discord.ui.button(label="تحرير مُخالفة", style=discord.ButtonStyle.danger, custom_id="issue_penalty", emoji="🚨")
    async def issue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await require_administrator(interaction):
            return
        await interaction.response.send_modal(IssuePenaltyModal())

@bot.tree.command(name="إستدعاء_تحرير_المخالفات", description="إرسال لوحة التحكم الخاصة بالبنك المركزي")
async def summon_bank_panel(interaction: discord.Interaction):
    if not await require_administrator(interaction):
        return
    if interaction.channel_id != 1526668039620395151:
        return await interaction.response.send_message("❌ **هذا الأمر مخصص لروم البنك فقط!**", ephemeral=True)
    
    embed = discord.Embed(
        title="🏦 | لوحة التحكم [ البنك المركزي - وزارة العدل ]",
        description="**استخدم الأزرار أدناه لإصدار أو إزالة التعميمات المالية الخاصة بالمطلوبين.**\nملاحظة: هذه اللوحة تعمل فقط لحاملي صلاحية Administrator.",
        color=discord.Color.dark_theme()
    )
    embed.set_image(url="https://palsawa.com/uploads/images/2022/10/z43kV.jpg")
    
    await interaction.channel.send(embed=embed, view=BankControlPanel())
    await interaction.response.send_message("✅ **تم استدعاء اللوحة بنجاح.**", ephemeral=True)


# ==========================================
# 🚀 تشغيل السيرفر والبوت
# ==========================================
if __name__ == "__main__":
    token = os.getenv("TOKEN")
    if not token:
        raise RuntimeError("TOKEN environment variable is required to run the bot.")
    bot.run(token)

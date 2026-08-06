import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import datetime
import asyncio
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
SUMMON_ALLOWED_ROLE_ID = 1527238059303899146

# رتب صلاحية جرد الكتائب + الأدمن
SQUAD_AUDIT_ROLES = [1526667439306178580, 1526957036561236141]

# قناة اللوق الإضافية لجرد الضباط والقبض
EXTRA_AUDIT_LOG_CHANNEL_ID = 1526668577971765449

# القناة المخصصة لإرسال رسائل الجرد تلقائياً
SQUAD_AUDIT_TARGET_CHANNEL_ID = 1526668237809520710

TARGET_CHANNELS_FOR_DIVIDER = [
    1534713004271079604, 1526668612398485584, 1526668615812907129,
    1534715397570560071, 1534711951144390806, 1526668510649122947,
    1526668448673828944, 1526668350846140599, 1526668314078740621,
    1526955624255066332, 1527751172029550713, 1526668199662452767,
    1526668203546382406, 1526668224140414986, 1528548590392180846,
    1527474093694390374, 1527464432618438778, 1526668041843249233,
    1526668648041681006, 1531025442390147262, 1534729850160545942
]

LOG_SLASH_COMMANDS_CHANNEL_ID = 1526668615812907129  
LOG_SYNC_CHANNEL_ID = 1526668612398485584          
LOG_ATTENDANCE_CHANNEL_ID = 1534711951144390806    
LOG_ID_COMMAND_CHANNEL_ID = 1534715397570560071    
SUMMON_TARGET_CHANNEL_ID = 1534729850160545942
GENERAL_CUSTOM_LOG_ID = 1534943475945177338 
OFFICERS_AUDIT_CHANNEL_ID = 1526668727657955418
OFFICERS_ALLOWED_ROLES = [
    1526667489147355146, 1526667490287947776, 1526667491353301093,
    1526667492590620865, 1526667402325131414
]
UNIT_AUDIT_CHANNEL_ID = 1526668730673664010
UNIT_ALLOWED_ROLES = [
    1526667440426188890, 1526667441395208305, 1526667402325131414,
    1526667535431504064, 1526667536542863400
]
ATTENDANCE_CHANNEL_ID = 1526668199662452767

# رتب جوائز الكتائب
WEEKLY_WINNER_ROLE_ID = 1534965674840035419
MONTHLY_WINNER_ROLE_ID = 1526667494901809202

# -------------------------------- بيانات الكتائب للجرد --------------------------------
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

weekly_audit_counter = 1
monthly_audit_counter = 1

# -------------------------------------------------------------------------------------
MAIN_GUILD_ID = 1441066070461911193       
SECONDARY_GUILD_ID = 1526667305017413643  

ROLE_MAPPING = {
    1441072532219498629: 1526667652431347772,
    1441072529111519353: 1526667549956116642,
}

OFFICER_CHANNELS = {
    1526668339391365170: 2, 1526668345448075284: 2,
    1526668348262187188: 2, 1526668342444949696: 4
}

ARREST_CHANNELS = {
    1526668398719926362: 6, 1526668402947653823: 8,
    1526668405619560468: 5, 1526668409046171699: 4,
    1526668395406430308: 4
}

active_sessions = {}
offline_timers = {}
attendance_history = []
event_data = {"is_active": False, "start_time": None}

IMAGE_URL = "https://media.discordapp.net/attachments/1151101245537386609/1472578282963865670/Screenshot_7.png?ex=6a748565&is=6a7333e5&hm=cbe205704e37d40df6e535912e57cb27353d9305f879b2efd12961d384bac3b0&=&format=webp&quality=lossless&width=1280&height=281"
DIVIDER_GIF_URL = "https://media.discordapp.net/attachments/1522904957391474759/1534717039459962950/49c865eae934de94.gif?ex=6a75241f&is=6a73d29f&hm=07f1d554361b2b891e6a4b4ed47f260cd92fbdc34cb7b811cc887e59f0928b18&="
SUMMON_IMAGE_URL = "https://images-ext-1.discordapp.net/external/y3hEPg39bmEeuUek4RN-j8j_XJCBrsaR6brBlfecBNs/https/i.ibb.co/gZyrTbZ1/1144444444.gif"

def has_summon_permission(interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator:
        return True
    user_role_ids = [role.id for role in interaction.user.roles]
    return SUMMON_ALLOWED_ROLE_ID in user_role_ids

def has_squad_audit_permission(interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator:
        return True
    user_role_ids = [role.id for role in interaction.user.roles]
    return any(role_id in user_role_ids for role_id in SQUAD_AUDIT_ROLES)

def get_role_members_mentions(guild: discord.Guild, role_id: int) -> str:
    role = guild.get_role(role_id)
    if role and role.members:
        return " ".join([m.mention for m in role.members])
    return "لا يوجد"

async def send_custom_log(title: str, description: str, color=discord.Color.blue()):
    try:
        log_channel = bot.get_channel(GENERAL_CUSTOM_LOG_ID)
        if log_channel:
            embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
            await log_channel.send(embed=embed)
    except Exception as e:
        print(f"❌ خطأ في إرسال لوق الأوامر الخاصة: {e}")

async def send_slash_log(interaction: discord.Interaction, result_text: str, is_success: bool = True):
    try:
        log_channel = bot.get_channel(LOG_SLASH_COMMANDS_CHANNEL_ID)
        if log_channel:
            color = discord.Color.green() if is_success else discord.Color.red()
            status_title = "✅ تنفيذ أمر سلاش بنجاح" if is_success else "⚠️ فشل أو رفض أمر سلاش"
            embed = discord.Embed(title=status_title, color=color, timestamp=datetime.datetime.now(datetime.timezone.utc))
            embed.add_field(name="العضو", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
            cmd_name = interaction.command.name if interaction.command else 'Unknown'
            embed.add_field(name="الأمر", value=f"/{cmd_name}", inline=True)
            embed.add_field(name="الروم", value=f"{interaction.channel.mention if interaction.channel else 'Unknown'}", inline=True)
            embed.add_field(name="الرد / النتيجة الصادرة", value=f"```{result_text[:1000]}```", inline=False)
            await log_channel.send(embed=embed)
    except Exception as e:
        print(f"❌ خطأ في إرسال لوق أوامر السلاش: {e}")

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
    except Exception as e:
        print(f"❌ تعذر تحديث رتب العضو {sec_member}: {e}")

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if after.guild.id != MAIN_GUILD_ID:
        return
    sec_guild = bot.get_guild(SECONDARY_GUILD_ID)
    if sec_guild:
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

@tasks.loop(seconds=30)
async def check_offline_status():
    now = datetime.datetime.now(datetime.timezone.utc)
    for user_id, login_time in list(active_sessions.items()):
        guild = bot.get_guild(MAIN_GUILD_ID)
        if not guild:
            continue
        member = guild.get_member(user_id)
        if not member:
            continue
        is_offline = member.status in (discord.Status.offline, discord.Status.invisible)
        if is_offline:
            if user_id not in offline_timers:
                offline_timers[user_id] = now
            else:
                elapsed_seconds = (now - offline_timers[user_id]).total_seconds()
                if elapsed_seconds >= 600:
                    del active_sessions[user_id]
                    del offline_timers[user_id]
                    attendance_history.append({"user_id": user_id, "login": login_time, "logout": now})
                    try:
                        await member.send("⚠️ تم تسجيل خروجك تلقائياً من النظام بسبب بقائك في وضع (Offline) لأكثر من 10 دقائق.")
                    except Exception:
                        pass

@check_offline_status.before_loop
async def before_check():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    await bot.tree.sync()
    keep_alive_task.start()
    check_offline_status.start()
    print(f"✅ تم تشغيل البوت بنجاح: {bot.user}")

summon_wizard_sessions = {}
channel_previous_permissions = {}

@bot.event
async def on_message(message: discord.Message):
    if message.channel.id in TARGET_CHANNELS_FOR_DIVIDER:
        if message.content != DIVIDER_GIF_URL:
            if message.channel.id != ATTENDANCE_CHANNEL_ID:
                await message.channel.send(DIVIDER_GIF_URL)
    if message.author.bot:
        return

    # معالجة أمر قفل الروم ($سكر_عليهم_الروم_يامدير)
    if message.content.strip() == "$سكر_عليهم_الروم_يامدير":
        if not message.author.guild_permissions.administrator:
            await message.reply("❌ عذراً، هذا الأمر مخصص فقط لمن يمتلك صلاحية الأدمنستريتور (Administrator).", delete_after=5)
            return
        
        try:
            await message.delete()
            guild = message.guild
            channel = message.channel
            default_role = guild.default_role
            allowed_roles_list = []
            overwrite_dict = channel.overwrites
            current_everyone_overwrite = channel.overwrites_for(default_role)
            current_everyone_overwrite.send_messages = False
            await channel.set_permissions(default_role, overwrite=current_everyone_overwrite)
            for target, overwrite in overwrite_dict.items():
                if isinstance(target, discord.Role) and target.id != default_role.id:
                    if overwrite.send_messages is True or (overwrite.send_messages is None and target.permissions.send_messages):
                        allowed_roles_list.append(target)
                        new_ov = channel.overwrites_for(target)
                        new_ov.send_messages = False
                        await channel.set_permissions(target, overwrite=new_ov)
            channel_previous_permissions[channel.id] = allowed_roles_list
            roles_mention_str = " ".join([r.mention for r in allowed_roles_list]) if allowed_roles_list else "لا توجد رتب محددة"
            
            await channel.send(
                "🔒 **تم إغلاق الروم:**\n\n"
                "لا تتعب نفسك أتركه علي.\n\n"
                f"📌 **الرتب التي تم إغلاق الروم عليها وصلاحياتها:**\n{roles_mention_str}"
            )
            await send_custom_log(
                title="🔒 إجراء قفل روم إداري",
                description=f"👤 **المسؤول:** {message.author.mention} (`{message.author.id}`)\n\n"
                            f"📍 **الروم:** {channel.mention} (`{channel.id}`)\n\n"
                            f"🛡️ **الرتب التي أُغلقت عليها:**\n{roles_mention_str}",
                color=discord.Color.dark_red()
            )
        except Exception as e:
            print(f"خطأ في أمر القفل: {e}")
        return

    # معالجة أمر فتح الروم ($أفتح_عليهم_الروم_يامدير)
    if message.content.strip() == "$أفتح_عليهم_الروم_يامدير":
        if not message.author.guild_permissions.administrator:
            await message.reply("❌ عذراً، هذا الأمر مخصص فقط لمن يمتلك صلاحية الأدمنستريتور (Administrator).", delete_after=5)
            return
        
        try:
            await message.delete()
            guild = message.guild
            channel = message.channel
            default_role = guild.default_role
            current_everyone_overwrite = channel.overwrites_for(default_role)
            current_everyone_overwrite.send_messages = None
            await channel.set_permissions(default_role, overwrite=current_everyone_overwrite)
            previously_allowed = channel_previous_permissions.get(channel.id, [])
            for role in previously_allowed:
                ov = channel.overwrites_for(role)
                ov.send_messages = True
                await channel.set_permissions(role, overwrite=ov)
            await channel.send(
                "🔓 **تنبيه إداري رسمي:**\n\n"
                "تم فتح هذه الروم وإعادة الصلاحيات للأشخاص والرتب التي تم إغلاق الروم عليهم مسبقاً. يمكنكم بدء الكتابة الآن."
            )
            await send_custom_log(
                title="🔓 إجراء فتح روم إداري",
                description=f"👤 **المسؤول:** {message.author.mention} (`{message.author.id}`)\n\n"
                            f"📍 **الروم:** {channel.mention} (`{channel.id}`)",
                color=discord.Color.green()
            )
        except Exception as e:
            print(f"خطأ في أمر الفتح: {e}")
        return

    # معالجة أمر مسح الرسائل (!مسح الرسائل أو !مسح_الرسائل)
    if message.content.strip().startswith("!مسح الرسائل") or message.content.strip().startswith("!مسح_الرسائل"):
        if not message.author.guild_permissions.administrator:
            await message.reply("❌ عذراً، هذا الأمر مخصص فقط للمشرفين والأدمنستريتور.", delete_after=5)
            return
        
        parts = message.content.strip().split()
        if len(parts) > 2:
            try:
                amount = int(parts[2])
                if 1 <= amount <= 300:
                    await message.delete()
                    deleted = await message.channel.purge(limit=amount)
                    
                    await send_custom_log(
                        title="🧹 عملية مسح رسائل",
                        description=f"👤 **المسؤول:** {message.author.mention} (`{message.author.id}`)\n\n"
                                    f"📍 **الروم:** {message.channel.mention} (`{message.channel.id}`)\n\n"
                                    f"🗑️ **عدد الرسائل المحذوفة:** `{len(deleted)}` رسالة",
                        color=discord.Color.orange()
                    )
                    return
            except ValueError:
                pass
        await message.reply("❌ يرجى كتابة الرقم بشكل صحيح بين 1 إلى 300، هكذا: `!مسح الرسائل 50`", delete_after=5)
        return

    if message.author.id in summon_wizard_sessions:
        session = summon_wizard_sessions[message.author.id]
        step = session["step"]
        content = message.content.strip()
        if step == 1:
            session["target_user_id"] = content
            session["step"] = 2
            await message.channel.send("✅ تم حفظ أيدي الشخص. الآن أرسل **سبب الاستدعاء**:")
            return
        elif step == 2:
            session["reason"] = content
            session["step"] = 3
            await message.channel.send("✅ تم حفظ السبب. الآن أرسل **أيدي المسؤول (أيدي الخاص بك)**:")
            return
        elif step == 3:
            session["officer_id"] = content
            session["step"] = 4
            await message.channel.send("✅ تم حفظ أيدي المسؤول. الآن أرسل **مكان الحضور (رابط الروم / الاجتماع)**:")
            return
        elif step == 4:
            session["meeting_link"] = content
            session["step"] = 5
            await message.channel.send("✅ تم حفظ الرابط. الآن أرسل **أيدي رتبة المسؤول (Role ID)**:")
            return
        elif step == 5:
            session["officer_role_id"] = content
            session["step"] = 6
            await message.channel.send("✅ تم حفظ رتبة المسؤول. الآن أرسل **أيدي رتبة المستدعَى (Role ID)**:")
            return
        elif step == 6:
            session["summoned_role_id"] = content
            session["step"] = 7
            
            view = SummonChoiceView(session, message.author)
            await message.channel.send("📌 **اختر الآن هل يشمل الاستدعاء إيقاف الصلاحيات؟**", view=view)
            return

    if message.channel.id == ATTENDANCE_CHANNEL_ID:
        now = datetime.datetime.now(datetime.timezone.utc)
        if message.content.strip() == '-د':
            active_sessions[message.author.id] = now
            if message.author.id in offline_timers:
                del offline_timers[message.author.id]
            embed = discord.Embed(title="تسجيل", color=0x00ff00)
            embed.description = f"المحامي : {message.author.mention}\n\nسجل دخول\n\nحياك الله"
            embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
            embed.set_image(url=IMAGE_URL) 
            embed.set_footer(text="تسجيل الدخول د\nتسجيل الخروج خ")
            await message.channel.send(embed=embed)
            await message.channel.send(DIVIDER_GIF_URL)
            await message.delete()
        elif message.content.strip() == '-خ':
            if message.author.id in active_sessions:
                login_time = active_sessions.pop(message.author.id)
                if message.author.id in offline_timers:
                    del offline_timers[message.author.id]
                attendance_history.append({"user_id": message.author.id, "login": login_time, "logout": now})
                embed = discord.Embed(title="تسجيل", color=0xff0000)
                embed.description = f"المحامي : {message.author.mention}\n\nسجل خروج\n\nموفق خير"
                embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
                embed.set_image(url=IMAGE_URL)
                embed.set_footer(text="تسجيل الدخول د\nتسجيل الخروج خ")
                await message.channel.send(embed=embed)
                await message.channel.send(DIVIDER_GIF_URL)
                await message.delete()

    await bot.process_commands(message)

# ----------------- أزرار خيار إيقاف الصلاحيات بتصميم رسمي ومهيب -----------------
class SummonChoiceView(discord.ui.View):
    def __init__(self, session_data, author):
        super().__init__(timeout=300)
        self.session_data = session_data
        self.author = author

    @discord.ui.button(label="إيقاف الصلاحيات (يُمنع من العمل)", style=discord.ButtonStyle.danger)
    async def yes_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ هذا ليس استدعاؤك!", ephemeral=True)
            return
        await self.finalize_summon(interaction, "محظور وموقوف من مباشرة المهام الرسمية حتى إشعار آخر.", discord.Color.dark_red())

    @discord.ui.button(label="استمرار بالعمل (بدون إيقاف)", style=discord.ButtonStyle.success)
    async def no_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ هذا ليس استدعاؤك!", ephemeral=True)
            return
        await self.finalize_summon(interaction, "مستمر في ممارسة مهامه الاعتيادية.", discord.Color.gold())

    async def finalize_summon(self, interaction: discord.Interaction, suspension_status, color):
        await interaction.response.defer(ephemeral=True)
        data = self.session_data
        target_channel = interaction.guild.get_channel(SUMMON_TARGET_CHANNEL_ID)
        if not target_channel:
            await interaction.followup.send("❌ قناة إرسال الاستدعاء غير موجودة أو خطأ في الأيدي!", ephemeral=True)
            return

        embed = discord.Embed(
            title="وزارة العدل • النيابة العامة | أخطار استدعاء رسمي",
            color=color,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        embed.description = (
            "بسم الله الرحمن الرحيم\n\n"
            "السلام عليكم ورحمة الله وبركاته،\n"
            "تحية طيبة وبعد،\n\n"
            "بناءً على الصلاحيات المخولة لنا، ولمقتضيات المصلحة العامة وسير العمل، تقرر استدعاء العضو الموضحة بياناته أدناه للمثول أمام الجهات المختصة.\n\n"
            f"العضو المستدعَى: <@{data['target_user_id']}> (`{data['target_user_id']}`)\n\n"
            f"الرتبة المعنية: <@&{data['summoned_role_id']}>\n\n"
            f"سبب الاستدعاء:\n{data['reason']}\n\n"
            f"المسؤول المُصدر للقرار: <@{data['officer_id']}> (`{data['officer_id']}`)\n\n"
            f"رتبة المسؤول التنفيذي: <@&{data['officer_role_id']}>\n\n"
            f"حالة الصلاحيات التنفيذية:\n{suspension_status}\n\n"
            f"رابط التوجه وحضور الجلسة:\n[اضغط هنا للانتقال إلى مقر الحضور والاستماع]({data['meeting_link']})"
        )
        
        embed.set_image(url=SUMMON_IMAGE_URL)
        icon_url = interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None
        embed.set_footer(text="النيابة العامة • وحدة الشؤون الإدارية والتحقيق النيابي", icon_url=icon_url)
        await target_channel.send(content="||@everyone|| ||@here||", embed=embed)
        
        if interaction.user.id in summon_wizard_sessions:
            del summon_wizard_sessions[interaction.user.id]
        await interaction.edit_original_response(content="✅ **تم إصدار البلاغ القضائي وتوثيقه وإرساله إلى القناة المخصصة بنجاح تام!**", view=None)

# ------------------------------- أوامر جرد الكتائب -------------------------------
@bot.tree.command(name="جرد_الكتائب_الأسبوعي", description="إجراء جرد الكتائب الأسبوعي وإعلان الكتيبة الفائزة وتوزيع الرتبة")
async def weekly_squad_audit(interaction: discord.Interaction):
    global weekly_audit_counter
    if not has_squad_audit_permission(interaction):
        await interaction.response.send_message("❌ عذراً، ليس لديك الصلاحية لاستخدام هذا الأمر.", ephemeral=True)
        return

    await interaction.response.send_message("✅ تم بدء جرد الكتائب الأسبوعي. سيتم إرسال البيان الأولي فوراً والبيان الختامي بعد 20 دقيقة.", ephemeral=True)
    
    target_channel = interaction.guild.get_channel(SQUAD_AUDIT_TARGET_CHANNEL_ID) or interaction.channel
    sig_mentions = get_role_members_mentions(interaction.guild, 1526957036561236141)
    
    initial_msg = (
        "| ﷽ |\n\n"
        "السلام عليكم ورحمة الله وبركاته .\n"
        "والصلاة والسلام على أشرف الأنبياء والمرسلين .\n"
        "أسعد الله أوقاتكم بكل خير .\n\n"
        "تحية طيبة أما بعد :\n\n"
        "بإسمنا نحن : <@&1526667439306178580> و <@&1526957036561236141>  \n\n\n"
        "`بيان قيادي قادم بعد قليل` \n\n\n"
        "فما يخص إعلان كتيبة الأسبوع \n\n\n"
        "سائلين الله التوفيق والسداد...\n\n\n"
        "يبلغ أمرنا هذا للجهات المختصة فور صدوره .\n\n"
        "التوقيع :\n\n"
        f"{sig_mentions}\n\n"
        "[|| @everyone || -- || @here ||]"
    )
    await target_channel.send(content=initial_msg)
    
    # الانتظار 20 دقيقة (1200 ثانية)
    await asyncio.sleep(1200)

    start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    squad_scores = {}
    for s_key, s_info in SQUADS_DATA.items():
        total_msgs = 0
        for cid in s_info["channels"]:
            ch = bot.get_channel(cid)
            if ch:
                async for msg in ch.history(after=start_date, limit=None):
                    if not msg.author.bot:
                        total_msgs += 1
        squad_scores[s_key] = total_msgs

    winner_key = max(squad_scores, key=squad_scores.get)
    winner_info = SQUADS_DATA[winner_key]
    winner_points = squad_scores[winner_key]
    
    # منح رتبة الفوز تلقائياً لقادة الكتيبة الفائزة
    winner_role_obj = interaction.guild.get_role(WEEKLY_WINNER_ROLE_ID)
    if winner_role_obj:
        for lead_id in winner_info["leaders"]:
            leader_member = interaction.guild.get_member(lead_id)
            if leader_member and winner_role_obj not in leader_member.roles:
                try:
                    await leader_member.add_roles(winner_role_obj)
                except Exception as e:
                    print(f"❌ تعذر إضافة رتبة الفوز للقائد {lead_id}: {e}")

    leaders_mentions = " و ".join([f"معالي <@&{lid}>" for lid in winner_info["leaders"]])
    current_date = datetime.datetime.now().strftime("%Y/%m/%d")

    final_msg = (
        "**| ﷽ |\n\n\n"
        f"الرقم: ({weekly_audit_counter})\n"
        f"التاريخ: ({current_date})\n\n"
        "السلام عليكم ورحمة الله وبركاته .\n"
        "والصلاة والسلام على أشرف الأنبياء والمرسلين .\n"
        "أسعد الله أوقاتكم بكل خير .\n\n"
        "تحية طيبة أما بعد :\n\n"
        "يسرنا نحن وبأسمنا : <@&1526667439306178580> و <@&1526957036561236141> :__:  \n\n\n"
        "الإعلان عن جرد الكتائب الأسبوعي\n\n\n"
        "بعد الإطلاع علئ جرد الكتائب كافة وأدائهم خلال الأسبوع الحالي يُقرر ما يلي:\n\n\n"
        f"تُنصب كتيبة الأسبوع وهي : <@&{winner_info['role_id']}> .\n\n"
        f"الحاصلين على رتبة : <@&{WEEKLY_WINNER_ROLE_ID}>\n\n\n"
        f"وذلك بمعدل : ({winner_points}) نقطة .\n\n\n"
        f"مع كامل الشكر لـــ ({leaders_mentions}) علئ ما قدموه خلال الأسبوع الماضي\n\n\n\n\n"
        "مُبارك لهم هذا التميز ونسأل الله لهم التوفيق والسداد في إداء مهامهم .\n\n"
        "وحظ أوفر للبقية.\n\n"
        "ويُبلَّغ أمرنا هذا إلى جميع الجهات المعنية لاعتماده والعمل بموجبه من تاريخ صدوره .\n\n"
        "والله ولي التوفيق .\n\n"
        "التوقيع :\n\n"
        f"{sig_mentions}\n\n"
        "[|| @everyone || -- || @here ||]**"
    )
    weekly_audit_counter += 1
    await target_channel.send(content=final_msg)

@bot.tree.command(name="جرد_الكتائب_الشهري", description="إجراء جرد الكتائب الشهري وإعلان كتيبة الشهر وتوزيع الرتبة")
async def monthly_squad_audit(interaction: discord.Interaction):
    global monthly_audit_counter
    if not has_squad_audit_permission(interaction):
        await interaction.response.send_message("❌ عذراً، ليس لديك الصلاحية لاستخدام هذا الأمر.", ephemeral=True)
        return

    await interaction.response.send_message("✅ تم بدء جرد الكتائب الشهري. سيتم إرسال البيان الأولي فوراً والبيان الختامي بعد 20 دقيقة.", ephemeral=True)
    
    target_channel = interaction.guild.get_channel(SQUAD_AUDIT_TARGET_CHANNEL_ID) or interaction.channel
    sig_mentions = get_role_members_mentions(interaction.guild, 1526957036561236141)
    
    initial_msg = (
        "**| ﷽ |\n\n"
        "السلام عليكم ورحمة الله وبركاته .\n"
        "والصلاة والسلام على أشرف الأنبياء والمرسلين .\n"
        "أسعد الله أوقاتكم بكل خير .\n\n"
        "تحية طيبة أما بعد :\n\n"
        "بإسمنا نحن : <@&1526667439306178580> و <@&1526957036561236141>  \n\n\n"
        "بيان قيادي قادم بعد قليل \n\n\n"
        "فما يخص إعلان كتيبة الشهر \n\n\n"
        "سائلين الله التوفيق والسداد...\n\n\n"
        "يبلغ أمرنا هذا للجهات المختصة فور صدوره .\n\n"
        "التوقيع :\n\n"
        f"{sig_mentions}\n\n"
        "[|| @everyone || -- || @here ||]**"
    )
    await target_channel.send(content=initial_msg)
    
    # الانتظار 20 دقيقة (1200 ثانية)
    await asyncio.sleep(1200)

    start_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    squad_scores = {}
    for s_key, s_info in SQUADS_DATA.items():
        total_msgs = 0
        for cid in s_info["channels"]:
            ch = bot.get_channel(cid)
            if ch:
                async for msg in ch.history(after=start_date, limit=None):
                    if not msg.author.bot:
                        total_msgs += 1
        squad_scores[s_key] = total_msgs

    winner_key = max(squad_scores, key=squad_scores.get)
    winner_info = SQUADS_DATA[winner_key]
    winner_points = squad_scores[winner_key]
    
    # منح رتبة الفوز الشهري تلقائياً لقادة الكتيبة الفائزة
    monthly_role_obj = interaction.guild.get_role(MONTHLY_WINNER_ROLE_ID)
    if monthly_role_obj:
        for lead_id in winner_info["leaders"]:
            leader_member = interaction.guild.get_member(lead_id)
            if leader_member and monthly_role_obj not in leader_member.roles:
                try:
                    await leader_member.add_roles(monthly_role_obj)
                except Exception as e:
                    print(f"❌ تعذر إضافة رتبة الفوز الشهري للقائد {lead_id}: {e}")

    leaders_mentions = " و ".join([f"معالي <@&{lid}>" for lid in winner_info["leaders"]])
    current_date = datetime.datetime.now().strftime("%Y/%m/%d")

    final_msg = (
        "**| ﷽ |\n\n\n"
        f"الرقم: ({monthly_audit_counter})\n"
        f"التاريخ: ({current_date})\n\n"
        "السلام عليكم ورحمة الله وبركاته .\n"
        "والصلاة والسلام على أشرف الأنبياء والمرسلين .\n"
        "أسعد الله أوقاتكم بكل خير .\n\n"
        "تحية طيبة أما بعد :\n\n"
        "يسرنا نحن وبأسمنا : <@&1526667439306178580> و <@&1526957036561236141> :__:  \n\n\n"
        "الإعلان عن جرد الكتائب الشهري\n\n\n"
        "بعد الإطلاع علئ جرد الكتائب كافة وأدائهم خلال الشهر الحالي يُقرر ما يلي:\n\n\n"
        f"تُنصب كتيبة الشهر وهي : <@&{winner_info['role_id']}> .\n\n"
        f"الحاصلين على رتبة : <@&{MONTHLY_WINNER_ROLE_ID}>\n\n\n"
        f"وذلك بمعدل : ({winner_points}) نقطة .\n\n\n"
        f"مع كامل الشكر لـــ ({leaders_mentions}) علئ ما قدموه خلال الشهر الماضي\n\n\n\n\n"
        "مُبارك لهم هذا التميز ونسأل الله لهم التوفيق والسداد في إداء مهامهم .\n\n"
        "وحظ أوفر للبقية.\n\n"
        "ويُبلَّغ أمرنا هذا إلى جميع الجهات المعنية لاعتماده والعمل بموجبه من تاريخ صدوره .\n\n"
        "والله ولي التوفيق .\n\n"
        "التوقيع :\n\n"
        f"{sig_mentions}\n\n"
        "[|| @everyone || -- || @here ||]**"
    )
    monthly_audit_counter += 1
    await target_channel.send(content=final_msg)

# باقي أوامر السلاش
@bot.tree.command(name="ألصقه_استدعاء", description="إصدار استدعاء رسمي عبر المحادثة التفاعلية خطوة بخطوة")
async def paste_summon(interaction: discord.Interaction):
    if not has_summon_permission(interaction):
        msg = "ليس لديك الصلاحية لاستخدام هذا الأمر."
        await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        await send_slash_log(interaction, msg, is_success=False)
        return
    summon_wizard_sessions[interaction.user.id] = {"step": 1}
    await interaction.response.send_message(
        "بدء نظام الاستدعاء القضائي الرسمي:\nالرجاء إرسال **أيدي الشخص المراد استدعاؤه (User ID)** في الرسالة القادمة:", 
        ephemeral=True
    )

class StopInvestigationModal(discord.ui.Modal, title="رفع التحقيق وإعادة الاعتبار"):
    target_user_id = discord.ui.TextInput(label="أيدي العضو المعني (User ID)", placeholder="مثال: 1521418837378072656", required=True)
    reason = discord.ui.TextInput(label="أسباب رفع الإيقاف والقرار الصادر", placeholder="اكتب التفاصيل القانونية هنا...", style=discord.TextStyle.paragraph, required=True)
    officer_id = discord.ui.TextInput(label="أيدي المسؤول (User ID)", placeholder="أيدي الخاص بك...", required=True)
    officer_role_id = discord.ui.TextInput(label="أيدي رتبة المسؤول (Role ID)", placeholder="أيدي رتبتك...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        target_channel = interaction.guild.get_channel(SUMMON_TARGET_CHANNEL_ID)
        if not target_channel:
            await interaction.followup.send("❌ قناة الاستدعاء واللوق غير موجودة!", ephemeral=True)
            return

        embed = discord.Embed(
            title="وزارة العدل・النيابة العامة | قرار رفع الإيقاف",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        embed.description = (
            "**بسم الله الرحمن الرحيم\n\n"
            "السلام عليكم ورحمة الله وبركاته،\n"
            "تحية طيبة وبعد،\n\n"
            "بناءً على مجريات التحقيق، وبعد مراجعة الحيثيات المتعلقة بالقرار السابق، تقرر رسمياً رفع الإيقاف وإعادة الاعتبار للعضو الموضحة بياناته أدناه.\n\n"
            f"العضو المعني بالقرار: <@{self.target_user_id.value.strip()}> (`{self.target_user_id.value.strip()}`)\n\n"
            f"الحيثيات والأسباب:\n{self.reason.value.strip()}\n\n"
            f"المسؤول المُصدر للقرار: <@{self.officer_id.value.strip()}> (`{self.officer_id.value.strip()}`)\n\n"
            f"رتبة المسؤول التنفيذي: <@&{self.officer_role_id.value.strip()}>\n\n"
            "الحالة النظامية:\nتم استئناف كافة الصلاحيات والعودة لممارسة مهام العمل بشكل رسمي.**"
        )
        
        embed.set_image(url=SUMMON_IMAGE_URL)
        icon_url = interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None
        embed.set_footer(text="النيابة العامة • وحدة الشؤون الإدارية والتحقيق النيابي", icon_url=icon_url)
        await target_channel.send(content="||@everyone|| ||@here||", embed=embed)
        await interaction.followup.send("✅ **تم إصدار وتوثيق قرار رفع التحقيق وإعادة العضو للعمل بنجاح!**", ephemeral=True)
        await send_slash_log(interaction, f"تم تنفيذ أمر /وقف_عنه_التحقيق للعضو ID: `{self.target_user_id.value}`", is_success=True)

@bot.tree.command(name="وقف_عنه_التحقيق", description="إيقاف التحقيق وإعادة العضو للخدمة وصلاحياته")
async def stop_investigation(interaction: discord.Interaction):
    if not has_summon_permission(interaction):
        msg = "ليس لديك الصلاحية لاستخدام هذا الأمر."
        await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        await send_slash_log(interaction, msg, is_success=False)
        return
    modal = StopInvestigationModal()
    await interaction.response.send_modal(modal)

@bot.command()
async def id(ctx, *, name: str):
    member = None
    for m in ctx.guild.members:
        if name.lower() in m.display_name.lower():
            member = m
            break
    if member:
        embed = discord.Embed(title=f"نتيجة البحث: {member.display_name}", color=discord.Color.blue())
        embed.add_field(name="الاسم الكامل", value=member.mention, inline=True)
        embed.add_field(name="User ID", value=f"`{member.id}`", inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ لم يتم العثور على أي شخص باسم: `{name}`")

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
        desc += f"`#{rank}` {name_str}\nالرصيد: **{count}** {unit_name}\n\n"
    embed.description = desc
    return embed

@bot.tree.command(name="check_officers", description="جرد نقاط الضباط")
@app_commands.checks.has_any_role(*OFFICERS_ALLOWED_ROLES)
async def check_officers(interaction: discord.Interaction):
    if interaction.channel_id != OFFICERS_AUDIT_CHANNEL_ID:
        msg = f"يمكن استخدام هذا الأمر فقط داخل الروم المخصصة: <#{OFFICERS_AUDIT_CHANNEL_ID}>"
        await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {}
    for cid, pts in OFFICER_CHANNELS.items():
        channel = bot.get_channel(cid)
        if channel:
            async for msg in channel.history(after=eight_days_ago, limit=None):
                if msg.attachments and not msg.author.bot:
                    stats[msg.author.id] = stats.get(msg.author.id, 0) + pts
                    
    embed_result = format_report_as_embed("ترتيب الضباط (حسب الصور)", stats, interaction.guild, "نقطة")
    await interaction.followup.send(embed=embed_result)
    
    # إرسال نسخة إلى قناة اللوق الإضافية
    extra_log_ch = bot.get_channel(EXTRA_AUDIT_LOG_CHANNEL_ID)
    if extra_log_ch:
        await extra_log_ch.send(embed=embed_result)

@bot.tree.command(name="check_arrests", description="جرد نقاط القبض")
@app_commands.checks.has_any_role(*UNIT_ALLOWED_ROLES)
async def check_arrests(interaction: discord.Interaction):
    if interaction.channel_id != UNIT_AUDIT_CHANNEL_ID:
        msg = f"يمكن استخدام هذا الأمر فقط داخل الروم المخصصة: <#{UNIT_AUDIT_CHANNEL_ID}>"
        await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {}
    for cid, pts in ARREST_CHANNELS.items():
        channel = bot.get_channel(cid)
        if channel:
            async for msg in channel.history(after=eight_days_ago, limit=None):
                if msg.mentions and not msg.author.bot:
                    stats[msg.author.id] = stats.get(msg.author.id, 0) + pts
                    
    embed_result = format_report_as_embed("ترتيب القبض (حسب المنشن)", stats, interaction.guild, "نقطة", discord.Color.red())
    await interaction.followup.send(embed=embed_result)
    
    # إرسال نسخة إلى قناة اللوق الإضافية
    extra_log_ch = bot.get_channel(EXTRA_AUDIT_LOG_CHANNEL_ID)
    if extra_log_ch:
        await extra_log_ch.send(embed=embed_result)

@bot.tree.command(name="mentions", description="حساب عدد المنشنات المرسلة في فترة محددة")
@app_commands.checks.has_role(MENTIONS_COUNT_ALLOWED_ROLE)
@app_commands.describe(
    start_year="سنة بداية الجرد", start_month="شهر بداية الجرد", start_day="يوم بداية الجرد",
    end_year="سنة نهاية الجرد", end_month="شهر نهاية الجرد", end_day="يوم نهاية الجرد"
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
        await interaction.response.send_message("❌ التاريخ الذي أدخلته غير صحيح!", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    stats = {}
    async for msg in interaction.channel.history(after=start_date, before=end_date, limit=None):
        if msg.mentions and not msg.author.bot:
            stats[msg.author.id] = stats.get(msg.author.id, 0) + len(msg.mentions)
    report_title = f"منشنات قناة #{interaction.channel.name} ({start_day}/{start_month} - {end_day}/{end_month})"
    embed_result = format_report_as_embed(report_title, stats, interaction.guild, "منشن", discord.Color.orange())
    await interaction.followup.send(embed=embed_result)

@bot.tree.command(name="count", description="حساب عدد الرسائل لكل شخص في فترة محددة")
@app_commands.checks.has_role(MENTIONS_COUNT_ALLOWED_ROLE)
@app_commands.describe(
    start_year="سنة بداية الجرد", start_month="شهر بداية الجرد", start_day="يوم بداية الجرد",
    end_year="سنة نهاية الجرد", end_month="شهر نهاية الجرد", end_day="يوم نهاية الجرد"
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
        await interaction.response.send_message("❌ التاريخ الذي أدخلته غير صحيح!", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    stats = {}
    async for msg in interaction.channel.history(after=start_date, before=end_date, limit=None):
        if not msg.author.bot:
            stats[msg.author.id] = stats.get(msg.author.id, 0) + 1
    report_title = f"رسائل قناة #{interaction.channel.name} ({start_day}/{start_month} - {end_day}/{end_month})"
    embed_result = format_report_as_embed(report_title, stats, interaction.guild, "رسالة", discord.Color.green())
    await interaction.followup.send(embed=embed_result)

@bot.tree.command(name="الجرد_الأسبوعي", description="يجرد معدل الدخول والخروج للأسبوع الماضي")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def weekly_audit(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    last_week = now - datetime.timedelta(days=7)
    users_stats = {}
    for record in attendance_history:
        if record["logout"] >= last_week:
            uid = record["user_id"]
            users_stats[uid] = users_stats.get(uid, 0) + (record["logout"] - record["login"]).total_seconds()
            
    embed = discord.Embed(title="الجرد الأسبوعي للمحامين", color=discord.Color.dark_blue())
    if not users_stats:
        embed.description = "لا توجد بيانات للأسبوع الماضي."
        await interaction.followup.send(embed=embed)
        return
    desc = ""
    for uid, seconds in sorted(users_stats.items(), key=lambda x: x[1], reverse=True):
        member = interaction.guild.get_member(uid)
        name = member.mention if member else f"ID: {uid}"
        desc += f"{name}\nإجمالي الوقت: **{round(seconds / 3600, 2)} ساعة**\n\n"
    embed.description = desc
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="الإحصائيات_اليومية", description="قائمة بكل شخص سجل دخول وخروج اليوم")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def daily_stats(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    embed = discord.Embed(title="إحصائيات اليوم الحالي", color=discord.Color.teal())
    desc = ""
    found = False
    
    for record in attendance_history:
        if record["login"] >= today_start or record["logout"] >= today_start:
            found = True
            member = interaction.guild.get_member(record["user_id"])
            name = member.mention if member else f"ID: {record['user_id']}"
            t_in = record["login"].strftime("%H:%M")
            t_out = record["logout"].strftime("%H:%M")
            desc += f"{name}\nالدخول: `{t_in}`\nالخروج: `{t_out}`\n\n"
            
    if not found:
        desc = "لم يقم أحد بتسجيل الدخول أو الخروج اليوم."
        
    embed.description = desc
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="قائمة_المتصدرين_الشهرية", description="أكثر الأشخاص تفاعلاً خلال آخر شهر")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def monthly_leaderboard(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    last_month = now - datetime.timedelta(days=30)
    users_stats = {}
    for record in attendance_history:
        if record["logout"] >= last_month:
            uid = record["user_id"]
            users_stats[uid] = users_stats.get(uid, 0) + (record["logout"] - record["login"]).total_seconds()
    embed = discord.Embed(title="قائمة المتصدرين الشهرية", color=discord.Color.gold())
    if not users_stats:
        embed.description = "لا توجد بيانات كافية."
        await interaction.followup.send(embed=embed)
        return
    desc = ""
    for rank, (uid, seconds) in enumerate(sorted(users_stats.items(), key=lambda x: x[1], reverse=True), 1):
        member = interaction.guild.get_member(uid)
        name = member.mention if member else f"ID: {uid}"
        desc += f"**المركز {rank}**\n{name}\n**{round(seconds / 3600, 2)} ساعة**\n\n"
    embed.description = desc
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="قائمة_المتصدرين", description="أكثر الأشخاص تفاعلاً بشكل كامل")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def all_time_leaderboard(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    users_stats = {}
    for record in attendance_history:
        uid = record["user_id"]
        users_stats[uid] = users_stats.get(uid, 0) + (record["logout"] - record["login"]).total_seconds()
    embed = discord.Embed(title="قائمة المتصدرين الشاملة", color=discord.Color.purple())
    if not users_stats:
        embed.description = "لا توجد بيانات مسجلة بعد."
        await interaction.followup.send(embed=embed)
        return
    desc = ""
    for rank, (uid, seconds) in enumerate(sorted(users_stats.items(), key=lambda x: x[1], reverse=True), 1):
        member = interaction.guild.get_member(uid)
        name = member.mention if member else f"ID: {uid}"
        desc += f"**المركز {rank}**\n{name}\n**{round(seconds / 3600, 2)} ساعة**\n\n"
    embed.description = desc
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="بدأ_فعالية", description="يبدأ احتساب الساعات لفعالية جديدة")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def start_event(interaction: discord.Interaction):
    event_data["is_active"] = True
    event_data["start_time"] = datetime.datetime.now(datetime.timezone.utc)
    embed = discord.Embed(title="تم بدء الفعالية بنجاح", description="سيتم الآن احتساب ساعات التفاعل بشكل منفصل حتى يتم إنهاء الفعالية.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="انهاء_الفعالية", description="ينهي الفعالية ويعرض قائمة المتصدرين الخاصة بها")
@app_commands.checks.has_role(ADMIN_ROLE_ID)
async def end_event(interaction: discord.Interaction):
    if not event_data["is_active"]:
        await interaction.response.send_message("⚠️ لا توجد فعالية نشطة حالياً لإنهائها.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    start_time = event_data["start_time"]
    users_stats = {}
    for record in attendance_history:
        if record["logout"] >= start_time:
            uid = record["user_id"]
            log_start = max(record["login"], start_time)
            users_stats[uid] = users_stats.get(uid, 0) + (record["logout"] - log_start).total_seconds()
    embed = discord.Embed(title="نتائج الفعالية الخاصة", color=discord.Color.magenta())
    if not users_stats:
        embed.description = "انتهت الفعالية ولم يقم أحد بتسجيل الدخول خلالها."
    else:
        desc = ""
        for rank, (uid, seconds) in enumerate(sorted(users_stats.items(), key=lambda x: x[1], reverse=True), 1):
            member = interaction.guild.get_member(uid)
            name = member.mention if member else f"ID: {uid}"
            desc += f"**المركز {rank}**\n{name}\n**{round(seconds / 3600, 2)} ساعة**\n\n"
        embed.description = desc
    event_data["is_active"] = False
    event_data["start_time"] = None
    await interaction.followup.send(embed=embed)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, (app_commands.errors.MissingRole, app_commands.errors.MissingAnyRole)):
        msg = "ليس لديك الصلاحية لاستخدام هذا الأمر."
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ {msg}", ephemeral=True)
    else:
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ حدث خطأ أثناء تنفيذ الأمر.", ephemeral=True)
        else:
            await interaction.followup.send("❌ حدث خطأ أثناء تنفيذ الأمر.", ephemeral=True)

bot.run(os.getenv('TOKEN'))

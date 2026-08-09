import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import datetime
import asyncio
import requests
import json
import random
from flask import Flask
from threading import Thread

# ==========================================
# 🌐 نظام إبقاء البوت متصلاً (لإرضاء منصة Render)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "✅ البوت يعمل بنجاح ومستقر على منصة Render!"

def run():
    # Render يحدد المنفذ (Port) تلقائياً، وإذا لم يجده يستخدم 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ==========================================
# 🤖 إعدادات البوت الأساسية
# ==========================================
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            help_command=None
        )

    async def setup_hook(self):
        # مزامنة أوامر السلاش عند تشغيل البوت
        await self.tree.sync()
        print("✅ تم تشغيل البوت ومزامنة الأوامر بنجاح، أهلاً بك يا عمر!")

bot = MyBot()

# بيانات الكتائب
SQUADS_DATA = {
    "eco": {"name": "الكتيبة الاقتصادية"},
    "air": {"name": "كتيبة الطيران"},
    "unit": {"name": "وحدة المهام الخاصة"}
}

# ==========================================
# 1. أمر مسح الرسائل (!مسح)
# ==========================================
@bot.command(name="مسح", aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 10):
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        confirm_msg = await ctx.send(f"✅ **تم مسح {len(deleted)-1} رسالة بنجاح بواسطة {ctx.author.mention}.**")
        await asyncio.sleep(3)
        await confirm_msg.delete()
    except Exception as e:
        msg = await ctx.send("❌ **حدث خطأ، تأكد من إعطاء البوت صلاحية Manage Messages!**")
        await asyncio.sleep(3)
        await msg.delete()

# ==========================================
# 2. نظام التقديمات (القبول والرفض مع الأسباب)
# ==========================================
class RejectReasonModal(discord.ui.Modal, title='سبب الرفض'):
    reason = discord.ui.TextInput(label='أدخل سبب الرفض (الأخطاء أو الشروط)', style=discord.TextStyle.long)
    
    def __init__(self, applicant, unit, is_initial):
        super().__init__()
        self.applicant = applicant
        self.unit = unit
        self.is_initial = is_initial

    async def on_submit(self, interaction: discord.Interaction):
        squad_name = SQUADS_DATA.get(self.unit, {}).get('name', 'الكتيبة')
        
        if self.is_initial:
            msg = (f"**نتأسف لعدم قبولك في كتيبة ( {squad_name} ) يُرجئ أعادة المحاولة مرة أخرئ .**\n\n"
                   f"**( يُرجئ التأكد من الشروط وهي هذه : {self.reason.value} )**\n\n"
                   f"**سائلين الله التوفيق والسداد لنا ولك**\n\n**{self.applicant.mention}**")
        else:
            msg = (f"**للأسف لم يتم قبولك في كتيبة ( {squad_name} ) يُرجئ أعادة المحاولة مرة أخرئ .**\n\n"
                   f"**( وذلك بسبب عدم أجتياز الإختبار الميداني: {self.reason.value} )**\n\n"
                   f"**حظ أوفر المرة القادمة لا تستسلم .**\n\n"
                   f"**سائلين الله التوفيق والسداد لنا ولك**\n\n**{self.applicant.mention}**")
        try:
            await self.applicant.send(msg)
            await interaction.response.send_message(f"✅ **تم إرسال الرفض لـ {self.applicant.mention}**", ephemeral=True)
        except:
            await interaction.response.send_message(f"⚠️ **عذراً، خاص العضو مقفل! الرسالة:**\n{msg}", ephemeral=True)

class AdminApplicationReviewView(discord.ui.View):
    def __init__(self, applicant: discord.Member, unit: str):
        super().__init__(timeout=None)
        self.applicant = applicant
        self.unit = unit
        self.squad_name = SQUADS_DATA.get(unit, {}).get('name', 'الكتيبة')

    @discord.ui.button(label="قبول مبدئي", style=discord.ButtonStyle.primary, custom_id="acc_init")
    async def accept_init(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = (f"**مُبارك قبولك في كتيبة {{ {self.squad_name} }} يُرجى التشييك علئ كافة رومات الكتيبة المذكورة إعلاه لفهم النظام والقوانين المعتمدة .**\n\n"
               f"**كما نُحيطك علمًا بأنَ هذا القبول يُعتبر قبول مبدئي القبول النهائي يُحدد من قبل مسؤولين الكتيبة بوقت آخر ليتم قبولك بشكل نهائي .**\n\n"
               f"**( نسأل المولى - عز وجل التوفيق والسداد لنا ولك )**\n\n**{self.applicant.mention}**")
        img_url = "https://media.discordapp.net/attachments/1526668577971765449/1535775643822727198/3.png"
        try:
            await self.applicant.send(content=msg)
            await self.applicant.send(content=img_url)
            await interaction.response.send_message(f"✅ **تم إرسال القبول المبدئي للعضو.**", ephemeral=True)
        except:
            await interaction.response.send_message(f"⚠️ **الخاص مقفل!**\n{msg}\n{img_url}", ephemeral=True)

    @discord.ui.button(label="قبول نهائي", style=discord.ButtonStyle.success, custom_id="acc_final")
    async def accept_final(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = (f"**مُبارك قبولك في كتيبة بشكل كامل {{ {self.squad_name} }} يُرجى التشييك علئ كافة رومات الكتيبة المذكورة إعلاه لفهم النظام والقوانين المعتمدة .**\n\n"
               f"**كما نُحيطك علمًا بأنَ هذا القبول لقد آتئ بسبب جهدك وأجتيازم للأختبارات المُقررة من قبل قيادة الكتيبة .**\n\n"
               f"**مُبارك لك هذا التميز وأستمر علئ ما أنت عليه يا وحش .**\n\n"
               f"**( نسأل المولى - عز وجل التوفيق والسداد لنا ولك )**\n\n**{self.applicant.mention}**")
        img_url = "https://media.discordapp.net/attachments/1526668577971765449/1535776350089252935/4.png"
        try:
            await self.applicant.send(content=msg)
            await self.applicant.send(content=img_url)
            await interaction.response.send_message(f"✅ **تم إرسال القبول النهائي للعضو.**", ephemeral=True)
        except:
            await interaction.response.send_message(f"⚠️ **الخاص مقفل!**\n{msg}\n{img_url}", ephemeral=True)

    @discord.ui.button(label="رفض مبدئي", style=discord.ButtonStyle.danger, custom_id="rej_init")
    async def reject_init(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RejectReasonModal(self.applicant, self.unit, is_initial=True))

    @discord.ui.button(label="رفض نهائي (مسؤولين)", style=discord.ButtonStyle.danger, custom_id="rej_final")
    async def reject_final(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RejectReasonModal(self.applicant, self.unit, is_initial=False))

# ==========================================
# 3. نظام البنك المركزي (لوحة التحكم والتعميمات)
# ==========================================
class RemovePenaltyModal(discord.ui.Modal, title='إزالة مخالفة ورفع التعميم'):
    msg_id = discord.ui.TextInput(label='آيدي رسالة التعميم (Message ID)', style=discord.TextStyle.short)
    reason = discord.ui.TextInput(label='سبب الإزالة ولماذا؟', style=discord.TextStyle.long)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        # تأكد من أن هذا هو آيدي روم التعميمات الصحيح
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
        await interaction.response.send_message("**✅ تم حفظ البيانات. الرجاء إرسال صور الإثبات (من 2 إلى 4 صور) في رسالة واحدة هنا الآن... معك دقيقتين.**", ephemeral=True)
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and len(m.attachments) >= 1
            
        try:
            msg = await bot.wait_for('message', timeout=120.0, check=check)
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
            embed.set_footer(text=f"تم الإصدار بواسطة: {interaction.user.display_name}")

            # الصورة الأولى كصورة رئيسية للإمبد
            if msg.attachments:
                embed.set_image(url=msg.attachments[0].url)

            await target_channel.send(content="@here **🚨 تعميم مالي جديد!**", embed=embed)
            
            # باقي الصور كرسائل ملحقة
            if len(msg.attachments) > 1:
                for attachment in msg.attachments[1:4]:
                    await target_channel.send(content=attachment.url)

            await interaction.followup.send("✅ **تم إصدار التعميم بنجاح مع الصور!**", ephemeral=True)
            try: await msg.delete() # لتنظيف الشات
            except: pass
        except asyncio.TimeoutError:
            await interaction.followup.send("❌ **انتهى الوقت ولم تقم بإرسال الصور. أعد المحاولة من جديد.**", ephemeral=True)

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
# 🚀 تشغيل السيرفر والبوت
# ==========================================
bot.run(os.getenv('TOKEN'))

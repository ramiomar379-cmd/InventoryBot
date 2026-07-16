import discord
from discord import app_commands
from discord.ext import commands
import os
import datetime

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# IDs الخاصة بك كما طلبت
CHANNELS = {
    "frind": 1526667955616743514,
    "officers": 1526668727657955418,
    "arrests": 1526668730673664010
}

ROLES = {
    "frind": 1526667395484225669,
    "officers": 1526667395484225670,
    "arrests": 1526667395484225672
}

async def get_audit_data(channel_id, role_id):
    channel = bot.get_channel(channel_id)
    eight_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=8)
    stats = {}
    
    async for msg in channel.history(after=eight_days_ago, limit=None):
        if any(role.id == role_id for role in msg.author.roles):
            stats[msg.author.id] = stats.get(msg.author.id, 0) + 1
    return stats

@bot.event
async def on_ready():
    await bot.tree.sync() # مزامنة الأوامر تلقائياً عند التشغيل
    print(f"البوت متصل: {bot.user}")

# الأوامر
@bot.tree.command(name="frind", description="جرد نشاط الفريند")
async def frind(interaction: discord.Interaction):
    await interaction.response.send_message("جاري الجرد...")
    stats = await get_audit_data(CHANNELS["frind"], ROLES["frind"])
    # [هنا نضع التنسيق المرتب الذي اتفقنا عليه]
    report = "\n".join([f"• {interaction.guild.get_member(uid).mention}: {count} رسالة" for uid, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)])
    await interaction.edit_original_response(content=f"📊 **نشاط الفريند:**\n{report}")

@bot.tree.command(name="check_officers", description="جرد نشاط الضباط")
async def check_officers(interaction: discord.Interaction):
    await interaction.response.send_message("جاري جرد الضباط...")
    stats = await get_audit_data(CHANNELS["officers"], ROLES["officers"])
    report = "\n".join([f"• {interaction.guild.get_member(uid).mention}: {count} رسالة" for uid, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)])
    await interaction.edit_original_response(content=f"📊 **نشاط الضباط:**\n{report}")

@bot.tree.command(name="check_arrests", description="جرد إلقاء القبض")
async def check_arrests(interaction: discord.Interaction):
    await interaction.response.send_message("جاري جرد إلقاء القبض...")
    stats = await get_audit_data(CHANNELS["arrests"], ROLES["arrests"])
    report = "\n".join([f"• {interaction.guild.get_member(uid).mention}: {count} رسالة" for uid, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)])
    await interaction.edit_original_response(content=f"📊 **نشاط إلقاء القبض:**\n{report}")

bot.run(os.getenv('TOKEN'))

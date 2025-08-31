import discord
from discord.ext import commands
from mcstatus import MinecraftServer
import json
import re
import asyncio
from datetime import timedelta

# Config dosyasını oku
with open("config.json", "r") as f:
    config = json.load(f)

TOKEN = config["token"]
PREFIX = config["prefix"]
MINECRAFT_IP = config["minecraft_ip"]
LOG_CHANNEL_ID = config["log_channel_id"]

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

KUFURLER = ["salak", "aptal", "siktir", "oç", "piç", "amk", "orospu", "aq"]

last_status = None

@bot.event
async def on_ready():
    print(f"✅ Bot Aktif: {bot.user}")
    bot.loop.create_task(monitor_mc_server())


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if any(re.search(rf"\b{re.escape(k)}\b", message.content.lower()) for k in KUFURLER):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, küfür yasaktır.")
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                f"⚠️ Küfür tespit edildi!\n👤 {message.author}\n📝 `{message.content}`\n📍 Kanal: {message.channel.mention}"
            )

        try:
            await message.author.timeout(duration=timedelta(minutes=5), reason="Küfür")
            await message.channel.send(f"{message.author.mention} 5 dakika susturuldu.")
        except:
            await message.channel.send("❌ Susturma başarısız. Yetki eksik olabilir.")
        return

    await bot.process_commands(message)


@bot.command()
async def mcstatus(ctx):
    try:
        server = MinecraftServer.lookup(MINECRAFT_IP)
        status = server.status()
        await ctx.send(f"🟢 Sunucu açık! 👥 {status.players.online}/{status.players.max} oyuncu")
    except:
        await ctx.send("🔴 Sunucuya ulaşılamadı. Kapalı olabilir.")


@bot.command()
async def mcinfo(ctx):
    try:
        server = MinecraftServer.lookup(MINECRAFT_IP)
        status = server.status()
        players = ", ".join(p.name for p in status.players.sample) if status.players.sample else "Bilinmiyor"

        embed = discord.Embed(title="🌍 Minecraft Sunucusu", color=discord.Color.green())
        embed.add_field(name="IP", value=MINECRAFT_IP)
        embed.add_field(name="Durum", value="🟢 Açık")
        embed.add_field(name="Oyuncular", value=f"{status.players.online}/{status.players.max}")
        embed.add_field(name="Gecikme", value=f"{round(status.latency)}ms")
        embed.add_field(name="Aktif Oyuncular", value=players)
        await ctx.send(embed=embed)
    except:
        await ctx.send("🔴 Sunucuya erişilemiyor.")


@bot.command()
async def say(ctx):
    try:
        server = MinecraftServer.lookup(MINECRAFT_IP)
        status = server.status()
        await ctx.send(f"👥 Sunucuda **{status.players.online}/{status.players.max}** oyuncu var.")
    except:
        await ctx.send("❌ Sunucuya ulaşılamadı.")


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 {amount} mesaj temizlendi.", delete_after=3)


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member} sunucudan atıldı. Sebep: {reason}")


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"⛔ {member} banlandı. Sebep: {reason}")


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member_name):
    banned_users = await ctx.guild.bans()
    for entry in banned_users:
        user = entry.user
        if f"{user.name}#{user.discriminator}" == member_name:
            await ctx.guild.unban(user)
            await ctx.send(f"✅ {member_name} yasağı kaldırıldı.")
            return
    await ctx.send("❌ Kullanıcı bulunamadı.")


async def monitor_mc_server():
    global last_status
    await bot.wait_until_ready()
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    while not bot.is_closed():
        try:
            server = MinecraftServer.lookup(MINECRAFT_IP)
            server.status()
            if last_status is False or last_status is None:
                await log_channel.send("🟢 Minecraft sunucusu **açıldı**!")
            last_status = True
        except:
            if last_status is True or last_status is None:
                await log_channel.send("🔴 Minecraft sunucusu **kapandı**!")
            last_status = False
        await asyncio.sleep(60)


bot.run(TOKEN)

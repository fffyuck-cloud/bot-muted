import discord
from discord.ext import commands
import asyncio

# ===== CẤU HÌNH =====
TOKEN = 'MTU0MzkzODIyOTQzMzAxNjUzMA.GhvIJ-.d3x0mBedbRaHZOly28bW_2h9bdCzTAU3W4a4vQ'  # 👈 THAY BẰNG TOKEN THẬT
GUILD_ID = 1536637861384687616/1542502535540113428  # 👈 THAY BẰNG SERVER ID THẬT
MUTED_ROLE_NAME = 'Muted'

# Khởi tạo bot
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} đã sẵn sàng!')

@bot.event
async def on_member_join(member):
    if member.guild.id != GUILD_ID:
        return
    
    muted_role = discord.utils.get(member.guild.roles, name=MUTED_ROLE_NAME)
    if muted_role is None:
        print(f'❌ Không tìm thấy role "{MUTED_ROLE_NAME}"!')
        return
    
    try:
        await member.add_roles(muted_role, reason="Tự động mute 50 ngày")
        print(f'🔇 Đã mute {member.name} khi vào server.')
    except Exception as e:
        print(f'❌ Lỗi: {e}')
        return
    
    # Đếm ngược 50 ngày
    await asyncio.sleep(50 * 24 * 60 * 60)  # 4,320,000 giây
    
    # Gỡ mute
    try:
        member = await member.guild.fetch_member(member.id)
        if member and muted_role in member.roles:
            await member.remove_roles(muted_role, reason="Hết 50 ngày mute")
            print(f'✅ Đã gỡ mute cho {member.name} sau 50 ngày.')
    except Exception as e:
        print(f'❌ Lỗi gỡ mute: {e}')

@bot.command()
@commands.has_permissions(administrator=True)
async def unmute(ctx, member: discord.Member):
    muted_role = discord.utils.get(ctx.guild.roles, name=MUTED_ROLE_NAME)
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f'✅ Đã gỡ mute cho {member.mention}.')
    else:
        await ctx.send(f'ℹ️ {member.mention} không bị mute.')

bot.run(MTU0MzkzODIyOTQzMzAxNjUzMA.GhvIJ-.d3x0mBedbRaHZOly28bW_2h9bdCzTAU3W4a4vQ)

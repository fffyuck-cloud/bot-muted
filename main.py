import discord
from discord.ext import commands
import asyncio
from datetime import datetime

# ===== CẤU HÌNH =====
TOKEN = 'MTU0MzkzODIyOTQzMzAxNjUzMA.GhvIJ-.d3x0mBedbRaHZOly28bW_2h9bdCzTAU3W4a4vQ'  # 👈 THAY BẰNG TOKEN THẬT
GUILD_ID = 1536637861384687616  # 👈 THAY BẰNG SERVER ID THẬT
MUTED_ROLE_NAME = 'Muted'
LOG_CHANNEL_ID = 1542502535540113428  # 👈 THAY BẰNG ID KÊNH LOG

# Danh sách kênh bị khóa (tự động mute)
locked_channels = []  # Lưu ID các kênh bị khóa

# Khởi tạo bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # Cần để đọc nội dung tin nhắn
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} đã sẵn sàng!')
    try:
        synced = await bot.tree.sync()
        print(f'✅ Đã đồng bộ {len(synced)} lệnh slash!')
    except Exception as e:
        print(f'❌ Lỗi sync lệnh: {e}')

# ===== HÀM GHI LOG =====
async def send_log(guild, action, member, duration=None, moderator=None, channel=None):
    """Gửi log vào kênh đã cấu hình"""
    channel_log = guild.get_channel(LOG_CHANNEL_ID)
    if channel_log is None:
        print(f'❌ Không tìm thấy kênh log (ID: {LOG_CHANNEL_ID})')
        return
    
    embed = discord.Embed(
        title=f'📋 {action}',
        color=discord.Color.blue() if 'MUTE' in action else discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(name='👤 Thành viên', value=member.mention, inline=True)
    embed.add_field(name='🆔 User ID', value=member.id, inline=True)
    
    if duration:
        embed.add_field(name='⏱️ Thời gian', value=duration, inline=True)
    
    if moderator:
        embed.add_field(name='🔧 Người thực hiện', value=moderator.mention, inline=True)
    
    if channel:
        embed.add_field(name='📌 Kênh', value=channel.mention, inline=True)
    
    embed.set_footer(text=f'Bot tự động | {datetime.utcnow().strftime("%H:%M:%S")}')
    
    await channel_log.send(embed=embed)

# ===== KIỂM TRA TIN NHẮN TRONG KÊNH BỊ KHÓA =====
@bot.event
async def on_message(message):
    # Bỏ qua tin nhắn của bot
    if message.author.bot:
        return
    
    # Chỉ kiểm tra trong server được cấu hình
    if message.guild is None or message.guild.id != GUILD_ID:
        await bot.process_commands(message)
        return
    
    # Kiểm tra kênh có trong danh sách bị khóa không
    if message.channel.id in locked_channels:
        muted_role = discord.utils.get(message.guild.roles, name=MUTED_ROLE_NAME)
        if muted_role is None:
            print(f'❌ Không tìm thấy role "{MUTED_ROLE_NAME}"!')
            await bot.process_commands(message)
            return
        
        # Kiểm tra xem thành viên đã bị mute chưa
        if muted_role not in message.author.roles:
            try:
                await message.author.add_roles(muted_role, reason=f"Tự động mute - Nhắn tin trong kênh {message.channel.name}")
                await message.delete()  # Xóa tin nhắn vi phạm
                
                # Gửi cảnh báo riêng tư
                try:
                    await message.author.send(f"🔇 Bạn đã bị mute vì nhắn tin trong kênh `#{message.channel.name}`. Kênh này đang bị khóa!")
                except:
                    pass
                
                # GHI LOG
                await send_log(
                    message.guild,
                    '🔇 AUTO MUTE (Kênh bị khóa)',
                    message.author,
                    'Vĩnh viễn (đến khi admin gỡ)',
                    None,
                    message.channel
                )
                
                print(f'🔇 Đã mute {message.author.name} vì nhắn tin trong kênh #{message.channel.name}')
            except Exception as e:
                print(f'❌ Lỗi mute: {e}')
    
    await bot.process_commands(message)

# ===== SỰ KIỆN THÀNH VIÊN VÀO SERVER =====
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
        
        await send_log(
            member.guild,
            '🔇 AUTO MUTE 50 NGÀY',
            member,
            '50 ngày',
            None
        )
    except Exception as e:
        print(f'❌ Lỗi cấp role: {e}')
        return
    
    # Đếm ngược 50 ngày
    await asyncio.sleep(50 * 24 * 60 * 60)
    
    try:
        member = await member.guild.fetch_member(member.id)
        if member and muted_role in member.roles:
            await member.remove_roles(muted_role, reason="Hết 50 ngày mute")
            print(f'✅ Đã gỡ mute cho {member.name} sau 50 ngày.')
            
            await send_log(
                member.guild,
                '✅ AUTO UNMUTE (Hết 50 ngày)',
                member,
                'Đã hoàn thành',
                None
            )
    except Exception as e:
        print(f'❌ Lỗi gỡ mute: {e}')

# ===== LỆNH SLASH /channel =====
@bot.tree.command(name='channel', description='Khóa/Mở khóa kênh (tự động mute người nhắn)')
async def channel(interaction: discord.Interaction, action: str):
    """
    Cách dùng: /channel lock - Khóa kênh hiện tại
               /channel unlock - Mở khóa kênh hiện tại
    """
    # Kiểm tra quyền admin
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message('❌ Bạn cần quyền **Administrator** để dùng lệnh này!', ephemeral=True)
        return
    
    global locked_channels
    channel = interaction.channel
    guild = interaction.guild
    
    if action.lower() == 'lock':
        if channel.id in locked_channels:
            await interaction.response.send_message(f'ℹ️ Kênh {channel.mention} đã bị khóa rồi!', ephemeral=True)
            return
        
        locked_channels.append(channel.id)
        
        embed = discord.Embed(
            title='🔒 ĐÃ KHÓA KÊNH',
            description=f'Kênh {channel.mention} đã bị khóa!',
            color=discord.Color.red()
        )
        embed.add_field(
            name='🚫 Quy tắc',
            value='Bất kỳ ai nhắn tin trong kênh này sẽ **tự động bị mute**!',
            inline=False
        )
        embed.add_field(
            name='🔓 Mở khóa',
            value='Dùng lệnh `/channel unlock` để mở khóa kênh',
            inline=False
        )
        embed.set_footer(text=f'Thực hiện bởi {interaction.user.name}')
        
        await interaction.response.send_message(embed=embed)
        
        # Ghi log
        await send_log(
            guild,
            '🔒 KHÓA KÊNH',
            interaction.user,
            None,
            interaction.user,
            channel
        )
        
    elif action.lower() == 'unlock':
        if channel.id not in locked_channels:
            await interaction.response.send_message(f'ℹ️ Kênh {channel.mention} không bị khóa!', ephemeral=True)
            return
        
        locked_channels.remove(channel.id)
        
        embed = discord.Embed(
            title='🔓 ĐÃ MỞ KHÓA KÊNH',
            description=f'Kênh {channel.mention} đã được mở khóa!',
            color=discord.Color.green()
        )
        embed.add_field(
            name='✅ Quy tắc mới',
            value='Mọi người có thể nhắn tin bình thường trong kênh này.',
            inline=False
        )
        embed.set_footer(text=f'Thực hiện bởi {interaction.user.name}')
        
        await interaction.response.send_message(embed=embed)
        
        # Ghi log
        await send_log(
            guild,
            '🔓 MỞ KHÓA KÊNH',
            interaction.user,
            None,
            interaction.user,
            channel
        )
    else:
        await interaction.response.send_message('❌ Hành động không hợp lệ! Dùng `lock` hoặc `unlock`', ephemeral=True)

# ===== LỆNH !channel (Text Command) =====
@bot.command()
@commands.has_permissions(administrator=True)
async def channel(ctx, action: str):
    """Khóa/Mở khóa kênh hiện tại (VD: !channel lock)"""
    global locked_channels
    
    if action.lower() == 'lock':
        if ctx.channel.id in locked_channels:
            await ctx.send(f'ℹ️ Kênh {ctx.channel.mention} đã bị khóa rồi!')
            return
        
        locked_channels.append(ctx.channel.id)
        
        embed = discord.Embed(
            title='🔒 ĐÃ KHÓA KÊNH',
            description=f'Kênh {ctx.channel.mention} đã bị khóa!',
            color=discord.Color.red()
        )
        embed.add_field(
            name='🚫 Quy tắc',
            value='Bất kỳ ai nhắn tin trong kênh này sẽ **tự động bị mute**!',
            inline=False
        )
        await ctx.send(embed=embed)
        
        await send_log(
            ctx.guild,
            '🔒 KHÓA KÊNH',
            ctx.author,
            None,
            ctx.author,
            ctx.channel
        )
        
    elif action.lower() == 'unlock':
        if ctx.channel.id not in locked_channels:
            await ctx.send(f'ℹ️ Kênh {ctx.channel.mention} không bị khóa!')
            return
        
        locked_channels.remove(ctx.channel.id)
        
        embed = discord.Embed(
            title='🔓 ĐÃ MỞ KHÓA KÊNH',
            description=f'Kênh {ctx.channel.mention} đã được mở khóa!',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        
        await send_log(
            ctx.guild,
            '🔓 MỞ KHÓA KÊNH',
            ctx.author,
            None,
            ctx.author,
            ctx.channel
        )
    else:
        await ctx.send('❌ Hành động không hợp lệ! Dùng `lock` hoặc `unlock`')

# ===== LỆNH !list_locked =====
@bot.command()
@commands.has_permissions(administrator=True)
async def list_locked(ctx):
    """Hiển thị danh sách kênh đang bị khóa"""
    if not locked_channels:
        await ctx.send('📋 Hiện không có kênh nào bị khóa.')
        return
    
    embed = discord.Embed(
        title='🔒 DANH SÁCH KÊNH BỊ KHÓA',
        color=discord.Color.red()
    )
    
    for channel_id in locked_channels:
        channel = ctx.guild.get_channel(channel_id)
        if channel:
            embed.add_field(
                name=f'📌 {channel.name}',
                value=f'ID: `{channel.id}`\nTrạng thái: 🔒 Đã khóa',
                inline=False
            )
    
    await ctx.send(embed=embed)

# ===== LỆNH !status =====
@bot.command()
async def status(ctx):
    """Kiểm tra trạng thái bot"""
    embed = discord.Embed(
        title='📊 Trạng thái Bot',
        color=discord.Color.blue()
    )
    embed.add_field(name='🤖 Tên bot', value=bot.user.name, inline=True)
    embed.add_field(name='🟢 Trạng thái', value='Đang hoạt động', inline=True)
    embed.add_field(name='📝 Kênh log', value=f'<#{LOG_CHANNEL_ID}>' if LOG_CHANNEL_ID else 'Chưa cài đặt', inline=False)
    embed.add_field(name='🔒 Số kênh bị khóa', value=len(locked_channels), inline=True)
    embed.add_field(name='👥 Số server', value=len(bot.guilds), inline=True)
    embed.add_field(name='⏱️ Ping', value=f'{round(bot.latency * 1000)}ms', inline=True)
    await ctx.send(embed=embed)

# Chạy bot
bot.run(MTU0MzkzODIyOTQzMzAxNjUzMA.GhvIJ-.d3x0mBedbRaHZOly28bW_2h9bdCzTAU3W4a4vQ)

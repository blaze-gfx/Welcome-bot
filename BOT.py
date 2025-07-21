import discord
from discord.ext import commands
from datetime import datetime
import os
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp

# Bot setup
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=(';', '/'), intents=intents, case_insensitive=True)

# Configuration storage
server_configs = {}

# Default configuration
DEFAULT_CONFIG = {
    "welcome_channel": None,
    "welcome_title": "Welcome to {server}",
    "welcome_description": "Enjoy your stay!",
    "welcome_banner": None,
    "welcome_footer": "Member #{member_count}",
    "welcome_color": 0x00ff00,
    "profile_template": {
        "title": "{server}",
        "subtitle": "GTA Roleplay Server",
        "description": "With Advanced Gang System, Business Role Play And Citizen Activities",
        "banner": None,
        "footer": "Account Created: {account_created}\nJoin Date: {join_date}",
        "color": 0x3498db
    }
}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    await bot.change_presence(activity=discord.Game(name="Welcoming new members!"))

@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    config = server_configs.get(guild_id, DEFAULT_CONFIG)
    
    if config["welcome_channel"]:
        channel = bot.get_channel(config["welcome_channel"])
        if channel:
            # Create welcome embed
            embed = discord.Embed(
                title=config["welcome_title"].format(server=member.guild.name, member=member),
                description=config["welcome_description"].format(server=member.guild.name, member=member),
                color=config["welcome_color"]
            )
            
            # Set banner if available
            if config["welcome_banner"]:
                embed.set_image(url=config["welcome_banner"])
            
            # Set footer
            embed.set_footer(text=config["welcome_footer"].format(
                server=member.guild.name,
                member=member,
                member_count=member.guild.member_count
            ))
            
            await channel.send(embed=embed)
            
            # Create and send profile card
            profile_card = await create_profile_card(member, config["profile_template"])
            if profile_card:
                await channel.send(file=profile_card)

async def create_profile_card(member, template):
    try:
        # Create blank image
        width, height = 800, 400
        background_color = (47, 49, 54)  # Discord dark theme color
        image = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(image)
        
        # Load fonts (you may need to adjust paths)
        try:
            title_font = ImageFont.truetype("arialbd.ttf", 36)
            subtitle_font = ImageFont.truetype("arial.ttf", 24)
            text_font = ImageFont.truetype("arial.ttf", 18)
        except:
            # Fallback fonts
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Draw title
        title = template["title"].format(server=member.guild.name)
        subtitle = template["subtitle"]
        draw.text((50, 30), title, font=title_font, fill=(255, 255, 255))
        draw.text((50, 80), subtitle, font=subtitle_font, fill=(200, 200, 200))
        
        # Draw description
        description = template["description"]
        draw.text((50, 130), description, font=text_font, fill=(180, 180, 180))
        
        # Member info
        draw.text((50, 200), f"Member: {member.name}", font=text_font, fill=(255, 255, 255))
        draw.text((50, 230), f"ID: {member.id}", font=text_font, fill=(255, 255, 255))
        draw.text((50, 260), f"Account Created: {member.created_at.strftime('%A, %B %d, %Y %I:%M %p')}", 
                 font=text_font, fill=(200, 200, 200))
        draw.text((50, 290), f"Join Date: {member.joined_at.strftime('%A, %B %d, %Y %I:%M %p')}", 
                 font=text_font, fill=(200, 200, 200))
        
        # Add avatar
        async with aiohttp.ClientSession() as session:
            async with session.get(str(member.avatar.url)) as resp:
                avatar_data = await resp.read()
        
        avatar = Image.open(io.BytesIO(avatar_data))
        avatar = avatar.resize((150, 150))
        
        # Create circular mask for avatar
        mask = Image.new('L', (150, 150), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, 150, 150), fill=255)
        
        # Paste avatar
        image.paste(avatar, (width - 180, 30), mask)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return discord.File(img_byte_arr, filename='profile_card.png')
    
    except Exception as e:
        print(f"Error creating profile card: {e}")
        return None

# Configuration commands
@bot.command(name='setwelcomechannel')
@commands.has_permissions(administrator=True)
async def set_welcome_channel(ctx, channel: discord.TextChannel):
    guild_id = str(ctx.guild.id)
    if guild_id not in server_configs:
        server_configs[guild_id] = DEFAULT_CONFIG.copy()
    
    server_configs[guild_id]["welcome_channel"] = channel.id
    await ctx.send(f"Welcome channel set to {channel.mention}")

@bot.command(name='setwelcometitle')
@commands.has_permissions(administrator=True)
async def set_welcome_title(ctx, *, title):
    guild_id = str(ctx.guild.id)
    if guild_id not in server_configs:
        server_configs[guild_id] = DEFAULT_CONFIG.copy()
    
    server_configs[guild_id]["welcome_title"] = title
    await ctx.send(f"Welcome title set to: {title}")

@bot.command(name='setwelcomedescription')
@commands.has_permissions(administrator=True)
async def set_welcome_description(ctx, *, description):
    guild_id = str(ctx.guild.id)
    if guild_id not in server_configs:
        server_configs[guild_id] = DEFAULT_CONFIG.copy()
    
    server_configs[guild_id]["welcome_description"] = description
    await ctx.send(f"Welcome description set to: {description}")

@bot.command(name='setwelcomebanner')
@commands.has_permissions(administrator=True)
async def set_welcome_banner(ctx, url: str):
    guild_id = str(ctx.guild.id)
    if guild_id not in server_configs:
        server_configs[guild_id] = DEFAULT_CONFIG.copy()
    
    server_configs[guild_id]["welcome_banner"] = url
    await ctx.send(f"Welcome banner set to the provided URL")

@bot.command(name='setwelcomefooter')
@commands.has_permissions(administrator=True)
async def set_welcome_footer(ctx, *, footer):
    guild_id = str(ctx.guild.id)
    if guild_id not in server_configs:
        server_configs[guild_id] = DEFAULT_CONFIG.copy()
    
    server_configs[guild_id]["welcome_footer"] = footer
    await ctx.send(f"Welcome footer set to: {footer}")

@bot.command(name='setwelcomecolor')
@commands.has_permissions(administrator=True)
async def set_welcome_color(ctx, hex_color: str):
    guild_id = str(ctx.guild.id)
    if guild_id not in server_configs:
        server_configs[guild_id] = DEFAULT_CONFIG.copy()
    
    try:
        color = int(hex_color.replace('#', ''), 16)
        server_configs[guild_id]["welcome_color"] = color
        await ctx.send(f"Welcome color set to: {hex_color}")
    except ValueError:
        await ctx.send("Invalid color format. Please use hex format (e.g., #00ff00)")

@bot.command(name='setprofiletemplate')
@commands.has_permissions(administrator=True)
async def set_profile_template(ctx, element: str, *, content: str):
    guild_id = str(ctx.guild.id)
    if guild_id not in server_configs:
        server_configs[guild_id] = DEFAULT_CONFIG.copy()
    
    valid_elements = ["title", "subtitle", "description", "banner", "footer", "color"]
    
    if element.lower() not in valid_elements:
        await ctx.send(f"Invalid element. Must be one of: {', '.join(valid_elements)}")
        return
    
    if element.lower() == "color":
        try:
            color = int(content.replace('#', ''), 16)
            server_configs[guild_id]["profile_template"]["color"] = color
            await ctx.send(f"Profile {element} set to: {content}")
        except ValueError:
            await ctx.send("Invalid color format. Please use hex format (e.g., #3498db)")
    else:
        server_configs[guild_id]["profile_template"][element.lower()] = content
        await ctx.send(f"Profile {element} set to: {content}")

@bot.command(name='showconfig')
@commands.has_permissions(administrator=True)
async def show_config(ctx):
    guild_id = str(ctx.guild.id)
    config = server_configs.get(guild_id, DEFAULT_CONFIG)
    
    embed = discord.Embed(title="Current Welcome Bot Configuration", color=0x3498db)
    
    embed.add_field(name="Welcome Channel", 
                   value=f"<#{config['welcome_channel']}>" if config['welcome_channel'] else "Not set", 
                   inline=False)
    embed.add_field(name="Welcome Title", value=config['welcome_title'], inline=False)
    embed.add_field(name="Welcome Description", value=config['welcome_description'], inline=False)
    embed.add_field(name="Welcome Banner", value=config['welcome_banner'] or "Not set", inline=False)
    embed.add_field(name="Welcome Footer", value=config['welcome_footer'], inline=False)
    embed.add_field(name="Welcome Color", value=f"#{hex(config['welcome_color'])[2:]}", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='welcometest')
@commands.has_permissions(administrator=True)
async def welcome_test(ctx):
    """Test the welcome message with your profile"""
    guild_id = str(ctx.guild.id)
    config = server_configs.get(guild_id, DEFAULT_CONFIG)
    
    if config["welcome_channel"]:
        channel = bot.get_channel(config["welcome_channel"])
    else:
        channel = ctx.channel
    
    # Create welcome embed
    embed = discord.Embed(
        title=config["welcome_title"].format(server=ctx.guild.name, member=ctx.author),
        description=config["welcome_description"].format(server=ctx.guild.name, member=ctx.author),
        color=config["welcome_color"]
    )
    
    # Set banner if available
    if config["welcome_banner"]:
        embed.set_image(url=config["welcome_banner"])
    
    # Set footer
    embed.set_footer(text=config["welcome_footer"].format(
        server=ctx.guild.name,
        member=ctx.author,
        member_count=ctx.guild.member_count
    ))
    
    await channel.send(embed=embed)
    
    # Create and send profile card
    profile_card = await create_profile_card(ctx.author, config["profile_template"])
    if profile_card:
        await channel.send(file=profile_card)

@bot.command(name='welcomehelp')
async def welcome_help(ctx):
    """Show all available commands"""
    embed = discord.Embed(title="Welcome Bot Help", color=0x3498db)
    
    embed.add_field(
        name="Configuration Commands (Admin Only)",
        value="""
        `/setwelcomechannel #channel` - Set the welcome channel
        `/setwelcometitle Your Title` - Set welcome message title
        `/setwelcomedescription Your description` - Set welcome description
        `/setwelcomebanner URL` - Set welcome banner image
        `/setwelcomefooter Your footer` - Set welcome footer
        `/setwelcomecolor #hexcolor` - Set welcome color
        `/setprofiletemplate element content` - Set profile template elements
          (elements: title, subtitle, description, banner, footer, color)
        """,
        inline=False
    )
    
    embed.add_field(
        name="Utility Commands",
        value="""
        `/showconfig` - Show current configuration
        `/welcometest` - Test the welcome message
        `/welcomehelp` - Show this help message
        """,
        inline=False
    )
    
    embed.set_footer(text="Use / or ; prefix for commands")
    
    await ctx.send(embed=embed)

# Run the bot
if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))

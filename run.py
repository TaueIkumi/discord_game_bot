import os
from dotenv import load_dotenv
import logging

import discord
from discord.ext import commands, tasks
from datetime import datetime

import settings as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

SETTINGS_FILE = "voice_notification_settings.json"

settings = st.load_settings()

@bot.tree.command(name='set_notification_voice_channel', description='Set the channel to send voice channel notifications')
async def set_notification_voice_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    
    if guild_id not in settings or not isinstance(settings[guild_id], dict):
        settings[guild_id] = {}
    
    settings[guild_id]['voice_channel_id'] = channel.id
    st.save_settings(settings)
    await interaction.response.send_message(f'Voice notification channel set to {channel.mention}')

@bot.tree.command(name='set_game_invite_channel', description='Set the channel to send game invites')
async def set_notification_text_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    guild_id = str(interaction.guild.id)

    if guild_id not in settings or not isinstance(settings[guild_id], dict):
        settings[guild_id] = {}
    
    settings[guild_id]['game_invite_channel'] = channel.id
    st.save_settings(settings)
    await interaction.response.send_message(f'Text notification channel set to {channel.mention}')


@bot.event
async def on_ready():
    logger.info('Bot is running')
    await bot.tree.sync()
    logger.info("Synced the command tree!")

    commands_list = bot.tree.get_commands()
    command_names = [command.name for command in commands_list]
    logger.info(f'Registered commands: {", ".join(command_names)}')

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is None and after.channel is not None:
        guild_settings = settings.get(str(member.guild.id), {})
        text_channel_id = guild_settings.get('voice_channel_id')
        if text_channel_id:
            text_channel = bot.get_channel(text_channel_id)
            if text_channel is not None:
                embed = discord.Embed(
                    title='Voice Channel Notification',
                    description=f'{member.mention} has started a voice chat in {after.channel.mention}',
                    color=discord.Color.dark_blue()
                )
                await text_channel.send(embed=embed)

@tasks.loop(minutes=1)
async def send_reminder():
    now = datetime.now().strftime('%H:%M')
    if now == '17:00':
        for guild_id, guild_settings in settings.items():
            reminder_channel_id = guild_settings.get('text_channel_id')
            if reminder_channel_id:
                reminder_channel = bot.get_channel(reminder_channel_id)
                if reminder_channel is not None:
                    embed = discord.Embed(
                        title='Game Invite',
                        description='Are you able to play?',
                        color=discord.Color.brand_red()
                    )
                    message = await reminder_channel.send(embed=embed)
                    await message.add_reaction('👍')
                    await message.add_reaction('👎')

bot.run(TOKEN)

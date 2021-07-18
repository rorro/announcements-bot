import json
import os
import time
from configparser import ConfigParser

import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv('TOKEN')
CONFIG_FILE = 'config.ini'

# Config
config_parser = ConfigParser()
config_parser.read(CONFIG_FILE)

# In minutes
CHALLENGE_TIME = int(config_parser.get('CHALLENGE', 'frequency'))
BOUNTY_TIME = int(config_parser.get('BOUNTY', 'frequency'))

challenge_start = 0
bounty_start = 0
started = False


def read_file(file):
    with open(file) as f:
        lst = []
        for entry in json.load(f):
            lst.append(entry)

        return lst


bounties = read_file(config_parser.get('BOUNTY', 'file'))
challenges = read_file(config_parser.get('CHALLENGE', 'file'))

# Create bot
client = commands.Bot(command_prefix='!')


# Startup information
@client.event
async def on_ready():
    print(f'Connected to bot: {client.user.name}')
    print(f'Bot ID: {client.user.id}')


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        return
    elif isinstance(error, commands.CommandInvokeError):
        return
    elif isinstance(error, commands.ChannelNotFound):
        return
    raise error


@commands.has_permissions(administrator=True)
@client.command(help='- Start the announcements')
async def start(ctx):
    global started

    if config_parser.get('CHALLENGE', 'enabled') == "True":
        challenge_loop.start()
    if config_parser.get('BOUNTY', 'enabled') == "True":
        bounty_loop.start()
    started = True
    await ctx.send('Announcements have been started')
    time.sleep(3)
    countdown.start()


@commands.has_permissions(administrator=True)
@client.command(help='- Stop the announcements')
async def stop(ctx):
    global started

    challenge_loop.cancel()
    bounty_loop.cancel()
    countdown.cancel()
    started = False
    await ctx.send('Announcements have been stopped')


@commands.has_permissions(administrator=True)
@client.command(help='- DO NOT USE THIS WHILE EVENT IS ONGOING!')
async def reset(ctx):
    config_parser.set('BOUNTY', 'index', '0')
    with open(CONFIG_FILE, 'w') as config_file:
        config_parser.write(config_file)

    config_parser.set('CHALLENGE', 'index', '0')
    with open(CONFIG_FILE, 'w') as config_file:
        config_parser.write(config_file)

    await ctx.send('Indexes have been reset to 0')


@commands.has_permissions(administrator=True)
@client.command(help='- Give a message id to set message as ended. Run this in the same channel as the ended message.')
async def end(ctx, arg):
    ended_message = await ctx.fetch_message(int(arg))

    if ended_message.author == client.user:
        new_embed = ended_message.embeds[0]
        new_embed.set_footer(text='Time remaining: 0h 0min')
        await ended_message.edit(embed=new_embed)
    await ctx.message.delete()


@commands.has_permissions(administrator=True)
@client.command(help='- Set channels for bounties and challenges. Configure this before you start the event!')
async def set_channel(ctx, t, channel: discord.TextChannel):
    if started:
        await ctx.send("You can only configure this while the event is stopped.")
        return

    if t not in ["bounty", "challenge"]:
        await ctx.send("Invalid type. Only valid types are 'bounty' and 'challenge'.")
        return

    config_parser.set(t.upper(), 'channel', str(channel.id))
    with open(CONFIG_FILE, 'w') as config_file:
        config_parser.write(config_file)

    await ctx.send(f'Successfully set the {t} channel to {channel.mention}')


# Announcements for the bounty channel
@tasks.loop(minutes=BOUNTY_TIME)
async def bounty_loop():
    global bounty_start
    bounty_start = datetime.now()

    bounty_channel = client.get_channel(int(config_parser.get('BOUNTY', 'channel')))
    bounty_index = int(config_parser.get('BOUNTY', 'index'))

    if bounty_index >= len(bounties):
        bounty_loop.stop()
        return

    embed_message = discord.Embed(title=f'{BOUNTY_TIME//60} Hour Bounty', color=discord.Color.green())
    embed_message.add_field(name="The current bounty is...", value=bounties[bounty_index]['bounty'], inline=False)
    embed_message.add_field(name="Keyword", value=bounties[bounty_index]['keyword'])
    embed_message.set_footer(text=f'Time remaining: {BOUNTY_TIME//60}h {BOUNTY_TIME%60}min')

    msg = await bounty_channel.send(embed=embed_message)

    config_parser.set('BOUNTY', 'index', str(bounty_index + 1))
    config_parser.set('BOUNTY', 'message_id', str(msg.id))
    with open(CONFIG_FILE, 'w') as config_file:
        config_parser.write(config_file)


# Announcements for the challenges channel
@tasks.loop(minutes=CHALLENGE_TIME)
async def challenge_loop():
    global challenge_start
    challenge_start = datetime.now()

    challenge_channel = client.get_channel(int(config_parser.get('CHALLENGE', 'channel')))
    challenge_index = int(config_parser.get('CHALLENGE', 'index'))

    if challenge_index >= len(challenges):
        challenge_loop.stop()
        return

    embed_message = discord.Embed(title="Daily Challenge", color=discord.Color.green())
    embed_message.add_field(name="The current challenge is...", value=challenges[challenge_index]['challenge'], inline=False)
    embed_message.add_field(name="Keyword", value=challenges[challenge_index]['keyword'])
    embed_message.set_footer(text=f'Time remaining: {CHALLENGE_TIME // 60}h {CHALLENGE_TIME % 60}min')

    msg = await challenge_channel.send(embed=embed_message)

    config_parser.set('CHALLENGE', 'index', str(challenge_index + 1))
    config_parser.set('CHALLENGE', 'message_id', str(msg.id))
    with open(CONFIG_FILE, 'w') as config_file:
        config_parser.write(config_file)


def update_counter(message, t, start_time):
    new_embed = message.embeds[0]

    difference = datetime.now() - start_time
    difference_min = difference.seconds//60

    new_embed.set_footer(text=f'Time remaining: {(t - difference_min)//60}h {(t - difference_min)%60}min')
    return new_embed


@tasks.loop(minutes=1)
async def countdown():
    if config_parser.get('BOUNTY', 'enabled') == "True":
        bounty_channel = await client.fetch_channel(config_parser.get('BOUNTY', 'channel'))
        bounty_message = await bounty_channel.fetch_message(config_parser.get('BOUNTY', 'message_id'))
        await bounty_message.edit(embed=update_counter(bounty_message, BOUNTY_TIME, bounty_start))

    if config_parser.get('CHALLENGE', 'enabled') == "True":
        challenge_channel = await client.fetch_channel(config_parser.get('CHALLENGE', 'channel'))
        challenge_message = await challenge_channel.fetch_message(config_parser.get('CHALLENGE', 'message_id'))
        await challenge_message.edit(embed=update_counter(challenge_message, CHALLENGE_TIME, challenge_start))


client.run(TOKEN)

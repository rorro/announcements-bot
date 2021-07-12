import json
import os
from configparser import ConfigParser
from discord.ext import tasks, commands
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv('TOKEN')
CONFIG_FILE = 'config.ini'

# In minutes
CHALLENGE_TIME = 1440
BOUNTY_TIME = 360

challenge_start = 0
bounty_start = 0

# Config
config_parser = ConfigParser()
config_parser.read(CONFIG_FILE)


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
    raise error


@commands.has_permissions(administrator=True)
@client.command(help='- Start the announcements')
async def start(ctx):
    challenge_loop.start()
    bounty_loop.start()
    countdown.start()
    await ctx.send('Announcements have been started')


@commands.has_permissions(administrator=True)
@client.command(help='- Stop the announcements')
async def stop(ctx):
    challenge_loop.stop()
    bounty_loop.stop()
    countdown.stop()
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
    message_content = ended_message.content

    is_bounty = message_content.find('6 Hour Bounty') != -1
    is_challenge = message_content.find('Daily Challenge') != -1

    if ended_message.author == client.user and (is_bounty or is_challenge):
        idx = message_content.find('remaining')
        if idx != -1:
            new_message = message_content[:idx - 5]
            new_message += 'Bounty ended*' if is_bounty else 'Challenge ended*'
            await ended_message.edit(content=new_message)
    await ctx.message.delete()


# Announcements for the bounty channel
@tasks.loop(minutes=BOUNTY_TIME)
async def bounty_loop():
    global bounty_start

    bounty_channel = client.get_channel(int(config_parser.get('BOUNTY', 'channel')))
    bounty_index = int(config_parser.get('BOUNTY', 'index'))

    if bounty_index >= len(bounties):
        bounty_loop.stop()
        return

    message = f"{bounty_index}). **6 Hour Bounty:**\n\
    The current bounty is...\n\
    `{bounties[bounty_index]['bounty']}`\n\n\
    **Keyword:**\n\
    `{bounties[bounty_index]['keyword']}`\n\n\
    *time remaining: {BOUNTY_TIME//60}h {BOUNTY_TIME%60}min*"

    msg = await bounty_channel.send(message)

    config_parser.set('BOUNTY', 'index', str(bounty_index + 1))
    config_parser.set('BOUNTY', 'message_id', str(msg.id))
    with open(CONFIG_FILE, 'w') as config_file:
        config_parser.write(config_file)

    bounty_start = datetime.now()


# Announcements for the challenges channel
@tasks.loop(minutes=CHALLENGE_TIME)
async def challenge_loop():
    global challenge_start

    challenge_channel = client.get_channel(int(config_parser.get('CHALLENGE', 'channel')))
    challenge_index = int(config_parser.get('CHALLENGE', 'index'))

    if challenge_index >= len(challenges):
        challenge_loop.stop()
        return

    message = f"{challenge_index}). **Daily Challenge:**\n\
    The current challenge is...\n\
    `{challenges[challenge_index]['challenge']}`\n\n\
    **Keyword:**\n\
    `{challenges[challenge_index]['keyword']}`\n\n\
    *time remaining: {CHALLENGE_TIME//60}h {CHALLENGE_TIME%60}min*"

    msg = await challenge_channel.send(message)

    config_parser.set('CHALLENGE', 'index', str(challenge_index + 1))
    config_parser.set('CHALLENGE', 'message_id', str(msg.id))
    with open(CONFIG_FILE, 'w') as config_file:
        config_parser.write(config_file)

    challenge_start = datetime.now()


def update_counter(message, t, start_time):
    idx = message.find("remaining")
    difference = datetime.now() - start_time
    difference_min = difference.seconds//60 + 1
    return message[:idx+11] + f'{(t - difference_min)//60}h {(t - difference_min)%60}min*'


@tasks.loop(minutes=1)
async def countdown():
    bounty_channel = await client.fetch_channel(config_parser.get('BOUNTY', 'channel'))
    bounty_message = await bounty_channel.fetch_message(config_parser.get('BOUNTY', 'message_id'))

    challenge_channel = await client.fetch_channel(config_parser.get('CHALLENGE', 'channel'))
    challenge_message = await challenge_channel.fetch_message(config_parser.get('CHALLENGE', 'message_id'))

    await bounty_message.edit(content=update_counter(bounty_message.content, BOUNTY_TIME, bounty_start))
    await challenge_message.edit(content=update_counter(challenge_message.content, CHALLENGE_TIME, challenge_start))

client.run(TOKEN)

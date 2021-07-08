import json
import os
from configparser import ConfigParser

from discord.ext import tasks, commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')
CONFIG_FILE = 'config.ini'

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


# Startup infomation
@client.event
async def on_ready():
    print(f'Connected to bot: {client.user.name}')
    print(f'Bot ID: {client.user.id}')


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        ctx.send('Only admins can use this command.')
        return
    raise error


@commands.has_permissions(administrator=True)
@client.command(help='- Start the announcements')
async def start(ctx):
    challenge_loop.start()
    bounty_loop.start()
    await ctx.send('Announcements have been started')


@commands.has_permissions(administrator=True)
@client.command(help='- Stop the announcements')
async def stop(ctx):
    challenge_loop.stop()
    bounty_loop.stop()
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

    await ctx.send('Indexes has been reset to 0')


# Announcements for the bounty channel
@tasks.loop(hours=6)
async def bounty_loop():
    bounty_channel = client.get_channel(int(config_parser.get('BOUNTY', 'channel')))
    bounty_index = int(config_parser.get('BOUNTY', 'index'))

    if bounty_index >= len(bounties):
        bounty_loop.stop()
        return

    message = f"{bounty_index}). **6 Hour Bounty:**\n\
    The current bounty is...\n\
    `{bounties[bounty_index]['bounty']}`\n\n\
    **Keyword:**\n\
    `{bounties[bounty_index]['keyword']}`"

    config_parser.set('BOUNTY', 'index', str(bounty_index+1))
    with open(CONFIG_FILE, 'w') as config_file:
        config_parser.write(config_file)

    await bounty_channel.send(message)


# Announcements for the challenges channel
@tasks.loop(hours=24)
async def challenge_loop():
    challenge_channel = client.get_channel(int(config_parser.get('CHALLENGE', 'channel')))
    challenge_index = int(config_parser.get('CHALLENGE', 'index'))

    if challenge_index >= len(challenges):
        challenge_loop.stop()
        return

    message = f"{challenge_index}). **Daily Challenge:**\n\
    The current challenge is...\n\
    `{challenges[challenge_index]['challenge']}`\n\n\
    **Keyword:**\n\
    `{challenges[challenge_index]['keyword']}`"

    config_parser.set('CHALLENGE', 'index', str(challenge_index+1))
    with open(CONFIG_FILE, 'w') as config_file:
        config_parser.write(config_file)

    await challenge_channel.send(message)


client.run(TOKEN)

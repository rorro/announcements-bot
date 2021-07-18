# Legacy Gauntlet
A Discord bot for simple bounties and challenges announcements.

## Requirements
Python3+ and pip.

## Setting up
1. Download source code and run 'pip install -r requirements.txt' in the project folder.
2. Create a .env file with your bot token in it (see below for how it should look).
3. Create bounty.json and challenge.json files in the root of the project (see below for how they should look).
4. Run the bot using 'python main.py'

## Configuration
The bot uses a config.ini file to keep all the configurations.

**channel**: The channel where the announcement is sent. Can be configured with a command.

**file**: The json file where the challenges/bounties are stored.

**index**: The index of the current challenge/bounty.

**message_id**: The id of current challenge/bounty message.

**frequency**: The frequency of announcements (in minutes).

**enabled**: If the bot will announce bounties/challenges. If set to False, the bot will make an announcement.

## Commands
All commands require admin permissions.

**start**: Starts the announcements. Note that this will send a bounty and a challenge immediately.

**stop**: Stops the announcements.

**reset**: This will reset the indexes back to 0. You probably don't wanna use this while the competition is ongoing.

**set_channel <bounty/challenge> <#channel>**: Set the channel in which the bounties and challenges are sent. The channel argument is a channel mention, eg #bounties.

**end <message_id>**: Sets the time remaining of a challenge/bounty to 0h 0min. You can get the message id by right clicking the message on discord.

## Files
.env should only contain your discord bot token.

`TOKEN = YOUR_DISCORD_BOT_TOKEN_GOES_HERE`

bounty.json should look like this (note the bounties below are just examples, write your own):
```
[
  {
    "bounty": "Obtain a goblin mail",
    "keyword": "It's too small :("
  },
  {
    "bounty": "Kill zuk",
    "keyword": "zucc it"
  }
 ]
```

challenge.json should look like this (note the bounties below are just examples, write your own):
```
[
  {
    "challenge": "Fastest vorkath kill",
    "keyword": "pew pew rng"
  },
  {
    "challenge": "Fastest zuk kill",
    "keyword": "zucc it, but quick"
  }
 ]
```

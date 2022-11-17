#!/usr/bin/env python3

import discord
from discord.ext import commands
import io
import aiohttp
import yaml
from datetime import datetime
import pytz



def log(message=str):
    '''
    Saves date, time and input message on a new line in 'log.txt'
    '''

    # Get current date and time (in UTC+0 time zone)
    date_time = datetime.now(pytz.utc)
    date = date_time.strftime('%Y-%m-%d')
    time = date_time.strftime('%H:%M:%S')


    # Create line: [YY-MM-DD] [hh:mm:ss]: message
    new_line = '[' + date + '] [' + time + ']: ' + message
    print(new_line)


    # Save to file
    log_file = open('log.txt', 'a')
    log_file.write('\n' + new_line)
    log_file.close()



# Load yaml file from 'file_name' as dictionary (config)
file_name = 'params.yaml'

try:
    with open(file_name) as file:
        config = yaml.safe_load(file)

except:
    print('Error loading ' + file_name)
    exit(0)



# Initialize client
client = commands.Bot(  command_prefix=commands.when_mentioned_or(
                        config['prefix']),
                        case_insensitive=True,
                        intents = discord.Intents.all(),
                        help_command=None)



# ---------------------
#        EVENTS
# ---------------------



@client.event
async def on_ready():
    '''
    This is executed when the bot is ready
    '''

    # Print server list
    print('\nReady! Connected as ' + str(client.user))
    print('Connected to ' + str(len(client.guilds)) + ' servers:')
    for guild in client.guilds:
        member_count = str(guild.member_count)
        print('- ' + guild.name + ' (' + member_count + ' members)')

    log('---------- READY ----------')



@client.event
async def on_message(message: discord.Message):
    '''
    Executed every time someone sends a message, with or without the prefix
    '''

    # Don't reply to self or other bots
    if message.author == client.user or message.author.bot:
        return


    # If the message isn't from Private, process commands
    if message.channel.type != discord.ChannelType.private:
        return await client.process_commands(message)


    # Get channel from saved ID
    target_channel = client.get_channel(config['channel_id'])


    # If the bot can't find the channel (no permissions / invalid id)
    if target_channel is None:
        embed = discord.Embed(
            title='Error',
            description='Invalid channel!',
            color=0xdd2e44)
        return await message.channel.send(embed=embed)


    # If the message has no attachments
    if len(message.attachments) < 1:
        log(message.content)
        await target_channel.send(message.content)


    # If the message has attachments
    else:
        url = message.attachments[0].url
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:


                # Fail message
                if resp.status != 200:
                    embed = discord.Embed(
                        title='Error',
                        description='Failed to send attachment',
                        color=0xdd2e44)
                    return await message.channel.send(embed=embed)


                # Log message + url
                new_line = message.content + ' [' + url + ']'
                log(new_line)


                # Send message with attachment
                data = io.BytesIO(await resp.read())
                image = discord.File(data, 'image.png')
                await target_channel.send(message.content, file=image)


    # If this is reached, the message was sent
    await message.add_reaction('✅')



@client.event
async def on_command_completion(ctx):
    '''
    This is executed when a command is successfully executed
    '''

    log(ctx.message.content)



@client.event
async def on_command_error(ctx, error):
    '''
    This is executed when a command catches an error (unknown commands)
    '''

    log(ctx.message.content)

    # Don't show error in terminal
    if isinstance(error, commands.CommandNotFound):
        pass



# ---------------------
#       COMMANDS
# ---------------------



@client.command()
async def help(ctx):
    '''
    help: give useful info depending on where it's used
    '''

    if ctx.channel.id == config['channel_id']:
        text = 'Messages received are sent to this channel'
    else:
        text = 'Messages received are sent to a different channel'

    embed = discord.Embed(
        title='How to use',
        description=text,
        color=0x77b255)
    await ctx.send(embed=embed)



@client.command()
async def set_channel(ctx):
    '''
    set_channel: set target channel to send messages
    '''

    # Only users in white list can use this
    if ctx.message.author.id in config['white_list']:

        # Only works on text channels
        if ctx.message.channel.type == discord.ChannelType.text:

            # Replace channel ID in file
            config['channel_id'] = ctx.channel.id
            with open(file_name, 'w') as file:
                yaml.dump(config, file)
            await ctx.message.add_reaction('✅')

        else:
            await ctx.message.add_reaction('❌')



@client.command()
async def where(ctx):
    '''
    where: get target channel location
    '''

    # Only users in white list can use this
    if ctx.message.author.id in config['white_list']:

        # Reply with target channel location
        channel = client.get_channel(config['channel_id'])
        if channel is not None:

            if channel == ctx.channel:
                location = "Here"
            else:
                location = "**Server:** " + channel.guild.name
                location += "\n**Channel:** " +  channel.name
            await ctx.send(location)
        else:
            await ctx.send("I don't know")



@client.command()
async def prefix(ctx, *, args):
    '''
    prefix: change bot prefix
    '''

    # Only users in white list can use this
    if ctx.message.author.id in config['white_list']:
        config['prefix'] = args
        with open(file_name, 'w') as file:
            yaml.dump(config, file)


        # Update client with new prefix
        client.command_prefix = commands.when_mentioned_or(config['prefix'])

        await ctx.message.add_reaction('✅')



# Run
client.run(config['TOKEN'])
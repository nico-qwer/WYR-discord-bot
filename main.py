import discord
from discord.ext import commands
import os
import random
import time
from replit import db
from keep_alive import keep_alive
from discord.utils import get

def get_prefix(client, ctx):
    print(db["prefixes"])
    prefixes = db["prefixes"]
    print(ctx.guild.id in prefixes)
    if not ctx.guild.id in prefixes:
        prefixes[ctx.guild.id] = "$"
        db["prefixes"] = prefixes
        print("changed")
    print(ctx.guild.id)
    print(prefixes)
    return prefixes[ctx.guild.id]

def get_prefix_2(client, ctx):
    prefixes = db["prefixes"]
    print(prefixes[ctx.guild.id])
    return prefixes[ctx.guild.id]

client = commands.Bot(command_prefix = get_prefix)
client.remove_command("help")

red_emoji = "🟥"
blue_emoji = "🟦"


if "prefixes" not in db.keys():
    db["prefixes"] = {}
  
if "add_roles" not in db.keys():
    db["add_roles"] = {}

if "delays" not in db.keys():
    db["delays"] = {}

if "update_channel" not in db.keys():
    db["update_channel"] = {}

#====================== UTILITIES ======================#
  
#Updates the prefix for a server
def update_prefix(prefix, server):
    prefixes = db["prefixes"]
    prefixes[server] = prefix
    db["prefixes"] = prefixes
  
#Updates the role needed to add questions
def update_add_role(role, server):
    roles = db["add_roles"]
    roles[server] = role
    db["add_roles"] = roles

#Updates the delay between the question and the reveal
def update_delay(delay, server):
    delays = db["delays"]
    delays[server] = delay
    db["delays"] = delays

#Updates the channel the bot will post updates
def update_channel(channel, server):
    channels = db["update_channel"]
    channels[server] = channel
    db["update_channel"] = channels
    
#Adds a choice in the database
def add_choice(new_sentence, server):
    if server not in db.keys():
        db[str(server)] = []
    sentences = db[str(server)]
    sentences.append(new_sentence)
    db[str(server)] = sentences

  
#Formats choices like this : ch1-ch2-author
def format_choices(choice1, choice2, author):
    return choice1 + "-" + choice2 + "-" + author


#====================== EVENTS ======================#
    
#Fires when the bot joins a server
@client.event
async def on_guild_join(guild):
    prefixes = db["prefixes"]
    if guild.id not in prefixes:
        prefixes[guild.id] = "$"
        #db["prefixes"] = prefixes
  
#Fires when the bot is logged in
@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))
    for guild in client.guilds:
        update_channel = 0
        if guild.id in db["update_channel"]:
            update_channels = db["update_channel"]
            update_channel = update_channels[guild.id]
        
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel) and channel.id == update_channel:
                await channel.send("I am back online!")
                break
            elif isinstance(channel, discord.TextChannel) and channel.name == "general":
                await channel.send("I am back online!")
                break
                    
                      
#====================== CUSTOM CHECKS ======================#
def has_add_role(ctx):
    roles = db["add_roles"]
    if ctx.guild.id in roles:
        role_name = str(roles[ctx.guild.id])
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role in ctx.author.roles:
            return True
        #elif str(ctx.author) == os.environ["BOT CREATOR"]:
        #return True
        else:
            return False
    return True
  
#====================== COMMANDS ======================#

#Lists every command possible
@client.command(description = "Lists every command possible \nNo arguments.")
async def help(ctx):
    embed = discord.Embed(title="Help menu:", colour=0xAD00AD)
    for command in client.walk_commands():
        if command.name == "deletedatabase": continue
        
        syntax = command.description
        
        if not syntax or syntax is None or syntax == "":
            syntax = "ERROR: no syntax specified."

        keywords = db["prefixes"]
        embed.add_field(name= keywords[ctx.guild.id] + command.name, value=syntax, inline=False)
    await ctx.send(embed=embed)
    
#Changes the prefix used to call the bot
@client.command(description = "Changes the prefix used to call the bot \narguments: <prefix>")
@commands.has_permissions(administrator = True)
async def setprefix(ctx, new_prefix):
    update_prefix(new_prefix, ctx.guild.id)
    await ctx.send("Updated prefix to " + new_prefix)

  
#Test
@client.command(description = "Test command \nNo arguments.")
async def test(ctx):
    await ctx.send("I am working!")

  
#Add a question to the database
@client.command(description = "Add a question to the database \narguments: <choice1> <choice2>")
async def addquestion(ctx, choice1, choice2):
    if has_add_role(ctx) == False: 
        roles = db["add_roles"]
        await ctx.send("You need the " + str(roles[ctx.guild.id]) + " role to add questions.")
        return
    
    add_choice(format_choices(choice1, choice2, str(ctx.author)), ctx.guild.id)
    await ctx.send("Added choices: "+ choice1 + ", or " + choice2)

    
#Changes channel the bot will post updates
@client.command(description = "Changes channel the bot will post updates \narguments: <#channelname>")
@commands.has_permissions(administrator = True)
async def setupdatechannel(ctx, channel: discord.TextChannel):
    channel_id = channel.id
    update_channel(channel_id, ctx.guild.id)
    ctx.send("Update messages will now be sent in " + channel.mention)

#Updates role necessary to add questions
@client.command(description = "Updates role necessary to add questions \narguments: <@role>")
@commands.has_permissions(administrator = True)
async def setaddrole(ctx, role: discord.Role):
    if role != None:
        update_add_role(role, ctx.guild.id)
        await ctx.send("Changed add role to {0}.".format(role.mention))


#Updates delay between question and reveal
@client.command(description = "Updates delay between question and reveal \narguments: <seconds>")
@commands.has_permissions(administrator = True)
async def setdelay(ctx, arg):
    update_delay(float(arg), ctx.guild.id)
    await ctx.send("Changed delay to " + arg + " seconds.")

      
#Lists all questions
@client.command(description = "Lists all questions in database \nNo arguments.")
async def list(ctx):
    questions = db[ctx.guild.id]

    if len(questions) == 0:
        prefixes = db["prefixes"]
        await ctx.send("No questions recorded yet. Use the '" + prefixes[ctx.guild.id] + "addquestion' command.")
        return
    
    embed = discord.Embed(title="Listing all recorded questions:", colour=0xAD00AD)
    i = 1
    for sentence in questions:
        choice1 = sentence.split("-")[0]
        choice2 = sentence.split("-")[1]
        author = sentence.split("-")[2]

        embed.add_field(
            name=str(i), 
            value=choice1 + ", or " + choice2 + ", made by " + author, inline=False
        )
        i = i + 1
      
    await ctx.send(embed=embed)

  
#Deletes one or multiple question(s)
@client.command(description = "Deletes one or multiple question(s) \narguments: <number>")
@commands.has_permissions(administrator = True)
async def delete(ctx, *args):
    questions = db[ctx.guild.id]
    indexes = []
    for number in args:
        int_num = int(number)
        indexes.append(int_num)
    
    for index in indexes:
        if index > len(questions): 
            await ctx.send(index + " will be skipped because it is not in the questions.")
            indexes.remove(index)
    
    embed = discord.Embed(title="Deleted questions:", colour=0xAD00AD)
    
    for question in questions:  
        if questions.index(question) + 1 in indexes:
            choice1 = question.split("-")[0]
            choice2 = question.split("-")[1]
            author = question.split("-")[2]
        
        embed.add_field(name=str(index), value= choice1 + ", or " + choice2 + ", made by " + author, inline=False)
        questions.pop(index - 1)
      
    await ctx.send(embed=embed)
    db[ctx.guild.id] = questions

    
#Main game
@client.command(description = "Play the game! \nNo arguments.")
async def play(ctx):
    if ctx.guild.id not in db.keys():
        prefixes = db["prefixes"]
        await ctx.send("No questions recorded yet. Use the '" + prefixes[ctx.guild.id] + "addquestion' command.")
        return
    
    sentences = db[ctx.guild.id]
    non_formated_chosen = random.choice(sentences)
    
    choice1 = non_formated_chosen.split("-")[0]
    choice2 = non_formated_chosen.split("-")[1]
    author = non_formated_chosen.split("-")[2]

    embed = discord.Embed(title="Would you rather:", colour=0xAD00AD)
    embed.add_field(name="Choice 1", value= red_emoji + " : " + choice1, inline=False)
    embed.add_field(name="Choice 2", value= blue_emoji + " : " + choice2, inline=False)
    embed.set_footer(text="Question by " + author)

    current = await ctx.send(embed=embed)
    
    await current.add_reaction(red_emoji)
    await current.add_reaction(blue_emoji)

    delays = db["delays"]
    if ctx.guild.id not in delays:
        update_delay(float(20), ctx.guild.id)
        delays = db["delays"]
    
    time.sleep(delays[ctx.guild.id])

    new_current = await current.channel.fetch_message(current.id)
    
    red_reactions = get(new_current.reactions, emoji=red_emoji).count
    blue_reactions = get(new_current.reactions, emoji=blue_emoji).count

    if red_reactions > blue_reactions:
        await new_current.channel.send("More people would rather " + choice1 + " than " + choice2 + "!")
    elif red_reactions < blue_reactions:
        await new_current.channel.send("More people would rather " + choice2 + " than " + choice1 + "!")
    
#Command to delete everything in database
@client.command()
async def deletedatabase(ctx, password):
    if str(ctx.author) != "nico_qwer#9317": return
    if password != "yes delete database": return
    keys = db.keys()
    for key in keys:
        print("Deleted " + str(key))
        del db[str(key)]
    await ctx.send("Deleted every key in database with success.")


#keep_alive()
client.run(os.environ['TOKEN'])

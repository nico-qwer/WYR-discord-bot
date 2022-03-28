import discord
from discord.ext import commands
import os
import random
import time
from replit import db
from keep_alive import keep_alive
from discord.utils import get

def get_prefix(client, ctx):
    prefixes = db["prefixes"]
    if str(ctx.guild.id) not in prefixes:
        prefixes[str(ctx.guild.id)] = "$"
        db["prefixes"] = prefixes
    return prefixes[str(ctx.guild.id)]
  

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

#====================== UTILITIES ======================#
  
#Updates the prefix for a server
def update_prefix(prefix, server):
    prefixes = db["prefixes"]
    prefixes[str(server)] = prefix
    db["prefixes"] = prefixes

  
#Updates the role needed to add questions
def update_add_role(role, server):
    roles = db["add_roles"]
    roles[str(server)] = role
    db["add_roles"] = roles

  
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


def get_role_from_mention(mention):
    if mention.startswith('<@&') and mention.endswith('>'):
        id = mention[3:-1]
        return int(id)

#====================== EVENTS ======================#
    
#Fires when the bot joins a server
@client.event
async def on_guild_join(guild):
    prefixes = db["prefixes"]
    prefixes[str(guild.id)] = "$"

  
#Fires when the bot is logged in
@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))
    #for guild in client.guilds:
    #  for channel in guild.channels:
    #    if isinstance(channel, discord.TextChannel): # Check if channel is a text channel
    #        await channel.send("I am back online!")
  
#====================== CUSTOM CHECKS ======================#
async def has_add_role(ctx):
    prefixes = db["prefixes"]
    if str(ctx.guild.id) in prefixes:
        return True
    elif str(ctx.author) == os.environ["BOT CREATOR"]:
        return True
    else:
        return False
  
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

        embed.add_field(name= db["prefixes"][str(ctx.guild.id)] + command.name, value=syntax, inline=False)
    await ctx.send(embed=embed)
    
#Changes the prefix used to call the bot
@client.command(description = "Changes the prefix used to call the bot \narguments: <prefix>")
@commands.has_permissions(administrator = True)
async def changeprefix(ctx, new_prefix):
    update_prefix(new_prefix, ctx.guild.id)
    await ctx.send("Updated prefix to " + new_prefix)

  
#Test
@client.command(description = "Test command \nNo arguments.")
async def test(ctx):
    await ctx.send("I am working!")

  
#Add a question to the database
@client.command(description = "Add a question to the database \narguments: <choice1> <choice2>")
@commands.check(has_add_role)
async def addquestion(ctx, choice1, choice2):

    add_choice(format_choices(choice1, choice2, str(ctx.author)), str(ctx.guild.id))

    await ctx.send("Added choices: "+ choice1 + ", or " + choice2)

  
#Updates role necessary to add questions
@client.command(description = "Updates role necessary to add questions \narguments: <@role>")
@commands.has_permissions(administrator = True)
async def setaddrole(ctx, arg):

    role_id = get_role_from_mention(str(arg))

    role = ctx.guild.get_role(role_id)
      
    if role != None:
        update_add_role(str(role), ctx.guild.id)
        await ctx.send("Changed add role to {0}.".format(role.mention))


#Updates delay between question and reveal
@client.command(description = "Updates delay between question and reveal \narguments: <seconds>")
@commands.has_permissions(administrator = True)
async def setdelay(ctx, arg):
    delays = db["delays"]
    delays[str(ctx.guild.id)] = float(arg)
    db["delays"] = delays

    await ctx.send("Changed delay to " + arg + " seconds.")

      
#Lists all questions
@client.command(description = "Lists all questions in database \nNo arguments.")
async def list(ctx):
    questions = db[str(ctx.guild.id)]

    if len(questions) == 0:
        prefixes = db["prefixes"]
        await ctx.send("No questions recorded yet. Use the '" + prefixes[str(ctx.guild.id)] + "addquestion' command.")
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
    questions = db[str(ctx.guild.id)]
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
    db[str(ctx.guild.id)] = questions

    
#Main game
@client.command(description = "Play the game! \nNo arguments.")
async def play(ctx):
    if str(ctx.guild.id) not in db.keys():
        prefixes = db["prefixes"]
        await ctx.send("No questions recorded yet. Use the '" + prefixes[str(ctx.guild.id)] + "addquestion' command.")
        return
    
    sentences = db[str(ctx.guild.id)]
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
    if str(ctx.guild.id) not in delays:
        delays[str(ctx.guild.id)] = 20
    
    time.sleep(delays[str(ctx.guild.id)])

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

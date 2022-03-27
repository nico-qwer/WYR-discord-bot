import discord
import os
import random
import time
from replit import db
from keep_alive import keep_alive
from discord.utils import get

client = discord.Client()
red_emoji = "🟥"
blue_emoji = "🟦"

if "keywords" not in db.keys():
  db["keywords"] = {}
  
if "add_roles" not in db.keys():
  db["add_roles"] = {}

#Updates the keyword for a server
def update_keyword(keyword, server):
  keywords = db["keywords"]
  keywords[server] = keyword
  db["keywords"] = keywords

#Updates the role needed to add questions
def update_add_role(role, server):
  roles = db["add_roles"]
  roles[server] = role
  db["add_roles"] = roles
  
#Adds a choice in the database
def add_choice(new_sentence, server):
  if server not in db.keys():
    db[server] = []
  sentences = db[server]
  sentences.append(new_sentence)
  db[server] = sentences

#Formats choices like this : ch1-ch2-author
def format_choices(choice1, choice2, author):
  return choice1 + "-" + choice2 + "-" + author

def get_role_from_mention(mention):
  if mention.startswith('<@&') and mention.endswith('>'):
    id = mention[3:-1]
    return int(id)
	


#Fires when the bot is logged in
@client.event
async def on_ready():
  print("Logged in as {0.user}".format(client))
  
  #for guild in client.guilds:
  #  for channel in guild.channels:
  #    if isinstance(channel, discord.TextChannel): # Check if channel is a text channel
  #      await channel.send("I am back online!")

  
#Fires when a message is posted
@client.event
async def on_message(message):
  #Verifies message is not from bot
  if message.author == client.user: return
  
  server = str(message.guild.id)
  guild = message.guild
  
  #Verifies if keyword key exists
  keywords = db["keywords"]
  if server not in keywords:
    keywords[server] = "+"
    db["keywords"] = keywords

  keyword = keywords[server]
  

  #Verifies if message is a keyword
  if not message.content.startswith(keyword):
    return

  #Update keyword
  if message.content.startswith(keyword + "keyword "):
    new_keyword = str(message.content.split(keyword + "keyword ", 1)[1])
    update_keyword(new_keyword, server)
    keyword = new_keyword
    await message.channel.send("Updated keyword to " + new_keyword)

  #Test
  if message.content.startswith(keyword + "test"):
    await message.channel.send("I am working!")

  #Add choice
  if message.content.startswith(keyword + "add"):
    allowed_roles = db["add_roles"]
    role = discord.utils.get(guild.roles, name=allowed_roles[server])
    if role in message.author.roles: #or str(message.author) == "nico_qwer#9317":
      try:
        input = str(message.content.split(keyword + "add ", 1)[1])
      
        choice1 = str(input.split(" - ")[0])
        choice2 = str(input.split(" - ")[1])
        add_choice(format_choices(choice1, choice2, str(message.author)), server)
      except:
        await message.channel.send("Sorry, wrong syntax.")
        
      await message.channel.send("Added choices: "+ choice1 + ", or " + choice2)
    else:
      await message.channel.send("Sorry, you need the " + str(role) + " role to add questions.")

  #Update role necessary to add questions
  if message.content.startswith(keyword + "adrole"):
    if not message.author.guild_permissions.administrator: 
      await message.channel.send("Sorry, you are not an admin.")
      return
      
    raw_role_id = str(message.content.split(keyword + "adrole ", 1)[1])
    role_id = get_role_from_mention(raw_role_id)

    role_name = str(guild.get_role(role_id))
    role = guild.get_role(role_id)
      
    if role != None:
      update_add_role(role_name, server)
      await message.channel.send("Changed add role to {0}.".format(role.mention))
      
    
  #Lists all 
  if message.content.startswith(keyword + "list"):
    questions = db[server]

    embed = discord.Embed(title="Listing all recorded questions:", colour=0xAD00AD)
    i = 1
    for sentence in questions:
      choice1 = sentence.split("-")[0]
      choice2 = sentence.split("-")[1]
      author = sentence.split("-")[2]

      embed.add_field(name=str(i), value= choice1 + ", or " + choice2 + ", made by " + author, inline=False)
      i = i + 1
      
    await message.channel.send(embed=embed)
  
  #Delete question
  if message.content.startswith(keyword + "del"):
    
    questions = db[server]
    string_indexes = message.content.split(keyword + "del ", 1)[1]
    array_string_indexes = string_indexes.split(" ")
    indexes = []
    for number in array_string_indexes:
      int_num = int(number)
      indexes.append(int_num)
    
    for index in indexes:
      if index > len(questions): 
        await message.channel.send(index + " was removed because it was not in the questions.")
        indexes.remove(index)
    
    embed = discord.Embed(title="Deleted questions:", colour=0xAD00AD)
    for question in questions:
      print(questions.index(question) + 1)
      if questions.index(question) + 1 in indexes:
        choice1 = question.split("-")[0]
        choice2 = question.split("-")[1]
        author = question.split("-")[2]
        
        embed.add_field(name=str(index), value= choice1 + ", or " + choice2 + ", made by " + author, inline=False)
        questions.pop(index - 1)
      
    await message.channel.send(embed=embed)
    db[server] = questions
    
  #Main game
  if message.content.startswith(keyword + "play"):
    if server not in db.keys():
      await message.channel.send("No questions recorded yet. Use the '" + keyword + "add' command.")
    sentences = db[server]
    non_formated_chosen = random.choice(sentences)
    
    choice1 = non_formated_chosen.split("-")[0]
    choice2 = non_formated_chosen.split("-")[1]
    author = non_formated_chosen.split("-")[2]

    embed = discord.Embed(title="Would you rather:", colour=0xAD00AD)
    embed.add_field(name="Choice 1", value= red_emoji + " : " + choice1, inline=False)
    embed.add_field(name="Choice 2", value= blue_emoji + " : " + choice2, inline=False)
    embed.set_footer(text="Question by " + author)

    current = await message.channel.send(embed=embed)
    
    await current.add_reaction(red_emoji)
    await current.add_reaction(blue_emoji)

    time.sleep(5)

    new_current = await current.channel.fetch_message(current.id)
    
    red_reactions = get(new_current.reactions, emoji=red_emoji).count
    blue_reactions = get(new_current.reactions, emoji=blue_emoji).count

    if red_reactions > blue_reactions:
      await new_current.channel.send("More people would rather " + choice1 + " than " + choice2 + "!")
    elif red_reactions < blue_reactions:
      await new_current.channel.send("More people would rather " + choice2 + " than " + choice1 + "!")
    
keep_alive()
client.run(os.environ['TOKEN'])

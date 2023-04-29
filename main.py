import os
import typing
import discord
import functools
from discord import app_commands
from discord.ext import commands
from asyncio import run_coroutine_threadsafe

import utils
import config

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())
bot.remove_command('help')

bot.vc = {}
bot.is_playing = {}
bot.is_paused = {}
bot.queue_status = {}
bot.ffmpeg_Process = {}
bot.last_message = {}
bot.current_song = {}
bot.embedColor = 0x875ae6

@bot.event
async def on_ready():
	print("Total servers:")
	try:
		synced = await bot.tree.sync()
		print(f"Synced {len(synced)} Slash commands.")
	except Exception as e:
		print(e)

	for guild in bot.guilds:
		id = int(guild.id)
		print(id)
		bot.vc[id] = None
		bot.is_paused[id] = bot.is_playing[id] = False
		bot.queue_status[id] = []
		bot.ffmpeg_Process[id] = None
		bot.last_message[id] = None
		bot.current_song[id] = None
	print("Bot up")

@bot.event
async def on_guild_join(guild):
	id = int(guild.id)
	print(f"Joined server: {str(id)}")
	bot.vc[id] = None
	bot.is_paused[id] = bot.is_playing[id] = False
	bot.queue_status[id] = []
	bot.ffmpeg_Process[id] = None
	bot.last_message[id] = None
	bot.current_song[id] = None

@bot.event
async def on_guild_remove(guild):
	id = int(guild.id)
	print(f"Left server: {str(id)}")
	if bot.vc[id] != None:
		
		if bot.is_paused[id] == True and bot.ffmpeg_Process[id] != None:
			bot.queue_status[id] = []
			bot.vc[id].resume()
			utils.kill_process(bot.ffmpeg_Process[id])

		elif bot.is_playing[id] == True and bot.ffmpeg_Process[id] != None:
			bot.queue_status[id] = []
			utils.kill_process(bot.ffmpeg_Process[id])

		else:
			pass

	else:
		bot.vc[id] = None
		bot.is_paused[id] = bot.is_playing[id] = False
		bot.queue_status[id] = []
		bot.ffmpeg_Process[id] = None
		bot.last_message[id] = None
		bot.current_song[id] = None


@bot.event
async def on_voice_state_update(member, before, after):
	id = int(member.guild.id)
	if member.id != bot.user.id and before.channel != None and after.channel != before.channel:
		voiceChannelMembers = before.channel.members
		
		if len(voiceChannelMembers) == 1 and voiceChannelMembers[0].id == bot.user.id and bot.vc[id].is_connected():

			if bot.is_paused[id] == True and bot.ffmpeg_Process[id] != None:
				bot.queue_status[id] = []
				bot.vc[id].resume()
				utils.kill_process(bot.ffmpeg_Process[id])

			elif bot.is_playing[id] == True and bot.ffmpeg_Process[id] != None:
				bot.queue_status[id] = []
				utils.kill_process(bot.ffmpeg_Process[id])

			else:
				pass
		else:
			pass
	else:
		pass

def getDuration(seconds):
	seconds = int(seconds)
	m, s = divmod(seconds, 60)
	if seconds >= 3600:
		h, m = divmod(m, 60)
		track_length = f"{h:d}:{m:02d}:{s:02d}"
		return track_length
	else:
		track_length = f"{m:02d}:{s:02d}"
		return track_length

def now_playing_embed(trackData):
	track_title = trackData['title']
	track_url = trackData['url']
	thumbnail = trackData['thumbnail']
	seconds = trackData['duration']
	author = trackData['added_by']
	track_length = getDuration(seconds)

	embed = discord.Embed(
		title="Currently Playing",
		description=f'[{track_title}]({track_url})',
		colour=bot.embedColor, 
	)
	embed.set_thumbnail(url=thumbnail)
	embed.add_field(name=f"**Song Requested By: {str(author)}**", value="", inline=True)
	embed.set_footer(text=f"Track Duration: {track_length}")
	return embed

def track_add_embed(ctx, trackData):
	track_title = trackData['title']
	track_url = trackData['url']
	seconds = trackData['duration']
	track_length = getDuration(seconds)

	embed = discord.Embed(
		title="Song Added To Queue!",
		description=f'[{track_title}]({track_url})',
		colour=bot.embedColor, 
	)
	embed.add_field(name=f"**Song Added By: **{ctx.user}", value="", inline=False)
	embed.set_footer(text=f"Track Duration: {track_length}")
	return embed

def pause_embed(ctx, trackData):
	track_title = trackData['title']
	track_url = trackData['url']
	thumbnail = trackData['thumbnail']

	embed = discord.Embed(
		title="Song Paused!",
		description=f'[{track_title}]({track_url})',
		colour=bot.embedColor, 
	)
	embed.add_field(name=f"**Paused By: ** {ctx.user}", value="", inline=True)
	embed.set_thumbnail(url=thumbnail)
	return embed

def resume_embed(ctx, trackData):
	track_title = trackData['title']
	track_url = trackData['url']
	thumbnail = trackData['thumbnail']
	seconds = trackData['duration']
	track_length = getDuration(seconds)

	embed = discord.Embed(
		title="Song Resumed!",
		description=f'[{track_title}]({track_url})',
		colour=bot.embedColor, 
	)
	embed.add_field(name=f"**Resumed By: **{ctx.user}", value="", inline=False)
	embed.set_footer(text=f"Duration: {track_length}")
	embed.set_thumbnail(url=thumbnail)
	return embed

def skip_embed(ctx):

	embed = discord.Embed(
			description=f"**Track skipped by: **{ctx.user.mention}",
			colour=bot.embedColor
	)
	return embed

def leave_embed(ctx):

	embed = discord.Embed(
		description=f"**Music stopped by:** {ctx.user.mention}",
		colour=bot.embedColor
	)
	return embed

def common_embed(message):

	embed = discord.Embed(
			description=message,
			colour=bot.embedColor
	)
	return embed

def queue_embed(queueList):

	# tabSpace = "\u200b"*8
	content = "`Queue`\u1CBC\u1CBC\u1CBC\u1CBC`Duration`\u1CBC\u1CBC\u1CBC\u1CBC\u1CBC\u1CBC`Title`\n\n"
	i = 1
	for song in queueList:
		x = "\u1CBC\u1CBC\u1CBC\u1CBC\u1CBC\u1CBC\u1CBC".join([f"`#{i}`", f"`{getDuration(song['duration'])}`", f"{song['title']}", '\n'])
		content = content + x
		i = i+1

	embed = discord.Embed(
		title="Next songs in the Queue:",
		description=content,
		colour=bot.embedColor, 
	)
	return embed

def play_music(ctx):

	id = int(ctx.guild.id)
	bot.ffmpeg_Process[id] = None
	rm_track = utils.deleteTrack(str(id))


	if bot.queue_status[id] == []:
		bot.is_paused[id] = bot.is_playing[id] = False
		
		msg = "**Queue Cleared, Disconnected from VC**"
		e_msg = common_embed(msg)
		coro = ctx.channel.send(embed=e_msg)	
		fut = run_coroutine_threadsafe(coro, bot.loop)
		try:
			fut.result()
		except:
			pass

		coro = bot.vc[id].disconnect()
		fut = run_coroutine_threadsafe(coro, bot.loop)	
		try:
			fut.result()
		except:
			pass

		bot.vc[id] = None
		bot.ffmpeg_Process[id] = None
		bot.current_song[id] = None

	if bot.queue_status[id] != []:

		bot.current_song[id] = bot.queue_status[id].pop(0)
		e_msg = now_playing_embed(bot.current_song[id])
		coro = ctx.channel.send(embed=e_msg)
		fut = run_coroutine_threadsafe(coro, bot.loop)	
		try:
			fut.result()
		except:
			pass

		utils.downloadTrack(bot.current_song[id]['id'], str(id))
		source = discord.FFmpegPCMAudio("rds/"+bot.current_song[id]['id']+"."+str(id)+".webm")
		bot.vc[id].play(source, after=lambda e: play_music(ctx))
		bot.ffmpeg_Process[id] = source._process.pid



async def run_player(play_music: typing.Callable, *args, **kwargs) -> typing.Any:
	func = functools.partial(play_music, *args, **kwargs)
	return await bot.loop.run_in_executor(None, func)


@bot.tree.command(
	name='help',
	description="Describes the usage of the Music bot."
)
async def help(ctx: discord.Interaction):
	await ctx.response.defer(ephemeral=True)
	helpDescription = "\
	**`/play`:** Enter the song name or URL to play.\n \
	**`/fplay`:** Force play the specified song (it clears the previous queue).\n\
	**`/queue`:** Displays all the songs in the queue.\n\
	**`/skip`:** Skip to the next song in the queue.\n\
	**`/pause`:** Pause the playback of the song.\n\
	**`/resume`:** Resume the playback if its paused.\n\
	**`/leave`:** Clears the queue and disconnects from Voice Channel.\n\
	**`/help`:** Describes the usage of the Music bot."

	helpEmbed = discord.Embed(
			title="Music Bot Commands:",
			description=helpDescription,
			colour=bot.embedColor,
		) 
	await ctx.followup.send(embed=helpEmbed)


@bot.tree.command(
	name='play',
	description="To play a song"
)
@app_commands.describe(query="Enter Song Name/URL")
async def play(ctx: discord.Interaction, query: str):
	await ctx.response.defer()
	id = int(ctx.guild.id)
	track = utils.checkArgs(query)

	if ctx.user.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif track['error'] != '':
		e_msg = f"**{track['error']}, Please type /help for usage.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	else:
		if bot.vc[id] == None:
			bot.vc[id] = await ctx.user.voice.channel.connect()
		else:
			pass

		if len(bot.queue_status[id]) >= 50:
			e_msg = "**Queue is full, try after the current song.**"
			e_msg = common_embed(e_msg)
			bot.last_messsage[id] = await ctx.followup.send(embed=e_msg)
			return
		
		else:
			if bot.queue_status[id] == [] and bot.is_playing[id] == False and bot.is_paused[id] == False:
				e_msg = "**Queue Initiated and song added to queue.**"
				e_msg = common_embed(e_msg)
				bot.last_message[id] = await ctx.followup.send(embed=e_msg)

				track = utils.getTrack(track['id'])
				track['added_by'] = ctx.user

				bot.queue_status[id].append(track)
				bot.is_playing[id] = True 
				await run_player(play_music, ctx)

			else:
				track = utils.getTrack(track['id'])
				track['added_by'] = ctx.user				

				bot.queue_status[id].append(track)
				e_msg = track_add_embed(ctx, track)
				bot.last_message[id] = await ctx.followup.send(embed=e_msg)
				pass

@bot.tree.command(
	name='fplay',
	description="To Force play a song."
)
@app_commands.describe(query="Enter Song Name/URL")
async def fplay(ctx: discord.Interaction, query: str):
	await ctx.response.defer()
	id = int(ctx.guild.id)
	track = utils.checkArgs(query)

	if ctx.user.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif track['error'] != '':
		e_msg = f"**{track['error']}, Please type /help for usage.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	else:
		if bot.vc[id] == None:
			bot.vc[id] = await ctx.user.voice.channel.connect()
		else:
			pass
				
		if bot.queue_status[id] == [] and bot.is_playing[id] == False and bot.is_paused[id] == False:
			e_msg = "**Queue Initiated and song added to queue.**"
			e_msg = common_embed(e_msg)
			bot.last_message[id] = await ctx.followup.send(embed=e_msg)

			track = utils.getTrack(track['id'])
			track['added_by'] = ctx.user

			bot.queue_status[id].append(track)
			bot.is_playing[id] = True 
			await run_player(play_music, ctx)

		elif bot.is_playing[id] == True and bot.ffmpeg_Process[id] != None:

			e_msg = "**New Queue Initiated and song added to queue.**"
			e_msg = common_embed(e_msg)
			bot.last_message[id] = await ctx.followup.send(embed=e_msg)

			track = utils.getTrack(track['id'])
			track['added_by'] = ctx.user
			bot.queue_status[id] = []
			bot.queue_status[id].append(track)
			utils.kill_process(bot.ffmpeg_Process[id])

		elif bot.is_paused[id] == True and bot.ffmpeg_Process[id] != None:

			e_msg = "**New Queue Initiated and song added to queue.**"
			e_msg = common_embed(e_msg)
			bot.last_message[id] = await ctx.followup.send(embed=e_msg)

			track = utils.getTrack(track['id'])
			track['added_by'] = ctx.user
			bot.queue_status[id] = []
			bot.queue_status[id].append(track)
			bot.is_paused[id] = False
			bot.is_playing[id] = True
			bot.vc[id].resume()
			utils.kill_process(bot.ffmpeg_Process[id])

		else:
			pass

@bot.tree.command(
	name='skip',
	description="Skip to the next song in the queue."
)
async def skip(ctx: discord.Interaction):
	await ctx.response.defer()
	id = int(ctx.guild.id)

	if ctx.user.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return
	
	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif bot.vc[id] == None:
		e_msg = "**You need to play some music first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	else:
		pass

	if bot.is_playing[id] == True and bot.ffmpeg_Process[id] != None:
		e_msg = skip_embed(ctx)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg)		
		utils.kill_process(bot.ffmpeg_Process[id])

	elif bot.is_paused[id] == True and bot.ffmpeg_Process[id] != None:
		e_msg = skip_embed(ctx)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg)		
		bot.is_paused[id] = False
		bot.is_playing[id] = True
		bot.vc[id].resume()
		utils.kill_process(bot.ffmpeg_Process[id])
		
	else:
		pass

@bot.tree.command(
	name='pause',
	description="Pause the playback of the song."
)
async def pause(ctx: discord.Interaction):
	await ctx.response.defer()
	id = int(ctx.guild.id)

	if ctx.user.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif bot.vc[id] == None:
		e_msg = "**You need to play some music first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	else:
		pass

	if bot.is_paused[id] == True:
		e_msg = "**Music is already paused.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg)
		return

	elif bot.is_playing[id] == True:
		bot.is_playing[id] = False
		bot.is_paused[id] = True
		bot.vc[id].pause()
		trackData = bot.current_song[id]
		e_msg = pause_embed(ctx, trackData)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg)
	
	else:
		pass

@bot.tree.command(
	name='resume',
	description="Resume the playback if its paused."
)
async def resume(ctx: discord.Interaction):
	await ctx.response.defer()
	id = int(ctx.guild.id)

	if ctx.user.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif bot.vc[id] == None:
		e_msg = "**You need to play some music first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	else:
		pass

	if bot.is_playing[id] == True:
		e_msg = "**Music is already being played.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg)
		return

	elif bot.is_paused[id] == True:
		bot.is_playing[id] = True
		bot.is_paused[id] = False
		bot.vc[id].resume()
		trackData = bot.current_song[id]
		e_msg = resume_embed(ctx, trackData)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg)
	
	else:
		pass

@bot.tree.command(
	name='leave',
	description="Clears the queue and disconnects from Voice Channel."
)
async def leave(ctx: discord.Interaction):
	await ctx.response.defer()
	id = int(ctx.guild.id)

	if ctx.user.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif bot.vc[id] == None:
		e_msg = "**You need to play some music first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	else:
		pass

	if bot.is_paused[id] == True and bot.ffmpeg_Process[id] != None:
		e_msg = leave_embed(ctx)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg)

		bot.queue_status[id] = []
		bot.vc[id].resume()
		utils.kill_process(bot.ffmpeg_Process[id])

	elif bot.is_playing[id] == True and bot.ffmpeg_Process[id] != None:
		e_msg = leave_embed(ctx)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg)	

		bot.queue_status[id] = []
		utils.kill_process(bot.ffmpeg_Process[id])

	else:
		pass

@bot.tree.command(
	name='queue',
	description="Display all the songs in the queue."
)
async def resume(ctx: discord.Interaction):
	await ctx.response.defer()
	id = int(ctx.guild.id)

	if ctx.user.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	elif bot.vc[id] == None:
		e_msg = "**You need to play some music first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

	else:
		pass
	
	if bot.queue_status[id] == []:
		e_msg = "**Queue is empty, add songs by /play command.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return
	
	elif bot.queue_status[id] != []:
		e_msg = queue_embed(bot.queue_status[id])
		bot.last_message[id] = await ctx.followup.send(embed=e_msg, ephemeral=True)
		return

bot.run(config.BOT_TOKEN)
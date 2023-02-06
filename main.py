import os
import typing
import discord
import functools
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
	print("Total server ids:")
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

def now_playing_embed(trackData):
	track_title = trackData['title']
	track_url = trackData['url']
	thumbnail = trackData['thumbnail']
	seconds = trackData['duration']
	author = trackData['added_by']

	m, s = divmod(seconds, 60)
	if seconds >= 3600:
		h, m = divmod(m, 60)
		track_length = f"{h:d}:{m:02d}:{s:02d}"
	else:
		track_length = f"{m:02d}:{s:02d}"

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

	m, s = divmod(seconds, 60)
	if seconds >= 3600:
		h, m = divmod(m, 60)
		track_length = f"{h:d}:{m:02d}:{s:02d}"
	else:
		track_length = f"{m:02d}:{s:02d}"

	embed = discord.Embed(
		title="Song Added To Queue!",
		description=f'[{track_title}]({track_url})',
		colour=bot.embedColor, 
	)
	embed.add_field(name=f"**Song Added By: **{ctx.author}", value="", inline=False)
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
	embed.add_field(name=f"**Paused By: ** {ctx.author}", value="", inline=True)
	embed.set_thumbnail(url=thumbnail)
	return embed

def resume_embed(ctx, trackData):
	track_title = trackData['title']
	track_url = trackData['url']
	thumbnail = trackData['thumbnail']
	seconds = trackData['duration']

	m, s = divmod(seconds, 60)
	if seconds >= 3600:
		h, m = divmod(m, 60)
		track_length = f"{h:d}:{m:02d}:{s:02d}"
	else:
		track_length = f"{m:02d}:{s:02d}"

	embed = discord.Embed(
		title="Song Resumed!",
		description=f'[{track_title}]({track_url})',
		colour=bot.embedColor, 
	)
	embed.add_field(name=f"**Resumed By: **{ctx.author}", value="", inline=False)
	embed.set_footer(text=f"Duration: {track_length}")
	embed.set_thumbnail(url=thumbnail)
	return embed

def skip_embed(ctx):

	embed = discord.Embed(
			description=f"**Track skipped by: **{ctx.author.mention}",
			colour=bot.embedColor
	)
	return embed

def common_embed(message):

	embed = discord.Embed(
			description=message,
			colour=bot.embedColor
	)
	return embed

def play_music(ctx):

	id = int(ctx.guild.id)
	bot.ffmpeg_Process[id] = None
	rm_track = utils.deleteTrack(str(id))


	if bot.queue_status[id] == []:
		bot.is_paused[id] = bot.is_playing[id] = False
		
		msg = "**Queue is empty. Disconnected from VC**"
		e_msg = common_embed(msg)
		coro = ctx.send(embed=e_msg)	
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
		coro = ctx.send(embed=e_msg)
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


@bot.command(
	name='help',
	help="Describes the usage of the Music bot."
)
async def help(ctx):

	helpDescription = "\
	**`/play`:** Enter the song name or URL to play.\n \
	**`/fplay`:** Force play the specified song (it clears the previous queue).\n\
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
	await ctx.reply(embed=helpEmbed, mention_author=False)


@bot.command(
	name='play',
	help="Plays a song, you need to specify the song name or its youtube link."
)
async def play(ctx, *args):

	query = " ".join(args)
	id = int(ctx.guild.id)
	track = utils.checkArgs(query)

	if ctx.author.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif track['error'] != '':
		e_msg = f"**{track['error']}, Please type /help for usage.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif bot.vc[id] != None and ctx.author.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	else:
		if bot.vc[id] == None:
			bot.vc[id] = await ctx.author.voice.channel.connect()
		else:
			pass

		track = utils.getTrack(track['id'])
		track['added_by'] = ctx.author

		if len(bot.queue_status[id]) >= 50:
			e_msg = "**Queue is full, try after the current song.**"
			e_msg = common_embed(e_msg)
			bot.last_messsage[id] = await ctx.reply(embed=e_msg, mention_author=False)
			return
		
		else:
			if bot.queue_status[id] == [] and bot.is_playing[id] == False and bot.is_paused[id] == False:
				bot.queue_status[id].append(track)
				bot.is_playing[id] = True 
				await run_player(play_music, ctx)

			else:
				bot.queue_status[id].append(track)
				e_msg = track_add_embed(ctx, track)
				bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
				pass

@bot.command(
	name='fplay',
	help="Force play the specified song."
)
async def fplay(ctx, *args):

	query = " ".join(args)
	id = int(ctx.guild.id)
	track = utils.checkArgs(query)

	if ctx.author.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif track['error'] != '':
		e_msg = f"**{track['error']}, Please type /help for usage.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif bot.vc[id] != None and ctx.author.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	else:
		if bot.vc[id] == None:
			bot.vc[id] = await ctx.author.voice.channel.connect()
		else:
			pass

		track = utils.getTrack(track['id'])
		track['added_by'] = ctx.author
				
		if bot.queue_status[id] == [] and bot.is_playing[id] == False and bot.is_paused[id] == False:
			bot.queue_status[id].append(track)
			bot.is_playing[id] = True 
			await run_player(play_music, ctx)

		elif bot.is_playing[id] == True and bot.ffmpeg_Process[id] != None:
			bot.queue_status[id] = []
			bot.queue_status[id].append(track)
			utils.kill_process(bot.ffmpeg_Process[id])

		elif bot.is_paused[id] == True and bot.ffmpeg_Process[id] != None:
			bot.queue_status[id] = []
			bot.queue_status[id].append(track)
			bot.is_paused[id] = False
			bot.is_playing[id] = True
			bot.vc[id].resume()
			utils.kill_process(bot.ffmpeg_Process[id])

		else:
			pass

@bot.command(
	name='skip',
	help="Skip to the next song in the queue."
)
async def skip(ctx):

	id = int(ctx.guild.id)

	if ctx.author.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return
	
	elif bot.vc[id] != None and ctx.author.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif bot.vc[id] == None:
		e_msg = "**You need to play some music first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	else:
		pass

	if bot.is_playing[id] == True and bot.ffmpeg_Process[id] != None:
		e_msg = skip_embed(ctx)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)		
		utils.kill_process(bot.ffmpeg_Process[id])

	elif bot.is_paused[id] == True and bot.ffmpeg_Process[id] != None:
		e_msg = skip_embed(ctx)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)		
		bot.is_paused[id] = False
		bot.is_playing[id] = True
		bot.vc[id].resume()
		utils.kill_process(bot.ffmpeg_Process[id])
		
	else:
		pass

@bot.command(
	name='pause',
	help="Pause the playback of the song."
)
async def pause(ctx):
	id = int(ctx.guild.id)

	if ctx.author.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif bot.vc[id] != None and ctx.author.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif bot.vc[id] == None:
		e_msg = "**You need to play some music first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	else:
		pass

	if bot.is_paused[id] == True:
		e_msg = "**Music is already paused.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif bot.is_playing[id] == True:
		bot.is_playing[id] = False
		bot.is_paused[id] = True
		bot.vc[id].pause()
		trackData = bot.current_song[id]
		e_msg = pause_embed(ctx, trackData)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
	
	else:
		pass

@bot.command(
	name='resume',
	help="Resume the playback if its paused."
)
async def resume(ctx):
	id = int(ctx.guild.id)

	if ctx.author.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif bot.vc[id] != None and ctx.author.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif bot.vc[id] == None:
		e_msg = "**You need to play some music first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	else:
		pass

	if bot.is_playing[id] == True:
		e_msg = "**Music is already being played.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif bot.is_paused[id] == True:
		bot.is_playing[id] = True
		bot.is_paused[id] = False
		bot.vc[id].resume()
		trackData = bot.current_song[id]
		e_msg = resume_embed(ctx, trackData)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
	
	else:
		pass

@bot.command(
	name='leave',
	help="Clears the queue and disconnects from Voice Channel."
)
async def leave(ctx):
	id = int(ctx.guild.id)

	if ctx.author.voice is None:
		e_msg = "**You need to join VC first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif bot.vc[id] != None and ctx.author.voice.channel != bot.vc[id].channel:
		e_msg = "**Please join the VC of the Bot.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	elif bot.vc[id] == None:
		e_msg = "**You need to play some music first.**"
		e_msg = common_embed(e_msg)
		bot.last_message[id] = await ctx.reply(embed=e_msg, mention_author=False)
		return

	else:
		pass

	if bot.is_paused[id] == True and bot.ffmpeg_Process[id] != None:
		bot.queue_status[id] = []
		bot.vc[id].resume()
		utils.kill_process(bot.ffmpeg_Process[id])

	elif bot.is_playing[id] == True and bot.ffmpeg_Process[id] != None:
		bot.queue_status[id] = []
		utils.kill_process(bot.ffmpeg_Process[id])

	else:
		pass

bot.run(config.BOT_TOKEN)
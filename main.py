import typing
import discord
import functools
from discord import app_commands
from discord.ext import commands
from asyncio import run_coroutine_threadsafe
from pathlib import Path

import utils
from embeds import *


config = utils.Config()
if config.spotify != True:
	print("Spotify Support Excluded.")
else:
	config.setupSpotifyClient()

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
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


def play_music(ctx):

	id = int(ctx.guild.id)
	bot.ffmpeg_Process[id] = None
	rm_track = utils.deleteTrack(str(id), config.DOWNLOAD_DIR)


	if bot.queue_status[id] == []:
		bot.is_paused[id] = bot.is_playing[id] = False
		
		coro = ctx.channel.send(embed=common_embed("**Queue Cleared, Disconnected from VC**"))	
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
		coro = ctx.channel.send(embed=now_playing_embed(bot.current_song[id]))
		fut = run_coroutine_threadsafe(coro, bot.loop)	
		try:
			fut.result()
		except:
			pass

		dl_loc = utils.downloadTrack(bot.current_song[id], str(id), config.DOWNLOAD_DIR)
		if dl_loc is None:
			coro = ctx.channel.send(embed=common_embed("**Skipped the track due to download error.**"))
			fut = run_coroutine_threadsafe(coro, bot.loop)	
			try:
				fut.result()
			except:
				pass
			
			print(f"Download Error: {bot.current_song[id]['track_id']}, platform: {bot.current_song[id]['track_platform']}")
			play_music(ctx)
		else:
			source = discord.FFmpegPCMAudio(str(dl_loc))
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
	query_bundle = utils.parse_args(query)

	if ctx.user.voice is None:
		bot.last_message[id] = await ctx.followup.send(embed=common_embed("**You need to join VC first.**"), ephemeral=True)
		return

	elif query_bundle['error'] is not None:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed(f"**{query_bundle['message']}, Please type /help for usage.**"), ephemeral=True)
		return

	elif query_bundle['platform'] == 'spotify' and config.spotify != True:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**Spotify support is exclueded by Admin. Please type the name of the song.**"), ephemeral=True)
		return

	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		bot.last_message[id] = await ctx.followup.send(embed=common_embed("**Please join the VC of the Bot.**"), ephemeral=True)
		return

	else:
		if bot.vc[id] == None:
			bot.vc[id] = await ctx.user.voice.channel.connect()
		else:
			pass

		if len(bot.queue_status[id]) >= 100:
			bot.last_messsage[id] = await ctx.followup.send(embed=common_embed("**Queue is full, try again after few songs.**"))
			return
		
		else:
			bundle = utils.getTrack(query_bundle)
			if bundle['bundle_type'] == 'single_track':
				if bundle['songs'] == []:
					bot.last_message[id] = await ctx.followup.send(
						embed=common_embed("**Unable to extract song info. Please try again later.**"))
					return
				else:
					bundle['to_be_added'] = bundle['songs']
					bot.last_message[id] = await ctx.followup.send(embed=track_add_embed(ctx, bundle))
			
			if bundle['bundle_type'] == 'playlist_info':
				if bundle['playlist_data']['playlist_items'] == []:
					bot.last_message[id] = await ctx.followup.send(
						embed=common_embed("**Unable to extract songs from the playlist. Please add the songs manually.**"))
					return
				else:
					bundle['to_be_added'] = bundle['playlist_data']['playlist_items']
					if 100 - len(bot.queue_status[id]) > len(bundle['to_be_added']):
						avl_length = len(bundle['to_be_added'])
					else:
						avl_length = 100 - len(bot.queue_status[id])
					bot.last_message[id] = await ctx.followup.send(embed=track_add_embed(ctx, bundle, avl_length))
			
			if bundle['bundle_type'] == 'album_info':
				if bundle['album_data']['album_items'] == []:
					bot.last_message[id] = await ctx.followup.send(
						embed=common_embed("**Unable to extract songs from the album. Please add the songs manually.**"))
					return
				else:
					bundle['to_be_added'] = bundle['album_data']['album_items']
					if 100 - len(bot.queue_status[id]) > len(bundle['to_be_added']):
						avl_length = len(bundle['to_be_added'])
					else:
						avl_length = 100 - len(bot.queue_status[id])
					bot.last_message[id] = await ctx.followup.send(embed=track_add_embed(ctx, bundle, avl_length))
				

			if bot.queue_status[id] == [] and bot.is_playing[id] == False and bot.is_paused[id] == False:
				for track in bundle['to_be_added']:
					if len(bot.queue_status[id]) <= 100:
						track['added_by'] = ctx.user
						bot.queue_status[id].append(track)
					else:
						break

				bot.is_playing[id] = True 
				await run_player(play_music, ctx)

			else:
				for track in bundle['to_be_added']:
					if len(bot.queue_status[id]) <= 100:
						track['added_by'] = ctx.user
						bot.queue_status[id].append(track)
					else:
						break
				pass

@bot.tree.command(
	name='fplay',
	description="To Force play a song."
)
@app_commands.describe(query="Enter Song Name/URL")
async def fplay(ctx: discord.Interaction, query: str):
	await ctx.response.defer()
	id = int(ctx.guild.id)
	query_bundle = utils.parse_args(query)

	if ctx.user.voice is None:
		bot.last_message[id] = await ctx.followup.send(embed=common_embed("**You need to join VC first.**"), ephemeral=True)
		return

	elif query_bundle['error'] is not None:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed(f"**{query_bundle['message']}, Please type /help for usage.**"), ephemeral=True)
		return

	elif query_bundle['platform'] == 'spotify' and config.spotify != True:
		bot.last_message[id] = await ctx.followup.send(embed=common_embed(
			"**Spotify support is exclueded by Admin. Please type the name of the song.**"
			), ephemeral=True)
		return

	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		bot.last_message[id] = await ctx.followup.send(embed=common_embed("**Please join the VC of the Bot.**"), ephemeral=True)
		return

	else:
		if bot.vc[id] == None:
			bot.vc[id] = await ctx.user.voice.channel.connect()
		else:
			pass

		bundle = utils.getTrack(query_bundle)
		if bundle['bundle_type'] == 'single_track':
			if bundle['songs'] == []:
				bot.last_message[id] = await ctx.followup.send(
					embed=common_embed("**Unable to extract song info. Please try again later.**"))
				return
			else:
				bundle['to_be_added'] = bundle['songs']
				bot.last_message[id] = await ctx.followup.send(embed=track_add_embed(ctx, bundle))
		
		if bundle['bundle_type'] == 'playlist_info':
			if bundle['playlist_data']['playlist_items'] == []:
				bot.last_message[id] = await ctx.followup.send(
					embed=common_embed("**Unable to extract songs from the playlist. Please add the songs manually.**"))
				return
			else:
				bundle['to_be_added'] = bundle['playlist_data']['playlist_items']
				bot.last_message[id] = await ctx.followup.send(embed=track_add_embed(ctx, bundle, len(bundle['to_be_added'])))
		
		if bundle['bundle_type'] == 'album_info':
			if bundle['album_data']['album_items'] == []:
				bot.last_message[id] = await ctx.followup.send(
					embed=common_embed("**Unable to extract songs from the album. Please add the songs manually.**"))
				return
			else:
				bundle['to_be_added'] = bundle['album_data']['album_items']
				bot.last_message[id] = await ctx.followup.send(embed=track_add_embed(ctx, bundle, len(bundle['to_be_added'])))


		if bot.queue_status[id] == [] and bot.is_playing[id] == False and bot.is_paused[id] == False:
			for track in bundle['to_be_added']:
				if len(bot.queue_status[id]) <= 100:
					track['added_by'] = ctx.user
					bot.queue_status[id].append(track)
				else:
					break

			bot.is_playing[id] = True 
			await run_player(play_music, ctx)

		elif bot.is_playing[id] == True and bot.ffmpeg_Process[id] != None:
			bot.queue_status[id] = []
			for track in bundle['to_be_added']:
				if len(bot.queue_status[id]) <= 100:
					track['added_by'] = ctx.user
					bot.queue_status[id].append(track)
				else:
					break
			utils.kill_process(bot.ffmpeg_Process[id])

		elif bot.is_paused[id] == True and bot.ffmpeg_Process[id] != None:
			bot.queue_status[id] = []
			for track in bundle['to_be_added']:
				if len(bot.queue_status[id]) <= 100:
					track['added_by'] = ctx.user
					bot.queue_status[id].append(track)
				else:
					break
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
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**You need to join VC first.**"), ephemeral=True)
		return
	
	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**Please join the VC of the Bot.**"), ephemeral=True)
		return

	elif bot.vc[id] == None:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**You need to play some music first.**"), ephemeral=True)
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
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**You need to join VC first.**"), ephemeral=True)
		return

	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**Please join the VC of the Bot.**"), ephemeral=True)
		return

	elif bot.vc[id] == None:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**You need to play some music first.**"), ephemeral=True)
		return

	else:
		pass

	if bot.is_paused[id] == True:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**Music is already paused.**"))
		return

	elif bot.is_playing[id] == True:
		bot.is_playing[id] = False
		bot.is_paused[id] = True
		bot.vc[id].pause()
		trackData = bot.current_song[id]
		bot.last_message[id] = await ctx.followup.send(embed=pause_embed(ctx, trackData))
	
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
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**You need to join VC first.**"), ephemeral=True)
		return

	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**Please join the VC of the Bot.**"), ephemeral=True)
		return

	elif bot.vc[id] == None:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**You need to play some music first.**"), ephemeral=True)
		return

	else:
		pass

	if bot.is_playing[id] == True:
		bot.last_message[id] = await ctx.followup.send(embed=common_embed("**Music is already being played.**"))
		return

	elif bot.is_paused[id] == True:
		bot.is_playing[id] = True
		bot.is_paused[id] = False
		bot.vc[id].resume()
		trackData = bot.current_song[id]
		bot.last_message[id] = await ctx.followup.send(embed=resume_embed(ctx, trackData))
	
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
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**You need to join VC first.**"), ephemeral=True)
		return

	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**Please join the VC of the Bot.**"), ephemeral=True)
		return

	elif bot.vc[id] == None:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**You need to play some music first.**"), ephemeral=True)
		return

	else:
		pass

	if bot.is_paused[id] == True and bot.ffmpeg_Process[id] != None:
		bot.last_message[id] = await ctx.followup.send(embed=leave_embed(ctx))

		bot.queue_status[id] = []
		bot.vc[id].resume()
		utils.kill_process(bot.ffmpeg_Process[id])

	elif bot.is_playing[id] == True and bot.ffmpeg_Process[id] != None:
		bot.last_message[id] = await ctx.followup.send(embed=leave_embed(ctx))	

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
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**You need to join VC first.**"), ephemeral=True)
		return

	elif bot.vc[id] != None and ctx.user.voice.channel != bot.vc[id].channel:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**Please join the VC of the Bot.**"), ephemeral=True)
		return

	elif bot.vc[id] == None:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**You need to play some music first.**"), ephemeral=True)
		return

	else:
		pass
	
	if bot.queue_status[id] == []:
		bot.last_message[id] = await ctx.followup.send(
			embed=common_embed("**Queue is empty, add songs by /play command.**"), ephemeral=True)
		return
	
	elif bot.queue_status[id] != []:
		bot.last_message[id] = await ctx.followup.send(embed=queue_embed(bot.queue_status[id]), ephemeral=True)
		return

bot.run(config.BOT_TOKEN)
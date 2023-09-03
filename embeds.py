import discord
from utils import getDuration

EMBED_COLOR = 0x875ae6


def now_playing_embed(trackBundle):
	track_title = trackBundle['title']
	track_url = trackBundle['track_url']
	thumbnail = trackBundle['thumbnail_url']
	seconds = trackBundle['duration']
	author = trackBundle['added_by']
	track_length = getDuration(seconds)

	embed = discord.Embed(
		title="Currently Playing",
		description=f'[{track_title}]({track_url})',
		colour=EMBED_COLOR, 
	)
	embed.set_thumbnail(url=thumbnail)
	embed.add_field(name=f"**Song Requested By: {str(author)}**", value="", inline=True)
	embed.set_footer(text=f"Track Duration: {track_length}")
	return embed

def track_add_embed(ctx, bundle, avl_length=None):

	if bundle['bundle_type'] == 'single_track':
		title = bundle['songs'][0]['title']
		url = bundle['songs'][0]['track_url']
		length = getDuration(bundle['songs'][0]['duration'])

		embed = discord.Embed(
			title="Song Added To Queue!",
			description=f'[{title}]({url})',
			colour=EMBED_COLOR, 
		)
		embed.add_field(name=f"**Song Added By: **{ctx.user}", value="", inline=False)
		embed.set_footer(text=f"Track Duration: {length}")
	
	if bundle['bundle_type'] == 'playlist_info':
		title = bundle['playlist_data']['title']
		url = bundle['playlist_data']['url']
		length = str(avl_length)

		embed = discord.Embed(
			title="Spotify Playlist Added To Queue!",
			description=f'[{title}]({url})',
			colour=EMBED_COLOR, 
		)
		embed.add_field(name=f"**Playlist Added By: **{ctx.user}", value="", inline=False)
		embed.set_footer(text=f"Total Songs Added: {length}")

	if bundle['bundle_type'] == 'album_info':
		title = bundle['album_data']['title']
		url = bundle['album_data']['url']
		length = str(avl_length)

		embed = discord.Embed(
			title="Spotify Album Added To Queue!",
			description=f'[{title}]({url})',
			colour=EMBED_COLOR, 
		)
		embed.add_field(name=f"**Album Added By: **{ctx.user}", value="", inline=False)
		embed.set_footer(text=f"Total Songs Added: {length}")

	return embed


def pause_embed(ctx, trackBundle):
	track_title = trackBundle['title']
	track_url = trackBundle['track_url']
	thumbnail = trackBundle['thumbnail_url']

	embed = discord.Embed(
		title="Song Paused!",
		description=f'[{track_title}]({track_url})',
		colour=EMBED_COLOR, 
	)
	embed.add_field(name=f"**Paused By: ** {ctx.user}", value="", inline=True)
	embed.set_thumbnail(url=thumbnail)
	return embed

def resume_embed(ctx, trackBundle):
	track_title = trackBundle['title']
	track_url = trackBundle['track_url']
	thumbnail = trackBundle['thumbnail_url']
	seconds = trackBundle['duration']
	track_length = getDuration(seconds)

	embed = discord.Embed(
		title="Song Resumed!",
		description=f'[{track_title}]({track_url})',
		colour=EMBED_COLOR, 
	)
	embed.add_field(name=f"**Resumed By: **{ctx.user}", value="", inline=False)
	embed.set_footer(text=f"Duration: {track_length}")
	embed.set_thumbnail(url=thumbnail)
	return embed

def skip_embed(ctx):

	embed = discord.Embed(
			description=f"**Track skipped by: **{ctx.user.mention}",
			colour=EMBED_COLOR
	)
	return embed

def leave_embed(ctx):

	embed = discord.Embed(
		description=f"**Music stopped by:** {ctx.user.mention}",
		colour=EMBED_COLOR
	)
	return embed

def common_embed(message):

	embed = discord.Embed(
			description=message,
			colour=EMBED_COLOR
	)
	return embed

def queue_embed(queueList):

	# tabSpace = "\u200b"*8
	content = "`Queue`\u1CBC\u1CBC\u1CBC\u1CBC`Duration`\u1CBC\u1CBC\u1CBC\u1CBC\u1CBC\u1CBC`Title`\n\n"
	i = 1
	for song in queueList:
		if i <= 30:
			x = "\u1CBC\u1CBC\u1CBC\u1CBC\u1CBC\u1CBC\u1CBC".join([f"`#{i}`", f"`{getDuration(song['duration'])}`", f"{song['title']}", '\n'])
			content = content + x
			i = i+1
		else:
			break

	embed = discord.Embed(
		title="Next songs in the Queue:",
		description=content,
		colour=EMBED_COLOR, 
	)
	return embed
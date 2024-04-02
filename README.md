
# Distro

A Discord Music Bot which offers various commands to control the music playback while streaming multiple songs to multiple server simultaneously, besides its quite easy to setup. 

## Supported Platforms
![Supported Platforms](https://imgsaver.com/images/2024/04/01/supported-platforms.png)
- Spotify : Tracks, Playlists, Albums
- Youtube Music : Tracks only
- Youtube : Video only 

## 🚧 Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- [FFmpeg](https://ffmpeg.org/download.html)

> ⚠**Note:** FFmpeg is required for music streaming. You need to add it's path to environmental variables. Make sure it can be accessed by typing `ffmpeg` in your command prompt before running the bot.
## 📝 Installation

Clone this repository to your computer
```bash
git clone https://github.com/chauhantirth/Distro
```
Install the required python packages from the requirements.txt file using: 
```bash
pip install -r requirements.txt
```
Open the `config.py` file and insert required information\
Run the `main.py` file to start the bot.
## ✅ Supported Commands

- `/help`**:** Displays the default Help message for the Bot.
- `/play {Track name/URL}`**:** Plays the Track / Add to Queue.
- `/fplay {Track name/URL}`**:** Force Plays the Track
- `/queue`**:** Displays all the songs in the queue.
- `/skip`**:** Skips the current playing track.
- `/pause`**:** Pause the playback of the track.
- `/resume`**:** Resumes the paused playback.
- `/leave`**:** Clears the queue and disconnects from Voice Channel.



## ✨ Demo

Add [Distro](https://discord.com/api/oauth2/authorize?client_id=932340193921491035&permissions=8&scope=applications.commands%20bot) to your server.\
Join our [Discord Server](https://discord.gg/RKBMgqwtNV), you can ask your queries if you face any problems while hosting.


## Authors

- [@chauhantirth](https://www.github.com/chauhantirth)

> Note: Give a star to this repository if it worked for you.
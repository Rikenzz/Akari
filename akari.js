// Discord music bot by Riken
const { Client, Intents } = require('discord.js');
const ytdl = require('ytdl-core');
const ytsr = require('ytsr');
require('dotenv').config();
const token = process.env.DISCORD_TOKEN;

const { createAudioResource, createAudioPlayer, joinVoiceChannel, AudioPlayerStatus } = require('@discordjs/voice');

const client = new Client({ intents: [Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_VOICE_STATES] });
const queue = new Map();

client.once('ready', () => {
    console.log('Akari is ready!');
});

client.on('interactionCreate', async interaction => {
    if (!interaction.isCommand()) return;

    const { commandName, options } = interaction;

    // PLAY COMMAND
    if (commandName === 'play') {
        const song = options.getString('song');
        // Check if user is in a voice channel
        const voiceChannel = interaction.member.voice.channel;
        if (!voiceChannel) {
            return interaction.reply({ content: 'You must be in a voice channel to play music!', ephemeral: true });
        }
        // Check if bot has permissions to connect and speak in a voice channel
        const permissions = voiceChannel.permissionsFor(interaction.client.user);
        if (!permissions.has('CONNECT') || !permissions.has('SPEAK')) {
            return interaction.reply({ content: 'I need the permissions to join and speak in your voice channel!', ephemeral: true });
        }

        const serverQueue = queue.get(interaction.guildId);

        // If URL, get song info. If not, get URL from first search result and proceed
        let songData;
        if (ytdl.validateURL(song)) {
            const songInfo = await ytdl.getInfo(song);
            songData = {
                title: songInfo.videoDetails.title,
                url: songInfo.videoDetails.video_url,
            }
        } else {
            const searchResults = await ytsr(song, { limit: 1 });
            const videoURL = searchResults.items[0].url;
            if (ytdl.validateURL(videoURL)) {
                const songInfo = await ytdl.getInfo(videoURL);
                songData = {
                    title: songInfo.videoDetails.title,
                    url: songInfo.videoDetails.video_url,
                }
            }
        }
        
        // Create server queue if it does not exist
        if (!serverQueue) {
            const queueContruct = {
                textChannel: interaction.channel,
                voiceChannel: voiceChannel,
                connection: null,
                songs: [],
                volume: 5,
                playing: true,
                player: null
            };
            queue.set(interaction.guildId, queueContruct);
            queueContruct.songs.push(songData);

            try {
                const connection = joinVoiceChannel({
                    channelId: voiceChannel.id,
                    guildId: voiceChannel.guild.id,
                    adapterCreator: voiceChannel.guild.voiceAdapterCreator,
                });
                queueContruct.connection = connection;
                const player = createAudioPlayer();
                queueContruct.player = player;
                connection.subscribe(player);
                playSong(queueContruct.songs[0], queueContruct);
                await interaction.reply(`Now playing: **${songData.title}**`);
            } catch (err) {
                queue.delete(interaction.guildId);
                console.error(err);
                return interaction.reply({ content: 'I was unable to join the voice channel!', ephemeral: true });
            }
        } else {
            serverQueue.songs.push(songData);
            return interaction.reply(`Added to the queue: **${songData.title}**`);
        }
    } else if (commandName === 'skip') {
        // SKIP COMMAND
        const serverQueue = queue.get(interaction.guildId);
        if (!serverQueue) {
            return interaction.reply('There is no song that I could skip!');
        }
        if (serverQueue.player) {
            serverQueue.player.stop();
        }
        return interaction.reply('Skipped the current song!');
    } else if (commandName === 'stop') {
        // STOP COMMAND
        const serverQueue = queue.get(interaction.guildId);
        if (!serverQueue) {
            return interaction.reply('There is no song that I could stop!');
        }
        if (serverQueue.player) {
            serverQueue.player.stop();
        }
        serverQueue.songs = [];
        serverQueue.playing = false;
        if (serverQueue.connection) {
            serverQueue.connection.destroy();
            serverQueue.connection = null;
            queue.clear();
        }
        return interaction.reply('Stopped playing music and cleared the queue!');
    }
});


// Play function
async function playSong(songData, serverQueue) {
    const stream = ytdl(songData.url, { 
        filter: 'audioonly',
        fmt: 'mp3',
        highWaterMark: 1 << 62,
        liveBuffer: 1 << 62,
        dlChunkSize: 0,
        bitrate: 64,
    });
    const resource = createAudioResource(stream, { inlineVolume: true });
    serverQueue.player.play(resource);
    serverQueue.player.on(AudioPlayerStatus.Idle, () => {
        serverQueue.songs.shift();
        if (serverQueue.songs.length > 0) {
            playSong(serverQueue.songs[0], serverQueue);
        } else {
            serverQueue.playing = false;
            serverQueue.connection.destroy();
            queue.delete(serverQueue.voiceChannel.guild.id);
        }
    });
}

client.login(token);

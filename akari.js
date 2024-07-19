// Discord music bot by Riken
const { Client, GatewayIntentBits, IntentsBitField } = require('discord.js');
const ytdl = require('ytdl-core');
const ytsr = require('ytsr');
require('dotenv').config();
const token = process.env.DISCORD_TOKEN;

const { createAudioResource, createAudioPlayer, joinVoiceChannel, AudioPlayerStatus, VoiceConnectionStatus } = require('@discordjs/voice');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildVoiceStates,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
});

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
        const voiceChannel = interaction.member.voice.channel;
        if (!voiceChannel) {
            return interaction.reply({ content: 'You must be in a voice channel to play music!', ephemeral: true });
        }

        const permissions = voiceChannel.permissionsFor(interaction.client.user);
        if (!permissions.has(IntentsBitField.Flags.Connect) || !permissions.has(IntentsBitField.Flags.Speak)) {
            return interaction.reply({ content: 'I need the permissions to join and speak in your voice channel!', ephemeral: true });
        }

        const serverQueue = queue.get(interaction.guildId);

        let songData;
        if (ytdl.validateURL(song)) {
            const songInfo = await ytdl.getInfo(song);
            songData = {
                title: songInfo.videoDetails.title,
                url: songInfo.videoDetails.video_url,
            };
        } else {
            const searchResults = await ytsr(song, { limit: 1 });
            const videoURL = searchResults.items[0].url;
            if (ytdl.validateURL(videoURL)) {
                const songInfo = await ytdl.getInfo(videoURL);
                songData = {
                    title: songInfo.videoDetails.title,
                    url: songInfo.videoDetails.video_url,
                };
            }
        }

        if (!serverQueue) {
            const queueConstruct = {
                textChannel: interaction.channel,
                voiceChannel: voiceChannel,
                connection: null,
                songs: [],
                volume: 5,
                playing: true,
                player: null
            };
            queue.set(interaction.guildId, queueConstruct);
            queueConstruct.songs.push(songData);

            try {
                const connection = joinVoiceChannel({
                    channelId: voiceChannel.id,
                    guildId: voiceChannel.guild.id,
                    adapterCreator: voiceChannel.guild.voiceAdapterCreator,
                });

                connection.on(VoiceConnectionStatus.Disconnected, async () => {
                    queue.delete(interaction.guildId);
                });

                queueConstruct.connection = connection;
                const player = createAudioPlayer();
                queueConstruct.player = player;
                connection.subscribe(player);
                playSong(queueConstruct.songs[0], queueConstruct);
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
            queue.delete(serverQueue.voiceChannel.guild.id);
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

    if (!serverQueue.player) {
        const player = createAudioPlayer();
        serverQueue.player = player;
        serverQueue.connection.subscribe(player);
    }

    serverQueue.player.play(resource);

    serverQueue.player.on(AudioPlayerStatus.Idle, async () => {
        if (serverQueue.songs.length > 0) {
            serverQueue.songs.shift();
            if (serverQueue.songs.length > 0) {
                await playSong(serverQueue.songs[0], serverQueue);
            } else {
                serverQueue.playing = false;
                if (serverQueue.connection) serverQueue.connection.destroy();
                queue.delete(serverQueue.voiceChannel.guild.id);
            }
        }
    });

    serverQueue.player.on('error', error => {
        console.error(`Error: ${error.message}`);
        serverQueue.songs.shift();
        if (serverQueue.songs.length > 0) {
            playSong(serverQueue.songs[0], serverQueue);
        } else {
            serverQueue.playing = false;
            if (serverQueue.connection) serverQueue.connection.destroy();
            queue.delete(serverQueue.voiceChannel.guild.id);
        }
    });
}

client.login(token);

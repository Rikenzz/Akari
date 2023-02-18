# Akari
Personal Discord music bot written in JavaScript

## SETUP
First, you need to install Node.JS and NPM for your environment.

To see if it installed correctly, run the following commands:
```
node -v
npm -v
```
Akari is currently running on Node v19.0.0 and NPM v8.19.2.

Then you can clone this repository and move into the newly created folder to run ```npm install```

You may also want to create a virtual environment before running the install command so packages are not installed globally on your system.

## CONFIG
Create a .env file containing your Discord bot token:
```
DISCORD_TOKEN = "put-your-discord-bot-token-here"
```

You are now ready to go! Just run ```node akari.js``` to get the bot online

To run it as a service on Linux :
```
vim /etc/systemd/system/akari.service

# AKARI.SERVICE
[Unit]
Description=Akari discord music bot

Wants=network.target
After=syslog.target network-online.target

[Service]
Type=simple
User=root
ExecStart= /root/.nvm/versions/node/v19.0.0/bin/node /root/dev/Akari/akari.js
WorkingDirectory=/root/dev/Akari
Restart=on-failure
RestartSec=10
KillMode=process
Environment=PATH=/usr/bin:/usr/local/bin

[Install]
WantedBy=multi-user.target
```
Then do:
```
systemctl enable akari.service
systemctl daemon-reload
systemctl start akari.service
```
To get the latest log if an error occurs: ```journalctl -u akari | tail```

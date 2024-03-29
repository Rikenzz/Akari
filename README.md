# Akari
Personal Discord music bot written in JavaScript

## SETUP
First, you need to install Node.JS and NPM for your environment.

To see if it installed correctly, run the following commands:
```
node -v
npm -v
```
Akari is currently running fine on Node v19.0.0 and NPM v9.6.7

You can then clone this repository and move into the newly created folder to run ```npm install```

You may also want to create a virtual environment before running the install command so packages are not installed globally on your system.

## CONFIG
Copy ```.env-sample``` to a ```.env``` file and fill in the DISCORD_TOKEN variable (only this one is required to run):
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
ExecStart= /root/.nvm/versions/node/v19.0.0/bin/node /app/akari/akari.js
WorkingDirectory=/app/akari
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

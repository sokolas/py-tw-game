# Pygame integrated with Twitch chat
## Installation
* create a cirtual env `python3 -m venv ./venv`
* activate it (`source ./venv/bin/activate` or whatever it is for your shell)
* install requirements `pip3 install -r requirements.txt`

## Prereqs
1. create an app here https://dev.twitch.tv/console/apps/create
    * Name: any
    * Redirect URI: must correspond to the chosen port (5000 by default) and have `/twitch` path (it's hardcoded for now). Default: `http://localhost:5000/twitch`
    * Category: any
    * Client type: `Public`, there's no support for storing secrets
2. Once the app is created, go to https://dev.twitch.tv/console/apps, click `Manage` on your app, and copy the `client_id`
3. Open `config/config.json` and fill out your settings: channel, port and client_id

## Running
`python3 -m game`

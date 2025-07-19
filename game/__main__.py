import os
import sys
import json
import asyncio

from .twitch import Twitch
from .webhandler import WebHandler
from .mygame import Game
from .eventhandler import EventHandler

channel = None
token = None
port = 5000
client_id = None

if os.path.exists("config/token.txt"):
    with open("config/token.txt") as token_file:
        token = token_file.read()
    

with open("config/config.json") as config_file:
    config_str = config_file.read()
    config = json.loads(config_str)
    
    channel = config.get("channel", None)
    port = config.get("port", 5000)
    client_id = config.get("client_id", None)

if (not channel):
    print("channel is not specified in the config")
    sys.exit(1)

if (not client_id):
    print("client_id is not specified in the config")
    sys.exit(1)
    
print("config is loaded, starting the app")

# wire everything up together
loop = asyncio.get_event_loop()

twitch = Twitch(channel, client_id, token, port, loop)

web_handler = WebHandler(twitch, port, loop)
web_task = web_handler.create_task()

game = Game()
game.set_tick_callback(web_handler.run_once)

event_handler = EventHandler(game)
twitch.set_chat_handler(event_handler.handle_chat_event)
web_handler.set_event_handler(event_handler.handle_web_event)

# start
twitch.check_auth()
game.run()

# cleanup
web_handler.close()

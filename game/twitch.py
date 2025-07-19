import aiohttp
import os
import urllib.parse
import websockets
import json
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

# handles everything twitch-specific
class Twitch:
    def __init__(self, channel, client_id, token, port, loop):
        print(f"Twitch initialized: #{channel}")
        self.channel = channel
        self.client_id = client_id
        self.token = token
        self.port = port
        self.loop = loop
        self.chat_handler = None

    # to avoid looping dependencies, we set the handler function independently
    # handler MUST be async to work in this way
    # this also prevents the event loop from being stuck on long-running operations
    def set_chat_handler(self, handler):
        self.chat_handler = handler

    # if the token is found, check it (receiving the broadcaster id and user id in the process)
    # if there's no token, prompt user to authorize
    def check_auth(self):
        if self.token:
            self.loop.create_task(self.check_token())
            return
        else:
            self.auth()
    
    # prompt the user to authorize
    def auth(self):
        params = {
            "scope": "user:read:chat user:write:chat",
            "redirect_uri": f"http://localhost:{self.port}/twitch",
            "response_type": "token",
            "client_id": self.client_id,
            "force_verify": "true"
        }
        params_str = urllib.parse.urlencode(params)

        auth_url = f"https://id.twitch.tv/oauth2/authorize?{params_str}"
        print("Follow this link to authorize on Twitch")
        print(auth_url) # TODO open a browser with this url

    # helper functions to perform GET and POST requests to twitch api
    async def get_data(self, session, url, params = {}):
        headers = {"Authorization": f"Bearer {self.token}", "Client-Id": self.client_id}
        async with session.get(url, params = params, headers = headers) as response:
            data = await response.json()
            # print("Twitch response: ", data)
            return data

    async def post_data(self, session, url, params = {}, data = {}):
        headers = {"Authorization": f"Bearer {self.token}", "Client-Id": self.client_id, "Content-Type": "application/json"}
        async with session.post(url, params = params, headers = headers, data = json.dumps(data)) as response:
            r_data = await response.json()
            # print("Twitch response: ", r_data)
            return r_data

    # check the token validity, retrieve the user and broadcaster ids
    async def check_token(self):
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"OAuth {self.token}", "Client-Id": self.client_id}
            async with session.get("https://id.twitch.tv/oauth2/validate", headers = headers) as response:
                data = await response.json()
                # print("Token validation response: ", data)
                status = data.get("status", None)
                if (status):
                    message = data.get("message", "")
                    print(f"Token validation error: {status} {message}")
                    self.auth()
                    return None
                self.login = data.get("login", None)
                self.user_id = data.get("user_id", None)
                print(f"Token validated, user: {self.user_id} {self.login}")
            await self.get_broadcaster_id()
            print(f"got channel {self.channel} id {self.broadcaster_id}")
            await self.connect_eventsub()
            return True

    # query the channel id and set it to broadcaster_id
    async def get_broadcaster_id(self):
        async with aiohttp.ClientSession() as session:
            response = await self.get_data(session, "https://api.twitch.tv/helix/users", params = {"login": self.channel})
            data = response.get("data", [])
            if len(data) > 0:
                self.broadcaster_id = data[0].get("id", None)

    # create a websocket and run an endless loop (in the event loop) receiving its messages
    async def connect_eventsub(self):
        self.ws = await websockets.connect("wss://eventsub.wss.twitch.tv/ws")
        try:
            while True:
                response = await self.ws.recv()
                data = json.loads(response)
                metadata = data.get("metadata", {})
                message_type = metadata.get("message_type")

                if message_type != "session_keepalive": # don't care, just means we're still online
                    # print(f"eventsub: {response}")
                    pass
                
                if message_type == "session_welcome": # first message we receive from twitch, prompting us to subscribe to one or more notifications
                    self.es_session_id = data["payload"]["session"]["id"]
                    self.loop.create_task(self.subscribe_eventsub_chat())
                elif message_type == "notification": # actual event data
                    event = data["payload"]["event"]
                    # ignore self-messages (use a bot account!)
                    if self.user_id != event["chatter_user_id"]:
                        # this is where we decouple twitch message handling from actual "business logic"
                        if self.chat_handler:
                            self.loop.create_task(self.chat_handler(event))
        except ConnectionClosedOK:
            print("Connection closed normally.")
        except ConnectionClosedError as e:
            print(f"Connection closed with error: {e}")
        except Exception as e:
            print(f"Unexpected error while receiving: {e}")
        self.ws = None
        # if we reached this point, the websocket is no longer connected
        # TODO reconnect on error (schedule a new task with connect_eventsub())

    # this is called when the server has received a token from the browser (user has authorized the app)
    async def do_auth(self, token):
        self.token = token
        print("Got twitch token")
        with open("config/token.txt", "w") as token_file:
            token_file.write(token)
        # validate token and receive the ids
        await self.check_token()
    
    # to be called from sync code
    def send_message(self, m):
        self.loop.create_task(self.send_message_async(m))

    # actually send a message, in async way
    async def send_message_async(self, message):
        if self.broadcaster_id:
            async with aiohttp.ClientSession() as session:
                data = await self.post_data(session, "https://api.twitch.tv/helix/chat/messages", data = {"broadcaster_id": self.broadcaster_id, "sender_id": self.user_id, "message": message})
        else:
            print(f"broadcaster_id of the channel {self.channel} is unknown")
    
    # we need to call this as asoon as we receive "session_welcome" from the websocket, in order to read chat
    async def subscribe_eventsub_chat(self):
        req = {
            "type" : "channel.chat.message",
            "version" : "1",
            "condition" : {
                "broadcaster_user_id" : self.broadcaster_id,
                "user_id" : self.user_id
            },
            "transport" : {
                "method" : "websocket",
                "session_id" : self.es_session_id
            }
        }
        async with aiohttp.ClientSession() as session:
            sub_response = await self.post_data(session, "https://api.twitch.tv/helix/eventsub/subscriptions", data = req)
            # await self.send_message("ready")
            
        
from fastapi import FastAPI, Response
import asyncio
import uvicorn
import json

twitch_auth_response = ""
with open("web/twitch_auth.html") as tw_resp_file:
    # because twitch returns the token in the hash, and it's not accessible by our server
    twitch_auth_response = tw_resp_file.read()

# an http server to process the authentication from twitch
# we can add more routes or even websocket handlers, to access some data in our game
class WebHandler:

    def __init__(self, twitch, port, event_loop):
        self.loop = event_loop
        self.app = FastAPI()
        self.twitch = twitch
        self.port = port
        self.setup_routes()

    # pass in a function to be called to signal some server event has occured
    def set_event_handler(self, event_handler):
        self.event_handler = event_handler

    def setup_routes(self):
        # handle twitch auth; this MUST correspond to the resirect uri in twitch setup
        @self.app.get("/twitch")
        async def auth_twitch(error: str = "", error_description: str = "", access_token: str = ""):
            if (error != ""):
                print(f"Twitch auth error {error}: {error_description}")
            elif access_token != "":
                self.loop.create_task(self.twitch.do_auth(access_token))
                print("got token")
            # a simple page to convert hash params from a url to query params, because only the browser can access those
            # also displays the auth status to the user
            return Response(content = twitch_auth_response, media_type = "text/html")
        
        # TODO add any routes you need, like:
        # @self.app.websocket("/ws") .......
        # @self.app.get("/hug") ....

        # an example on how to pass the server event to the "business logic"
        @self.app.post("/exit")
        async def handle_exit():
            if self.event_handler:
                self.loop.create_task(self.event_handler("exit"))
            return {}

    # a wrapper to be able to run one step of asyncio event loop inside the synchronous pygame loop
    def run_once(self):
        self.loop.call_soon(self.loop.stop)
        self.loop.run_forever()
    
    # coroutine wrapper to start the server
    async def serve(self):
        config = uvicorn.Config(app=self.app, port=self.port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    # sync entry point to "run in background"
    def create_task(self):
        return self.loop.create_task(self.serve())

    def close(self):
        self.loop.stop()

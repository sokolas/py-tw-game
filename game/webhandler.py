from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route
import uvicorn

twitch_auth_response = ""
with open("web/twitch_auth.html") as tw_resp_file:
    # because twitch returns the token in the hash, and it's not accessible by our server
    twitch_auth_response = tw_resp_file.read()

# an http server to process the authentication from twitch
# we can add more routes or even websocket handlers, to access some data in our game
class WebHandler:

    def __init__(self, twitch, port, event_loop):
        self.loop = event_loop
        self.twitch = twitch
        self.port = port
        self.setup_app()

    # pass in a function to be called to signal some server event has occured
    def set_event_handler(self, event_handler):
        self.event_handler = event_handler

    def setup_app(self):
        # route handlers
        # handle twitch auth
        async def auth_twitch(request):
            error = request.query_params.get("error", "")
            error_description = request.query_params.get("error_description", "")
            access_token = request.query_params.get("access_token", "")

            if (error != ""):
                print(f"Twitch auth error {error}: {error_description}")
            elif access_token != "":
                self.loop.create_task(self.twitch.do_auth(access_token))
                print("got token")
            # a simple page to convert hash params from a url to query params, because only the browser can access those
            # also displays the auth status to the user
            return HTMLResponse(twitch_auth_response)
        
        # an example on how to pass the server event to the "business logic"
        async def handle_exit(request):
            if self.event_handler:
                self.loop.create_task(self.event_handler("exit"))
            return {}

        # set up the app
        self.app = Starlette(debug=False, routes=[
            Route("/twitch", auth_twitch, methods = ["GET"]),   # this MUST correspond to the redirect uri in twitch setup
            Route("/exit", handle_exit, methods = ["POST"])
            # TODO add any routes you need, like:
            # WebSocketRoute("/ws") .......
            # Route("/hug") ....
        ])

    # a wrapper to be able to run one step of asyncio event loop inside the synchronous pygame loop
    def run_once(self):
        self.loop.call_soon(self.loop.stop)
        self.loop.run_forever()
    
    # coroutine wrapper to start the server
    async def serve(self):
        config = uvicorn.Config(app=self.app, port=self.port, log_level="info", access_log=False)
        server = uvicorn.Server(config)
        await server.serve()

    # sync entry point to "run in background"
    def create_task(self):
        return self.loop.create_task(self.serve())

    def close(self):
        self.loop.stop()

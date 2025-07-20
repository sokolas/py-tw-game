# a "business logic" event handler, decoupling twitch stuff from the game/presentation
class EventHandler:
    def __init__(self, game):
        self.game = game

    # must be async in order to be handled properly
    async def handle_chat_event(self, event):
        text = event["message"]["text"]
        chatter_id = event["chatter_user_id"]
        chatter_login = event["chatter_user_login"]
        chatter_name = event["chatter_user_name"]
        
        print(f"message from {chatter_name}: {text}")
        # or do something in the game:
        # game.displayMessage(chatter_name, text)
        # game.hug(chatter_name)
        #.....

    # an entry point for the server, to close the game from a request, or something
    async def handle_web_event(self, event):
        if event == "exit":
            self.game.running = False
    
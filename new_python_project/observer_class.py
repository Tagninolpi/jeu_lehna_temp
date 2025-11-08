class Observer:
    def __init__(self, server):
        self.server = server  # store a reference to the server
        self.message_queue = server.message_queue  # listener pulls from this

    async def message_listener(self):
        while True:
            client_id, msg = await self.message_queue.get()
            page_name = msg["page"]
            button = msg["button"]

            if page_name == "main_menu":
                if button == "player":
                    self.server.join_lobby()
                elif button == "admin":
                    self.server.become_admin(msg["password"])
                else:
                    print(f"{button} is not valid")
            elif page_name == "admin_para":
                if button == "create_lobby":
                    self.server.create_lobby()
                else:
                    print(f"{button} is not valid")
            elif page_name == "admin_lobby":
                if button == "start_game":
                    self.server.start_game()
                else:
                    print(f"{button} is not valid")
            elif page_name == "game":
                if button == "change_partner":
                    self.server.player_change_partner()
                else:
                    print(f"{button} is not valid")
            elif page_name == "admin_game_results":
                if button == "download":
                    self.server.download_game_results()
                else:
                    print(f"{button} is not valid")
            else:
                print(f"{page_name} is not valid")
import asyncio
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
                if button == "player": #done
                    await self.server.join_lobby(client_id)
                elif button == "admin": #done
                    await self.server.become_admin(client_id,msg["message"])
                else:
                    print(f"{button} is not valid")
            elif page_name == "admin_para":
                if button == "create_lobby":
                    await self.server.create_lobby(client_id,msg["message"])
                else:
                    print(f"{button} is not valid")
            elif page_name == "admin_lobby":
                if button == "start_game":
                    asyncio.create_task(self.server.start_game())
                else:
                    print(f"{button} is not valid")
            elif page_name == "player":
                if button == "change_partner":
                    print("funcchange")
                    await self.server.player_change_partner(client_id)
                else:
                    print(f"{button} is not valid")
            elif page_name == "admin_result":
                if button == "reset_game":
                    await self.server.reset_all(True)
                else:
                    print(f"{button} is not valid")
            else:
                print(f"{page_name} is not valid")
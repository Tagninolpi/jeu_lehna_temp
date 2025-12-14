import asyncio

# Ecoute les actions du coté client => dit au server de faire des actions.
class Observer:
    def __init__(self, server):
        self.server = server  #reference au server
        self.message_queue = server.message_queue  # list des messages recu du client (html=>main.js=>app.py=>ici)

    async def message_listener(self): # appelé au lancement de l'app (app.py)
        while True:
            client_id, msg = await self.message_queue.get() 
            '''
            msg recu du client : {page: "nom_page_html",button: "bouton_clické",message: "info_suplémentaire"}
            '''
            page_name = msg["page"]
            button = msg["button"]

            # selon le bouton clicker dit au server de faire qqchose
            if page_name == "main_menu":
                if button == "player":
                    await self.server.join_lobby(client_id)
                elif button == "admin":
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
                    await self.server.player_change_partner(client_id)
                else:
                    print(f"{button} is not valid")

            elif page_name == "player_lobby":
                if button == "leave":
                    await self.server.leave_lobby(client_id)
                else:
                    print(f"{button} is not valid")

            elif page_name == "admin_result":
                if button == "reset_game":
                    await self.server.reset_all(True)
                else:
                    print(f"{button} is not valid")

            elif page_name == "player_result":
                if button == "leave_game":
                    await self.server.leave_game(client_id)
                else:
                    print(f"{button} is not valid")

            elif page_name == "pre_game":
                if button == "load_page":
                    await self.server.pre_game(client_id)
                else:
                    print(f"{button} is not valid")
            else:
                print(f"{page_name} is not valid")
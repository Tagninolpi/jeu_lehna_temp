from game_class import Game
#gestion des connexions WebSocket (Joueurs et Admin)
class Connections():
    def __init__(self):
        self.websockets = {} # {"admin ou player id": object WS} ajout depuis (app.py)
        self.lobby = {} #{"game id" (=0):["id_joueur1",id_joueur2",...]} (ajout depuis server_class.py join_lobby())  1 seul jeu à tous moment 
        self.game = None # instance de la class Game() game_class.py ajout depuis server_class.py create_lobby()
        self.admin_id = None # id de l'admin de la partie  1 seul admin à la fois, ajout depuis server_class.py become_admin()
        

    async def disconnect(self, client_id: str):
        # supprime et deconnect client_id de lobby (aussi utilisé pendant game)
        #lobby = {0:["id_joueur1",id_joueur2",...]}
        lobby_list = self.lobby.get(0) if isinstance(self.lobby, dict) else None
        if isinstance(lobby_list, list) and client_id in lobby_list:
            lobby_list.remove(client_id)
        websocket = self.websockets.pop(client_id, None)
        if websocket:
            try:
                print("diconnect")
                await websocket.close()
            except Exception as e:
                print(e)

    async def update_value_all(self, targets, info_dict):
        # server_class.py => ici => main.js => html
        # prend tout type de structure pour targets : None,str,list,dict,list,set,tupples => list d'ids
        if targets is None:
            target_ids = list(self.websockets.keys()) 
        elif isinstance(targets, str):
            target_ids = [targets]
        elif isinstance(targets, dict):
            target_ids = list(targets.keys())
        else:
            # list, set, tuple
            target_ids = list(targets)

        # info_dict contient {"id_champ_html":("nouvelle_valeur","bool_visibilité")}
        msg = {
            "type": "ui_update",
            "payload": info_dict
        }

        to_remove = [] # si deconnecté

        for client_id in target_ids:
            ws = self.websockets.get(client_id)
            if not ws:
                to_remove.append(client_id)
                continue
            try:
                await ws.send_json(msg) # envoi à main.js
            except Exception:
                to_remove.append(client_id)

        # deconnecter les clients proprement
        for client_id in to_remove:
            await self.disconnect(client_id)
        
    async def change_page(self, targets, new_page):
        # Normalise les target comme pour update_vale_all()
        if targets is None:
            target_ids = list(self.websockets.keys())
        elif isinstance(targets, str):
            target_ids = [targets]
        else:
            target_ids = list(targets)
        
        #new_page = "nom_page_html"
        msg = {"type": "change_page", "payload": new_page}

        to_remove = []

        for client_id in target_ids:
            ws = self.websockets.get(client_id)
            if not ws:
                to_remove.append(client_id)
                continue

            try:
                await ws.send_json(msg)
            except Exception:
                to_remove.append(client_id)

        # Safely remove clients AFTER iteration
        for client_id in to_remove:
            await self.disconnect(client_id)
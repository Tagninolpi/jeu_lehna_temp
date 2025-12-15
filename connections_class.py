from game_class import Game
#manage the Websocket connections (players and Admin)
class Connections():
    def __init__(self):
        self.websockets = {} # {"admin or player id": WS object} set in (app.py)
        self.lobby = {} #{"game id" (=0):["player1_id",player2_id",...]} (set in server_class.py join_lobby())  1 game at any time
        self.game = None # instance of the class Game() game_class.py set in server_class.py create_lobby()
        self.admin_id = None # duplicat of server class can be deleted (to verify)
        

    async def disconnect(self, client_id: str):
        # delete and disconnect client_id from lobby
        #lobby = {0:["player1_id,player2_id",...]}
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
        # server_class.py => here => main.js => html
        # can take any type of structure for targets : None,str,list,dict,list,set,tupples => list d'ids
        if targets is None:
            target_ids = list(self.websockets.keys()) 
        elif isinstance(targets, str):
            target_ids = [targets]
        elif isinstance(targets, dict):
            target_ids = list(targets.keys())
        else:
            # list, set, tuple
            target_ids = list(targets)

        # info_dict contains {"id_of_the_html_value_id":("new_value","bool_visibility")}
        msg = {
            "type": "ui_update",
            "payload": info_dict
        }

        to_remove = [] # if disconnected

        for client_id in target_ids:
            ws = self.websockets.get(client_id)
            if not ws:
                to_remove.append(client_id)
                continue
            try:
                await ws.send_json(msg) # send to main.js
            except Exception:
                to_remove.append(client_id)

        # disconnect clients properly
        for client_id in to_remove:
            await self.disconnect(client_id)
        
    async def change_page(self, targets, new_page):
        # Normalise the targets like in update_vale_all()
        if targets is None:
            target_ids = list(self.websockets.keys())
        elif isinstance(targets, str):
            target_ids = [targets]
        else:
            target_ids = list(targets)
        
        #new_page = "name_page_html"
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
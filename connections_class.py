from game_class import Game
class Connections():
    def __init__(self):
        self.websockets = {}
        self.lobby = {}
        self.game = None
        self.admin_id = None # neccesary for await self.update_connected_ammount(self.admin_id)
        

    async def disconnect(self, client_id: str):
        lobby_list = self.lobby.get(0) if isinstance(self.lobby, dict) else None
        if isinstance(lobby_list, list) and client_id in lobby_list:
            lobby_list.remove(client_id)
        websocket = self.websockets.pop(client_id, None)
        #await self.connections.update_value_all(self.websockets,{"players_connected":(f"Joueurs connectés : {len(self.connections.lobby.get(0, []))}",True)})
        if websocket:
            try:
                print("diconnect")
                await websocket.close()
                
            except Exception as e:
                print(e)

    async def update_value_all(self, targets, info_dict):

        # Normalize "targets"
        if targets is None:
            target_ids = list(self.websockets.keys())  # broadcast
        elif isinstance(targets, str):
            target_ids = [targets]                     # single client
        elif isinstance(targets, dict):
            target_ids = list(targets.keys())          # dict keys
        else:
            # list, set, tuple
            target_ids = list(targets)

        msg = {
            "type": "ui_update",
            "payload": info_dict
        }

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

        # Cleanup disconnected clients
        for client_id in to_remove:
            await self.disconnect(client_id)
        
    async def change_page(self, targets, new_page):
        # Normalize targets
        if targets is None:
            target_ids = list(self.websockets.keys())  # broadcast to everyone
        elif isinstance(targets, str):
            target_ids = [targets]                     # single ID
        else:
            target_ids = list(targets)                 # list, set, tuple

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

    """ 
        async def change_page(self, client_id: str,new_page):
            ws = self.websockets.get(client_id)
            try:
                await ws.send_json({"type": "change_page","payload": new_page})
                #print("send json")
            except Exception as e:
                await self.disconnect(client_id)

        async def change_page_for_all_in(self, client_id_list:list,new_page):
            to_remove = []
            for client_id in client_id_list:
                try:
                    await self.websockets[client_id].send_json({"type": "change_page","payload": new_page})
                except Exception as e:
                    print(e)
                    to_remove.append((client_id,self.websockets[client_id]))
            for connections in to_remove:
                await self.disconnect(connections[0],connections[1])

    def get_play_info(self,client_id):
        player = self.game.all_players[client_id]
        return {
                "type": "player_update",
                "payload": {
                    "id": player.id,
                    "value": player.value,
                    "candidate": player.candidate,
                    "candidate_id": player.candidate_id,
                    "partner": player.partner,
                    "partner_id": player.partner_id,
                    "courtship_timer": player.courtship_timer,
                    "mating": player.mating,
                    "button": player.accept_candidate
                }
            }


######

    async def update_player_info(self, client_id: str):
        ws = self.websockets.get(client_id)
        try:
            await ws.send_json(self.get_play_info(client_id))
        except Exception as e:
            await self.disconnect(client_id)


    async def update_game_stat_in_player_view(self):
        targets = set(self.lobby.get(0, []))
        for client_id in targets:
            ws = self.websockets.get(client_id)
            if not ws:
                continue

            try:
                await ws.send_json({
                    "type": "player_parameters",
                    "payload": self.game.parameters
                })
            except Exception as e:
                print(f"Disconnecting {client_id} due to error: {e}")
                await self.disconnect(client_id)
"""
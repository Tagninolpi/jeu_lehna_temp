from game_class import Game
class Connections():
    def __init__(self):
        self.websockets = {}
        self.lobby = {}
        self.game = Game(10,10,30,2,5)
        

    async def disconnect(self, client_id: str):
        websocket = self.websockets.pop(client_id, None)
        if client_id in self.lobby[0]:
            self.lobby[0].remove(client_id)
        if websocket:
            try:
                print("diconnect")
                await websocket.close()
            except Exception as e:
                print(e)

    async def update_player_info(self, client_id: str,player_info):
        """Send the full player data to the client."""
        ws = self.websockets.get(client_id)
        try:
            await ws.send_json(self.get_play_info(client_id))
        except Exception as e:
            await self.disconnect(client_id)

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
                    "mating": player.mating
                }
            }
    
    async def change_page(self, client_id: str,new_page):
        """Send the full player data to the client."""
        ws = self.websockets.get(client_id)
        try:
            await ws.send_json({"type": "change_page","payload": new_page})
            print("send json")
        except Exception as e:
            await self.disconnect(client_id)

    async def change_page_for_all_in(self, client_id_list:list,new_page):
        """Send the full player data to the client."""
        to_remove = []
        for client_id in client_id_list:
            try:
                await self.websockets[client_id].send_json({"type": "change_page","payload": new_page})
            except Exception as e:
                print(e)
                to_remove.append((client_id,self.websockets[client_id]))
        for connections in to_remove:
            await self.disconnect(connections[0],connections[1])

    async def broadcast_game_status_update(self, new_status):
        coros = []
        to_remove = []
        print(self.websockets)
        for client_id in self.game.active_players:
            ws = self.websockets.get(client_id)
            if ws:
                coros.append(self._safe_send(ws, client_id, new_status))

        if coros:
            await asyncio.gather(*coros)

    async def _safe_send(self, ws, client_id, new_status):
        try:
            print(2)
            await ws.send_json({"type": "status_update", "payload": new_status})
        except Exception as e:
            print(f"Disconnecting {client_id} due to error: {e}")
            await self.disconnect(client_id)

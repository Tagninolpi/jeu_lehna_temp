class Connections():
    def __init__(self):
        self.websockets = {}

    async def disconnect(self, client_id: str):
        websocket = self.websockets.pop(client_id, None)
        if websocket:
            try:
                await websocket.close()
            except Exception as e:
                print(e)

    async def update_player_info(self, client_id: str,player_info):
        """Send the full player data to the client."""
        ws = self.player_game.get(client_id)
        try:
            await ws.send_json(player_info)
        except Exception as e:
            await self.disconnect(client_id)

    async def broadcast_game_status_update(self,new_status,page_connections):
        to_remove = []
        for client_id, ws in page_connections.items():
            try:
                await ws.send_json({"type": "status_update", "payload": new_status})
            except Exception as e:
                print(e)
                to_remove.append((client_id,page_connections))
        for connections in to_remove:
            await self.disconnect(connections[0],connections[1])


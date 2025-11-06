from fastapi import WebSocket
import asyncio, math, random
from test import Player
players = None
nb_classes = None
server = None

class Connectionserver:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.all_players = {}
        #lists
        self.active_players = []
        self.mating_players = []
        self.previous_pairs = []
        self.current_pairs = []
        self.changing_players = []

        #vars
        self.game_status = "waiting for player"
        self.round = 0

        #events
        self.ev_lobby_full = asyncio.Event()
        self.ev_players_start_choose = asyncio.Event()
        self.ev_players_choose_finish = asyncio.Event()


    async def connect(self, websocket: WebSocket, client_id: str):
        if len(self.active_connections) <players:
            await websocket.accept() # server accept player
            self.active_connections[client_id] = websocket # store server connect
            self.all_players[client_id] = Player(nb_classes,client_id) #Player class
            self.active_players.append(client_id)
            await self.send_player_update(client_id)
            await self.broadcast(f"You connected, the game will start soon, waiting for {players-len(server.all_players)} players")
        else:
            await websocket.accept()
         

    async def disconnect(self, client_id: str):
        websocket = self.active_connections.pop(client_id, None)
        if websocket:
            try:
                await websocket.close()
            except Exception:
                pass
    async def send_status(self, client_id: str, message: str):
        """Send only a status message to one client."""
        ws = self.active_connections.get(client_id)
        if not ws:
            return
        try:
            await ws.send_json({"type": "status_update", "payload": message})
        except Exception as e:
            await self.disconnect(client_id)

    async def send_player_update(self, client_id: str):
        """Send the full player data to the client."""
        player = self.all_players[client_id]
        ws = self.active_connections.get(client_id)
        if not (player and ws):
            return
        try:
            await ws.send_json({
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
            })
        except Exception as e:
            await self.disconnect(client_id)

    async def broadcast(self,msg):
        to_remove = []
        for cid, ws in self.active_connections.items():
            try:
                await ws.send_json({"type": "status_update", "payload": msg})
            except Exception as e:
                print(f"⚠️ broadcast: erreur avec {cid} → {e}")
                to_remove.append(cid)
        for cid in to_remove:
            await self.disconnect(cid)
        


from __future__ import annotations
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from test import *
import uuid
import asyncio
import json

app = FastAPI() #create the fastApi app
app.mount("/static", StaticFiles(directory="static"), name="static")# link to js and html
nb_classes = 10

class Connectionserver:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.all_players = {}
        self.active_players = []
        self.mating_players = []
        self.previous_pairs = []
        self.current_pairs = []


    async def connect(self, websocket: WebSocket, client_id: str):
        if len(self.active_connections) <10:
            await websocket.accept() # server accept player
            self.active_connections[client_id] = websocket # store server connect
            self.all_players[client_id] = Player(nb_classes,client_id) #Player class
            self.active_players.append(client_id)
            await self.up_val(client_id,my_value=self.all_players[client_id].value)
            await self.broadcast(f"You connected, the game will start soon, waiting for {10-len(server.all_players)} players")  
        else:
            await websocket.accept()

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id)# remove player from list

    async def up_val(self, client_id: str,status=None,my_value=None,candidate=None,currentPartner=None):
        ws = self.active_connections.get(client_id)
        if ws:
            await ws.send_json({"type": "up_val", "payload": {
                "status": status,
                "my_value": my_value,
                "candidate": candidate,
                "currentPartner":currentPartner
            }})

    async def broadcast(self,msg):
        for ws in self.active_connections.values():
            await ws.send_json({"type": "up_val", "payload": {"status":msg}})

server = Connectionserver()


async def give_all_new_partner():
    #create pairs
    server.current_pairs = encounter(server.active_players,avoid=server.previous_pairs)
    # change the value of candidat in player class
    for pair in server.current_pairs:
        id_1 = pair[0]
        id_2 = pair[1]
        server.all_players[id_1].candidate = server.all_players[id_2].value
        server.all_players[id_2].candidate = server.all_players[id_1].value
    #send the value of the candidate
    for id in server.active_connections:
        await server.up_val(id,candidate= server.all_players[id].id)
    await server.broadcast("You got a new candidate")
        




@app.get("/")
def get_index():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(uuid.uuid4())[:8]  # assign unique ID
    await server.connect(websocket, client_id) #create player connection and class
    
    while len(server.active_connections)<10:
        await asyncio.sleep(0.1)

    await give_all_new_partner()

    try:
        while True:
            raw_msg = await websocket.receive_text()
            msg = json.loads(raw_msg)  # parse JSON
            action_type = msg.get("type")
            if action_type == "change_partner":
                print(f"player {client_id} want's to change partner")

    except WebSocketDisconnect:# if disconnect
        server.disconnect(client_id)
    except Exception as e: # if other error
        print(f"Error: {e}")

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

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket,Player] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        if len(self.active_connections) <10:
            await websocket.accept() # server accept player
            self.active_connections[client_id] = websocket,Player(nb_classes,client_id) # store server connect,Player class
            await self.send(client_id,{
                "type":"up_val",
                "payload": {
                    "status":"You connected, the game will start when enough players connect",
                    "my_value": self.active_connections[client_id][1].value
                    }})
        else:
            await websocket.accept()
            await self.send(client_id,{
                "type":"up_val",
                "payload": {
                    "status":"The game already started, wait for the next game"
                    }})
            await websocket.close()

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)# remove player from list

    async def send(self, client_id: str, type_: str, payload: dict):
        ws = self.active_connections.get(client_id)
        if ws:
            await ws.send_json({"type": type_, "payload": payload})

    async def broadcast(self, type_: str, payload: dict):
        for ws in self.active_connections.values():
            await ws.send_json({"type": type_, "payload": payload})

manager = ConnectionManager()



def give_all_new_partner():


@app.get("/")
def get_index():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(uuid.uuid4())[:8]  # assign unique ID
    await manager.connect(websocket, client_id) #create player connection and class
    print(f"ID={client_id}, class={manager.active_connections[client_id][1]}")
    
    while len(manager.active_connections)<10:
        await asyncio.sleep(0.1)
    
    give_all_new_partner()

    
    try:
        while True:
            raw_msg = await websocket.receive_text()
            msg = json.loads(raw_msg)  # parse JSON
            action_type = msg.get("type")

    except WebSocketDisconnect:# if disconnect
        manager.disconnect(client_id)
    except Exception as e: # if other error
        print(f"Error: {e}")

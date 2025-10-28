from __future__ import annotations
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from test import Player
import uuid

app = FastAPI() #create the fastApi app

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket,Player] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept() # server accept player
        self.active_connections[client_id] = websocket,Player(0) # store server connect,Player class
        await self.broadcast(f"Client {client_id} joined the server")

    def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)

    async def broadcast(self, message: str):
        for conn in self.active_connections.values():
            await conn.send_text(message)

manager = ConnectionManager()
# htlm client
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI WebSocket Test</title>
    </head>
    <body>
        <h1>WebSocket Test Client</h1>
        <div id="messages"></div>
        <input type="text" id="messageText" placeholder="Type a message...">
        <button onclick="sendMessage()">Send</button>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('div');
                message.textContent = event.data;
                messages.appendChild(message);
            };
            function sendMessage() {
                var input = document.getElementById('messageText');
                ws.send(input.value);
                input.value = '';
            }
        </script>
    </body>
</html>
"""
@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(uuid.uuid4())[:8]  # assign unique ID
    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"{client_id} said: {data}")
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"Error: {e}")

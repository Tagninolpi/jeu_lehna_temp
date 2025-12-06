from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager

from server_class import Server
from observer_class import Observer

import asyncio
import uuid
import json

server = Server()
observer = Observer(server)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code that runs on startup
    asyncio.create_task(observer.message_listener())
    yield
    # Code that runs on shutdown (optional)

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return RedirectResponse("/static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(uuid.uuid4())[:8]  # assign unique ID
    await websocket.accept() # server accept player
    server.connections.websockets[client_id] = websocket # store server connect
    try:
        while True:
            raw_msg = await websocket.receive_text()
            msg = json.loads(raw_msg)
            print(f"recieved : {msg}")
            await server.message_queue.put((client_id, msg))
    except WebSocketDisconnect:# if disconnect
        await server.connections.disconnect(client_id)
    except Exception as e: # if other error
        print(f"Error: {e}")

@app.get("/download_csv")
async def download_csv():
    csv_file = server.get_game_result()

    # No CSV available? → Tell the browser "nothing to download"
    if not csv_file:
        return {"available": False}

    # CSV exists → return file
    return StreamingResponse(
        csv_file,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=game_results.csv"}
    )

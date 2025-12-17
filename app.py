from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.responses import StreamingResponse
from fastapi import Response
from contextlib import asynccontextmanager

from server_class import Server
from observer_class import Observer

import asyncio
import uuid
import json

server = Server()
observer = Observer(server)

#  Code that runs on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(observer.message_listener())
    yield

app = FastAPI(lifespan=lifespan)
# load the static directory to the app (the app can use it directly)
app.mount("/static", StaticFiles(directory="static"), name="static")

# load first page = index.html 
@app.get("/")
async def root():
    return RedirectResponse("/static/index.html")

# used for Uptime robot ping
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.head("/health")
async def health_head():
    return Response(status_code=200)


# create WebSoclet endpoint (runs when a client opens the first page)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # assign unique ID to that client
    while True:
        client_id = uuid.uuid4().hex[:8]
        if client_id not in server.connections.websockets:
            break  
    await websocket.accept() # server accept player
    server.connections.websockets[client_id] = websocket # store server(WS) connection
    try:
        while True:#until disconnect
            raw_msg = await websocket.receive_text() # recieve msg from html pages
            msg = json.loads(raw_msg)
            #print(f"recieved : {msg}")
            await server.message_queue.put((client_id, msg)) # add msg to server queue
    except WebSocketDisconnect:# if disconnect
        await server.connections.disconnect(client_id)
    except Exception as e: # if other error
        print(f"Error: {e}")

# 
@app.get("/download_csv")
async def download_csv():
    csv_file, file_name = server.get_game_result() # get csv file content and file name (date and time of creation)

    # No CSV available
    if not csv_file:
        return {"available": False}

    # Return CSV to browser (the file is downloaded on the client admin page)
    return StreamingResponse(
        csv_file,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={file_name}"}
    )

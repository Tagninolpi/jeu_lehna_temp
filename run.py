from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio, uuid, json, uvicorn

import connection
import server
import game

# ------- INIT GLOBAL SETTINGS -------
NB_CLASSES = 10
PLAYERS = 6
CHOOSE_TIME = 20

# --- assign values to modules ---
server.nb_classes = NB_CLASSES
server.players = PLAYERS
server.choose_time = CHOOSE_TIME

connection.nb_classes = NB_CLASSES
connection.players = PLAYERS

# --- Create ONE shared Connectionserver instance ---
server.server = connection.Connectionserver()
connection.server = server.server


# ------- FASTAPI APP -------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.sleep(0.5)
    asyncio.create_task(server.main_loop())
    yield


app = FastAPI(lifespan=lifespan)


# ------- WEBSOCKET -------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(uuid.uuid4())[:8]
    await connection.server.connect(websocket, client_id)

    while True:
        try:
            while connection.server.game_status != "Game end":
                if len(connection.server.all_players) == PLAYERS:
                    connection.server.ev_lobby_full.set()

                await connection.server.ev_players_start_choose.wait()

                while connection.server.game_status == "player_choose":
                    raw_msg = await websocket.receive_text()
                    msg = json.loads(raw_msg)
                    action_type = msg.get("type")

                    if action_type == "change_partner" and client_id not in connection.server.changing_players:
                        await connection.server.send_status(client_id, "You decided to change partner")
                        connection.server.changing_players.append(client_id)

                        if len(connection.server.changing_players) == PLAYERS:
                            connection.server.ev_players_choose_finish.set()

        except WebSocketDisconnect:
            await connection.server.disconnect(client_id)
        except Exception as e:
            print(f"Error: {e}")

# Serve static files (index.html etc.)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# ------- RUN SERVER -------
if __name__ == "__main__":
    uvicorn.run("run:app", host="127.0.0.1", port=8000, reload=True)

from __future__ import annotations
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from test import Player
import uuid
import asyncio
import json
import uvicorn
import math
import random

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(main_loop())  # schedule main_loop in the correct loop
    yield  # control returns to FastAPI for normal startup
    # optional: cleanup code goes here

app = FastAPI(lifespan=lifespan)
### app.mount("/static", StaticFiles(directory="static"), name="static")# link to js and html 
# On veut que les fichiers du dossier static soient accessibles directement à la racine, au lieu d’un sous-dossier (sinon = confusion)
nb_classes = 10
players = 6
choose_time = 20

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

        #helper_vars
        self.sigmoid_proba = self.sigmoid_probability(1,5)

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
        
    def after_choose(self):
        # list de tous les ids de joueurs qui veulent changer = changing_players
        # list de tous les ids de joueurs actif = active_players
        remove=[]
        for id in self.changing_players:
            me = server.all_players[id]
            candidate_id = me.candidate_id
            #si je veux changer et mon candidat veux aussi changer
            if candidate_id in self.changing_players:
                me.partner = me.candidate
                me.partner_id = me.candidate_id
                me.courtship_timer =0
            else:# sinon je ne peux pas changer enlevé de la list pour changer
                remove.append(id)
        for id in remove:
            self.changing_players.remove(id)
        # pour tous les joueurs
        for player_id in self.active_players:
            me = server.all_players[player_id]
            partner_id = me.partner_id
            if partner_id in self.changing_players and not(me.id in self.changing_players):
                me.partner = None
                me.partner_id = None
                me.courtship_timer = -1
            else:
                if me.courtship_timer == -1:
                    me.courtship_timer = 0
                else:
                    me.courtship_timer += 1
    
    def sigmoid_probability(self,sigma :int, T :int, round_to=3)->tuple:
        ##retourne tuples des valeurs d'1 sigmoide avc 1 pas de tps de 1
        #T : absisse du pt d'inflexion
        #sigma : pente du pt d'inflexion
        #round_to : nb de decimales à qui l'on arrondit
        t=0
        L=[round(1/(1+math.exp(T*sigma)), round_to)]
        while L[t]<1:
            t+=1
            L.append(round(1/(1+math.exp(-1*sigma*(t-T))), round_to))
        return tuple(L)
    
    async def tryToMate(self)->bool:
        #id_individu: id de l'individu ds D
        #D:dict contenant individus
        #Tproba:tuple des proba de passer en mate
        pairs = []
        for id in self.active_players:
            if self.all_players[id].partner_id:
                if any(id in t for t in pairs):# if id in pairs
                    pass
                else:#if not in pairs add me and partnerto it
                    pairs.append((id,self.all_players[id].partner_id))
        for pair in pairs:
            me = self.all_players[pair[0]]
            partner = self.all_players[pair[1]]
            courtship_time = me.courtship_timer
            if me.partner_id:
                if not(courtship_time ==-1) and me.mating == "waiting":
                    proba =random.random()
                    mate_threachold = self.sigmoid_proba[courtship_time]
                    if proba < mate_threachold:
                        self.mating_players.append(me.id)
                        self.mating_players.append(partner.id)
                        self.active_players.remove(me.id)
                        self.active_players.remove(partner.id)

                        me.mating = "mate"
                        partner.mating = "mate"
                        await self.send_player_update(me.id)
                        await self.send_player_update(partner.id)
    
    def end_turn_clean_up(self):
        self.changing_players.clear()
        self.round += 1
        if len(self.active_players) == 0  or self.round == 10:
            server.game_status = "Game end"
        self.ev_players_choose_finish.clear()
        self.ev_players_start_choose.clear()

    def reset_game_state(self):
        # reset uniquement ce qui concerne la partie
        self.active_players.clear()
        for id,player in self.all_players.items():
            player.reset_player(nb_classes)
            self.active_players.append(id)
        self.mating_players.clear()
        self.previous_pairs.clear()
        self.current_pairs.clear()
        self.changing_players.clear()

        # réinitialise les variables de jeu
        self.game_status = "waiting for player"
        self.round = 0

        # réinitialise les events
        self.ev_lobby_full.clear()
        self.ev_players_start_choose.clear()
        self.ev_players_choose_finish.clear()

    async def end_game(self): # reinitialyse the server for a new start
        await self.broadcast("End of the game")
        await asyncio.sleep(3)
        self.reset_game_state()
            







server = Connectionserver()

async def give_all_new_candidate():
    #create pairs
    server.current_pairs = Player.encounter(server.active_players,avoid=server.previous_pairs)
    server.previous_pairs = server.current_pairs
    # change the value of candidat in player class
    for pair in server.current_pairs:
        id_1 = pair[0]
        id_2 = pair[1]
        server.all_players[id_1].candidate = server.all_players[id_2].value
        server.all_players[id_1].candidate_id = server.all_players[id_2].id
        server.all_players[id_2].candidate = server.all_players[id_1].value
        server.all_players[id_2].candidate_id = server.all_players[id_1].id
    #send the value of the candidate
    for id in server.active_players:
        await server.send_player_update(id)
    await server.broadcast("You got a new candidate")

async def choose_timer(time):
    for i in range(time):
        await asyncio.sleep(1)
        await server.broadcast(f"time remaining : {time-i} seconds")
    server.ev_players_choose_finish.set()

### On peut supprimer car StaticFiles(html=True) fait le boulot

#@app.get("/")
#def get_index():
    #with open("static/index.html") as f:
        #return HTMLResponse(f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(uuid.uuid4())[:8]  # assign unique ID
    await server.connect(websocket, client_id) #create player connection and class
    while True:
        while server.game_status != "Game end":
            if len(server.all_players) == players:# and server.game_status == "Waiting for player":
                server.ev_lobby_full.set()
            await server.ev_players_start_choose.wait()
            try:
                while server.game_status == "player_choose":
                    raw_msg = await websocket.receive_text()
                    msg = json.loads(raw_msg)  # parse JSON
                    action_type = msg.get("type")
                    if action_type == "change_partner" and not(client_id in server.changing_players):
                        await server.send_status(client_id,"You decided to change partner")
                        server.changing_players.append(client_id)
                        if len(server.changing_players) == players:
                            server.ev_players_choose_finish.set()
            except WebSocketDisconnect:# if disconnect
                await server.disconnect(client_id)
            except Exception as e: # if other error
                print(f"Error: {e}")

async def main_loop():
    while True:
        while server.game_status != "Game end":
            if len(server.all_players) != players:
                await server.ev_lobby_full.wait()
            await server.broadcast("Game Start")
            await server.broadcast(f"start of round {server.round}")
            await asyncio.sleep(3)
            await give_all_new_candidate()
            print(server.previous_pairs)
            timer = asyncio.create_task(choose_timer(choose_time))
            server.game_status = "player_choose"
            server.ev_players_start_choose.set()
            await server.ev_players_choose_finish.wait()
            timer.cancel()
            await server.broadcast("Choosing periode is over")
            server.after_choose()
            await server.tryToMate()
            server.end_turn_clean_up()
            await server.broadcast(f"end of round {server.round}")
            await asyncio.sleep(3)
            print(f"end of round {server.round}")
        await server.end_game()

app.mount("/", StaticFiles(directory="static", html=True), name="static") #Pour que index.html devienne la page d’accueil et que player.html + admin.html soient accessibles simplement
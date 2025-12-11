
from player_class import Player
from game_class import Game
from connections_class import Connections
import asyncio
import csv
import io

class Server:
    def __init__(self):
        self.message_queue = asyncio.Queue()
        self.connections = Connections()
        self.admin_id = None
        self.admin_page = "main_menu"
        self.games = {}
        self.lobby_state = "closed"

        self.ev_players_choose_finish = asyncio.Event()
        
        self.timer = 0
        self.game_results = []

    async def pre_game(self,client_id):
        await asyncio.sleep(0.05)
        await self.connections.update_value_all(client_id,{"lobby_status":(self.lobby_state,True)})



    # on client message recieve 
    async def join_lobby(self,client_id):
        if self.lobby_state == "opened":
            self.connections.lobby[0].append(client_id)
            await self.connections.change_page(client_id,"player_lobby")
            await asyncio.sleep(0.05)
            await self.connections.update_value_all(self.connections.websockets,{"players_connected":(f"Joueurs connectés : {len(self.connections.lobby.get(0, []))}",True)})

            

    async def become_admin(self,client_id,password):
        #print(self.admin_id)
        if password == 'password' and (self.admin_id == None or not(self.admin_id in self.connections.websockets)):
            self.admin_id = client_id
            self.connections.admin_id = client_id
            if self.admin_page == "main_menu":
                await self.connections.change_page(client_id,"admin")
                self.admin_page = "admin"
            else:
                await self.connections.change_page(client_id,self.admin_page)

            #print("is admin")

    async def create_lobby(self,client_id,parameters):
        #print(f"parameters{parameters}")
        self.lobby_state = "opened"
        await self.connections.update_value_all(self.connections.websockets,{"lobby_status":(self.lobby_state,True)})
        #print(self.lobby_state)
        self.admin_page = "admin_lobby"
        self.connections.lobby[0] = []
        self.connections.game = Game(parameters['NbClass'][0],parameters['nb_tours_saison'][0],parameters['TmaxTour'][0],parameters['sigma'][0],parameters['npt_moy_before_mating'][0],parameters['nb_bots'][0])
        self.connections.game.parameters = parameters
        await self.connections.change_page(client_id,"admin_lobby")

    # game functions
    async def start_game(self):
        if  not(len(self.connections.lobby[0])==0):
            self.connections.game.game_status = "active"
            self.lobby_state = "closed"
            await self.connections.update_value_all(self.connections.websockets,{"lobby_status":(self.lobby_state,True)})
            print("game start")
            await self.connections.change_page(self.admin_id,"admin_result")
            self.admin_page = "admin_result"
            await self.connections.change_page(self.connections.lobby[0],"player")
            await asyncio.sleep(2)
            await self.add_players_to_game()
            if (len(self.connections.lobby[0])+self.connections.game.bot_nb)%2 == 0:
                await self.add_bots_to_game(self.connections.game.bot_nb)
            else:
                await self.add_bots_to_game(self.connections.game.bot_nb+1)
            await self.connections.update_value_all(set(self.connections.lobby.get(0, [])),self.connections.game.parameters)
            await self.game_loop()
            await self.reset_all()

    async def add_bots_to_game(self,bot_nb):
        for i in range(bot_nb):
            self.connections.game.all_players[f"bot{i}"] = Player(10,f"bot{i}")
            self.connections.game.active_players.append(f"bot{i}")


    async def add_players_to_game(self):
        for client_id in self.connections.lobby[0]:
            self.connections.game.all_players[client_id] = Player(10,client_id)
            self.connections.game.active_players.append(client_id)
            await self.connections.update_value_all(client_id,self.connections.game.all_players[client_id].player_info())
            

    async def game_loop(self):
        while self.connections.game.game_status == "active":
            self.ev_players_choose_finish.clear()
            self.connections.game.changing_players.clear()
            self.connections.game.give_all_new_candidate()
            for id in self.connections.game.active_players:
                await self.connections.update_value_all(id,self.connections.game.all_players[id].player_info())
            self.timer = asyncio.create_task(self.start_timer(self.connections.game.choose_time))
            await self.ev_players_choose_finish.wait()
            self.timer.cancel()
            self.bot_choose()
            self.connections.game.after_choose()
            self.connections.game.tryToMate()
            self.connections.game.end_turn_clean_up()
            self.add_turn_stats_game()
            if len(self.connections.game.active_players) == 0  or self.connections.game.round_nb == self.connections.game.round :
                self.connections.game.game_status = "Game end"
            else:
                self.connections.game.game_status = "active"
    
    def bot_choose(self):
        for key,player in self.connections.game.all_players.items():
            if "bot" in key:
                if player.mating != "mate":
                    if player.partner:
                        if player.candidate > player.partner:
                            self.connections.game.changing_players.append(key)
                            player.accept_candidate = False
                    else:
                        self.connections.game.changing_players.append(key)
                        player.accept_candidate = False
                    

    async def start_timer(self,time):
        for i in range(time):
            await asyncio.sleep(1)
            print(i)
            await self.connections.update_value_all(set(self.connections.lobby.get(0, [])),{"status":(f"time remaining : {time-i} seconds",True)})
        self.connections.game.game_status = "choose_finish"
        self.ev_players_choose_finish.set()

    async def player_change_partner(self,client_id):
        print(self.connections.game.changing_players)
        if not client_id in self.connections.game.changing_players:
            self.connections.game.changing_players.append(client_id)
            self.connections.game.all_players[client_id].accept_candidate = False
            self.connections.game.all_players[client_id].mating = "candidate accepted"
            await self.connections.update_value_all(client_id,self.connections.game.all_players[client_id].player_info())
            #print("change")
            if len(self.connections.game.changing_players) == len(self.connections.game.active_players):
                self.ev_players_choose_finish.set()

    async def reset_all(self,all=False):
        # Cancel the timer if running
        if self.timer and not self.timer.done():
            self.timer.cancel()
            try:
                await self.timer
            except asyncio.CancelledError:
                pass
        
        self.game_results = self.connections.game.game_results

        await self.connections.change_page(self.admin_id, "admin_download")
        self.admin_page = "admin_download"
        # Reset lobby state
        self.lobby_state = "closed"
        await self.connections.update_value_all(self.connections.websockets,{"lobby_status":(self.lobby_state,True)})
        self.connections.lobby.clear()

        # Reset all games
        self.connections.game = None
        self.games = {}

        # Clear event
        self.ev_players_choose_finish.clear()

        # Send everyone to main_menu
        coros = []
        for client_id, ws in self.connections.websockets.items():
            if client_id != self.admin_id:  # do NOT move admin
                coros.append(self.connections.change_page(client_id, "main_menu"))
            elif all:
                self.admin_page = "main_menu"
                self.admin_id = None
                coros.append(self.connections.change_page(client_id, "main_menu"))
        
        if coros:
            await asyncio.gather(*coros)
        await self.connections.update_value_all(None,{"lobby_status":(self.lobby_state,True)})

    def add_turn_stats_game(self):
        for key,player in self.connections.game.all_players.items():
            line = {"my_valeur":player.value,
                    "my_id":player.id,
                    "partner_value":player.partner,
                    "partner_id":player.partner_id,
                    "candidate_value":player.candidate,
                    "candidate_id":player.candidate_id,
                    "accept_candidate":(True if not(player.accept_candidate)else False),
                    "courtship_timer":player.courtship_timer,
                    "pas de temps":self.connections.game.round}
            #print(line)
            self.connections.game.game_results.append(line)
            if player.mating != "mate":
                player.accept_candidate = True
    
    def get_game_result(self):
        """
        Returns a CSV in-memory file from game_results
        """
        print("game results:")
        #print(self.game_results)
        if not self.game_results:
            return None
        
        self.admin_page = "admin" 
        #print(self.admin_page)

        output = io.StringIO()
        fieldnames = self.game_results[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for player_info in self.game_results:
            writer.writerow(player_info)

        output.seek(0)
        return output

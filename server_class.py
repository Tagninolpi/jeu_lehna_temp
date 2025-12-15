
from player_class import Player
from game_class import Game
from connections_class import Connections
import asyncio
import csv
import io
from datetime import datetime

# central class of the programme
class Server:
    def __init__(self):
        # self.message_queue can be moved to observer_class.py
        self.message_queue = asyncio.Queue() # used in observer_class.py (not here) 
        self.connections = Connections()
        self.admin_id = None # id of the admin of the current game  1 admin at any time, set in server_class.py become_admin()
        self.admin_page = "main_menu" # current page of the admin (if he disconnects
        #when he reconnects he is sent back to the last page)
        self.lobby_state = "closed" # 1 unique lobby at any time

        self.ev_players_choose_finish = asyncio.Event() # used to stop the curretn loop and to wait for an event
        
        self.timer: asyncio.Task | None = None # référence to the timer (choosing periode of the players)
        
        self.game_results = [] # list of lists of dicts
        # result list for every "pas de temps" (pdt)
        # [[{data player 1 pdt1},{data player 2 pdt1}...],[{data player 1 pdt2},{data player 2 pdt2}...]...]
        
        self.parameters = {} # recieved from admin.html => main.js => observer_class.py=> here create_lobby() 

    async def pre_game(self,client_id): # not necessary can be deleted (to verify)
        await asyncio.sleep(1)
        await self.connections.update_value_all(client_id,{"lobby_status":(self.lobby_state,True)})


    async def join_lobby(self,client_id):
        # if lobby exists , append player,
        # send him to lobby page, update number of connected players (visual)
        if self.lobby_state == "opened":
            self.connections.lobby[0].append(client_id)
            await self.connections.change_page(client_id,"player_lobby")
            await asyncio.sleep(1)
            await self.connections.update_value_all(self.connections.websockets,{"players_connected":(f"Joueurs connectés : {len(self.connections.lobby.get(0, []))}",True)})
 

    async def become_admin(self,client_id,password):
        # right password set by default défaut (hard coded)
        # if good password and no admin exists or connected
        if password == 'password' and (self.admin_id == None or not(self.admin_id in self.connections.websockets)):
            self.admin_id = client_id
            self.connections.admin_id = client_id
            if self.admin_page == "main_menu":# normal connection
                await self.connections.change_page(client_id,"admin")
                self.admin_page = "admin"
            else: # admin was on page "self.admin_page" and disconnected
                await self.connections.change_page(client_id,self.admin_page)


    async def create_lobby(self,client_id,parameters):
        # admin create lobby, Game instance with selected parameters, change page
        self.lobby_state = "opened"
        await self.connections.update_value_all(self.connections.websockets,{"lobby_status":(self.lobby_state,True)})
        self.admin_page = "admin_lobby"
        self.connections.lobby[0] = []
        self.connections.game = Game(parameters['NbClass'][0],parameters['nb_tours_saison'][0],parameters['TmaxTour'][0],parameters['sigma'][0],parameters['npt_moy_before_mating'][0],parameters['nb_bots'][0])
        self.connections.game.parameters = parameters
        self.parameters = parameters # chosen parameters(or default)
        self.connections.game.last_chance_option = parameters['last_chance'][0]
        await self.connections.change_page(client_id,"admin_lobby")

    # start game
    #I.  from this point multiple functions used only for the game loop and results
    # (could be a seperate class to make it easier to understand)
    async def start_game(self):
        # at least 1 player or bot connected
        # the bots don't have WebSocket connections they only exist in the server) 
        if  not(len(self.connections.lobby[0])==0) or self.connections.game.bot_nb != 0 :
            self.connections.game.game_status = "active"
            self.lobby_state = "closed" # no one can join the game
            await self.connections.update_value_all(self.connections.websockets,{"lobby_status":(self.lobby_state,True)})
            # admin can oversee the Game in admin_result.html
            await self.connections.change_page(self.admin_id,"admin_result")
            self.admin_page = "admin_result"
            # send players form lobby to game page (player.html)
            await self.connections.change_page(self.connections.lobby[0],"player")
            await asyncio.sleep(2)
            # create player instance for every player, add them to the current game
            await self.add_players_to_game()
            # always even player count (if not add bot to make even)
            if (len(self.connections.lobby[0])+self.connections.game.bot_nb)%2 == 0:
                await self.add_bots_to_game(self.connections.game.bot_nb)
            else:
                await self.add_bots_to_game(self.connections.game.bot_nb+1)
            # update player visual (dependiing on the parametres chosen by the admin)
            # the admin chooses what the players see
            await self.connections.update_value_all(set(self.connections.lobby.get(0, [])),self.connections.game.parameters)
            # start main loop:
            # loop ends when all players mate
            # or "pas de temps" of the game reached
            # the admin can close teh game at anytime by pressing on the reset button
            await self.game_loop()
            # at the end of the game everyting is reset for the next game
            await self.reset_all()

    # can be moved to game_class.py (self.connections.lobby[0] needs to be passed as an argument)
    async def add_players_to_game(self):
        for client_id in self.connections.lobby[0]:
            self.connections.game.all_players[client_id] = Player(10,client_id)
            self.connections.game.active_players.append(client_id)
            await self.connections.update_value_all(client_id,self.connections.game.all_players[client_id].player_info(self.connections.game.parameters))
    # same as add_players_to_game()
    async def add_bots_to_game(self,bot_nb):
        for i in range(bot_nb):
            self.connections.game.all_players[f"bot{i}"] = Player(10,f"bot{i}")
            self.connections.game.active_players.append(f"bot{i}")

    async def game_loop(self): #main game loop
        while self.connections.game.game_status == "active":# exit flag set if end conditions true
            self.ev_players_choose_finish.clear()#reset event monitor
            self.connections.game.changing_players.clear()
            self.connections.game.give_all_new_candidate() 
            #update visuals of all players
            for id in self.connections.lobby[0]:
                await self.connections.update_value_all(id,self.connections.game.all_players[id].player_info(self.connections.game.parameters))
            # start choose timer
            self.timer = asyncio.create_task(self.start_timer(self.connections.game.choose_time))
            await self.ev_players_choose_finish.wait() # stop loop until event cleared:
            # timer finished or all players choose to change
            self.timer.cancel() # if timer not 0
            self.bot_choose()# calculate the choice of existing bots ( accept if candidate>partner)
            self.calculate_biais() # calculate the biais of the players (not bots)
            self.connections.game.after_choose() # based on the choises update the partners
            self.connections.game.tryToMate() # can culate probability => determine if mate (sigmoide curve)
            await self.new_admin_overview() # update amdin overview
            self.connections.game.end_turn_clean_up() # reset some value for the next turn
            # exit loop if all players mate or "pas de temps" max reached
            if len(self.connections.game.active_players) == 0  or self.connections.game.round_nb == self.connections.game.round :
                # add last data turn to the game results
                # if last chance para => set all pairs to mate
                self.add_turn_stats_game(last=self.connections.game.last_chance_option)
                self.connections.game.game_status = "Game end"
            else:
                # continue loop
                self.connections.game.game_status = "active"
                # add the data for every player of this turn to game results
                self.add_turn_stats_game()
    
    async def start_timer(self,time):
        for i in range(time):
            await asyncio.sleep(1)
            await self.connections.update_value_all(set(self.connections.lobby.get(0, [])),{"status":(f"Time remaining : {time-i} seconds",True)})
        self.connections.game.game_status = "choose_finish" # can be deleted (not be verified)
        self.ev_players_choose_finish.set()

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
    
    def calculate_biais(self): # could go in game class
        game = self.connections.game
        for id in game.active_players:
            #set change (choice) , curent partner (value), current candidate (value)
            change = True if id in game.changing_players else False
            partner = game.all_players[id].partner
            candidate = game.all_players[id].candidate
            if partner > candidate and change: # negative biais
                game.admin_overview["bias_neg_step"][0] += 1
            if partner < candidate and not(change): # positive biais
                game.admin_overview["bias_pos_step"][0] += 1
        # update the value for the admin overview
        game.admin_overview["bias_pos_total"][0] += game.admin_overview["bias_pos_step"][0]
        game.admin_overview["bias_neg_total"][0] += game.admin_overview["bias_neg_step"][0]


    async def new_admin_overview(self): # could go in game class
        game = self.connections.game
        # set mate, courtship and "celibataire" count
        court = 0
        mate = 0
        celib = 0
        for id,player in game.all_players.items():
            if player.courtship_timer == 0:
                mate += 1
            elif player.courtship_timer < 0:
                celib += 1
            else:
                court += 1
        game.admin_overview["players_courtship"][0] = court
        game.admin_overview["players_mate"][0] = mate
        game.admin_overview["players_single"][0] = celib

        # total player count (never changes)
        game.admin_overview["players_total"][0] = court + celib + mate
        
        # remaining ("pas de temps")
        game.admin_overview["steps_remaining"][0] = game.round_nb - game.round
        
        # update admin view
        await self.connections.update_value_all(self.admin_id,self.connections.game.admin_overview)
        
        # reset biais for next round (admin view not modified)
        game.admin_overview["bias_pos_step"][0] = 0
        game.admin_overview["bias_neg_step"][0] = 0


    def add_turn_stats_game(self,last = False):
        # for every player (and bot) add data to game results
        for key,player in self.connections.game.all_players.items():
            line = {"my_value":player.value,
                    "my_id":player.id,
                    "partner_value":player.partner,
                    "partner_id":player.partner_id,
                    "candidate_value":player.candidate,
                    "candidate_id":player.candidate_id,
                    # choise is inversed because it is saved as False if the player changes,
                    # false = hide button 
                    "accept_candidate":(False if player.accept_candidate else True),
                    # implement last chance option => set all courtship to mate
                    "courtship_timer":0 if (last and player.courtship_timer >= 0) else player.courtship_timer,
                    "pas de temps":self.connections.game.round}
            self.connections.game.game_results.append(line)
            # if mate => hide accept button
            if player.mating != "mate":
                player.accept_candidate = True
            else:
                player.accept_candidate = False
    
    async def reset_all(self,all=False):
        # Cancel the timer if running
        if self.timer and not self.timer.done():
            self.timer.cancel()
            try:
                await self.timer
            except asyncio.CancelledError:
                pass
        # get the game results from Game instance (in the future only the server can be used)
        # the game_results variable in Game can be deleted
        self.game_results = self.connections.game.game_results
        
        if all: # admin reset game
            self.admin_page = "main_menu"
            await self.connections.change_page(self.admin_id, "admin")
            self.game_results = []
            await self.connections.change_page(self.connections.lobby[0],"main_menu")
            await asyncio.sleep(1)
            await self.connections.update_value_all(None,{"lobby_status":(self.lobby_state,True)})
        else: # reset at the end of the game 
            # admin can dowload csv
            await self.connections.change_page(self.admin_id, "admin_download")
            self.admin_page = "admin_download"
            # players can see their game stats
            await self.connections.change_page(self.connections.lobby[0],"player_result")
            await asyncio.sleep(2.5)
            # update the values of the player_result page (for each player with their stats)
            await self.send_game_results()
        
        # Reset lobby state
        self.lobby_state = "closed"
        # delete lobby
        self.connections.lobby.clear()

        # delete Game instance
        self.connections.game = None

        # reset event manager
        self.ev_players_choose_finish.clear()
    

    async def send_game_results(self):

        players = self.get_stat_from_result()
        if players:
            for id,info in players.items():
                self.parameters["valeur_du_partenaire_obtenu"][0] = info["p_val"]
                self.parameters["nombre_de_joueurs_dans_ma_class"][0] = info["nb_p"]
                self.parameters["moyenne_valeur_partenaire_meme_classe"][0] = info["p_val_moy"]
                self.parameters["pourcentage_classe_ayant_partenaire"][0] = info["p_percent"]
                self.parameters["temps_pour_obtenir_partenaire"][0] = info["pas_to_mate"]
                self.parameters["nombre_de_rencontres"][0] = info["p_nb"]
                self.parameters["nombre_de_refus"][0] = info["p_fail"]
                self.parameters["nombre_d_acceptations"][0] = info["p_success"]
                self.parameters["rang_dans_sa_classe"][0] = info["p_rank"]
                await self.connections.update_value_all(id,self.parameters)
            self.parameters["valeur_du_partenaire_obtenu"][0] = 0
            self.parameters["nombre_de_joueurs_dans_ma_class"][0] = 0
            self.parameters["moyenne_valeur_partenaire_meme_classe"][0] = 0
            self.parameters["pourcentage_classe_ayant_partenaire"][0] = 0
            self.parameters["temps_pour_obtenir_partenaire"][0] = 0
            self.parameters["nombre_de_rencontres"][0] = 0
            self.parameters["nombre_de_refus"][0] = 0
            self.parameters["nombre_d_acceptations"][0] = 0
            self.parameters["rang_dans_sa_classe"][0] = 0


    def get_stat_from_result(self):
        players = {}
        nb_lines = len(self.game_results)
        nb_players = len(self.connections.game.all_players)
        nb_real_players = len(self.connections.lobby[0])
        nb_bots = nb_players-nb_real_players
        nb_pas = nb_lines/nb_players
        if nb_pas < 2:
            return None
        partner_value = {}
        for i in range(self.parameters['NbClass'][0]+1):
            partner_value[i]=[]
        for line in self.game_results[nb_lines-nb_players:]:
            print(line["my_id"])
            partner_value[line["my_value"]].append([line["my_id"],line["partner_value"],line["courtship_timer"]])
        print(partner_value)
        for value,p_list in partner_value.items():
            p_list = sorted(p_list,key=lambda x:x[1])
            print(f"{value} : {p_list}")
            sum_per_value = 0
            for items in p_list:
                if items[2] == 0:
                    sum_per_value += items[1]
            celib_count = 0
            for p in p_list:
                if p[1] == 0:
                    celib_count += 1
            for i,player in enumerate(p_list):
                if not "bot" in player[0]:
                    players[player[0]] = {
                        "p_val": 0,
                        "nb_p":0,
                        "p_val_moy": 0,
                        "p_percent": 0,
                        "pas_to_mate": 0,
                        "p_nb": "0",
                        "p_fail": 0,
                        "p_success": 0,
                        "p_rank": 0 
                        }
                    players[player[0]]["p_val"] = player[1]
                    players[player[0]]["nb_p"] = len(p_list)-1
                    players[player[0]]["p_val_moy"] = round(sum_per_value/len(p_list),1)
                    players[player[0]]["p_percent"] = f"{celib_count}/{len(p_list)}"
                    players[player[0]]["p_rank"] = len(p_list)-i
        real_players = {}
        for index,line in enumerate(self.game_results):
            id = line["my_id"]
            if not "bot" in id:
                if line["courtship_timer"] == 0 and self.game_results[index-nb_players]["courtship_timer"] != 0:
                    players[id]["pas_to_mate"]= self.game_results[index-nb_players]["courtship_timer"]
                if id in real_players:
                    players[id]["p_nb"] = line["my_value"]
                    if line["accept_candidate"]:
                        if line["partner_id"] == line["candidate_id"]:
                            real_players[id]["success"] += 1
                        else:
                            real_players[id]["fail"] += 1
                    real_players[id]["prev_partner_id"] = line["partner_id"]
                else:
                    real_players[id] = {
                        "court_nb":0,
                        "fail":0,
                        "success":0,
                        "prev_partner_id":"0"
                        }
        print(real_players)
        for id,stats in real_players.items():
            players[id]["p_fail"] = stats["fail"]
            players[id]["p_success"] = stats["success"]


        return players

    ### END of Game loop functions


        
    async def player_change_partner(self,client_id): # player clicked accept candidate button
        if not client_id in self.connections.game.changing_players:
            self.connections.game.changing_players.append(client_id)
            self.connections.game.all_players[client_id].accept_candidate = False 
            # False = hide button (in the server a conversion is done to make it True)
            self.connections.game.all_players[client_id].mating = "candidate accepted"
            await self.connections.update_value_all(client_id,self.connections.game.all_players[client_id].player_info(self.connections.game.parameters))
            # if all players have chosen unlock event manager => continue main game loop
            if len(self.connections.game.changing_players) == len(self.connections.game.active_players):
                self.ev_players_choose_finish.set()
    
    async def leave_lobby(self,client_id):
        # remove player from lobby, go to main menu, update connected player count
        self.connections.lobby[0].remove(client_id)
        await self.connections.change_page(client_id,"main_menu")
        await asyncio.sleep(1)
        await self.connections.update_value_all(self.connections.websockets,{"players_connected":(f"Joueurs connectés : {len(self.connections.lobby.get(0, []))}",True)})

    async def leave_game(self,client_id):
        # on player result page (go to main menu)
        # (the visual for the player stats are deleted)
        await self.connections.change_page(client_id,"main_menu")
    
    def get_game_result(self):
        # return csv file and it's name (date and time of creation)
        # used in app.py 
        if not self.game_results:
            return None, None # if no game results create empty csv

        output = io.StringIO()

        # --- 0. Header for the parameter section ---
        output.write("Parameter,Value,Visible_to_player\n")

        # --- 1. Write CSV creation timestamp ---
        now = datetime.now()
        output.write(f"csv_created_at,{now.isoformat()},NA\n")

        # --- 2. Write game parameters including visibility ---
        # self.parameters = {'NbClass': [10, False], 'id': False, ...}
        for key, val in self.parameters.items():
            if isinstance(val, list):
                value, visible = val
            else:
                # Only visibility provided → set value to "NA"
                value = "NA"
                visible = val if isinstance(val, bool) else False
            output.write(f"{key},{value},{visible}\n")

        # Blank line before table
        output.write("\n")

        # --- 3. Write the game results table ---
        if not self.game_results:
            return None, None  # nothing to save

        fieldnames = list(self.game_results[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for row in self.game_results:
            writer.writerow(row)

        # Reset pointer and create filename
        output.seek(0)
        file_name = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_game_results.csv"

        # delete all results AFTER generating the CSV
        self.game_results = []

        return output, file_name
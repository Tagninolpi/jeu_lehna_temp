
from player_class import Player
from game_class import Game
from connections_class import Connections
import asyncio
import csv
import io
from datetime import datetime

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
        self.parameters = {}

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
        self.parameters = parameters
        self.connections.game.last_chance_option = parameters['last_chance'][0]
        #print(f"00000 : {parameters}")
        await self.connections.change_page(client_id,"admin_lobby")

    ###
    async def start_game(self):
        if  not(len(self.connections.lobby[0])==0) or self.connections.game.bot_nb != 0 :
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

    async def add_players_to_game(self):
        for client_id in self.connections.lobby[0]:
            self.connections.game.all_players[client_id] = Player(10,client_id)
            self.connections.game.active_players.append(client_id)
            await self.connections.update_value_all(client_id,self.connections.game.all_players[client_id].player_info(self.connections.game.parameters))

    async def add_bots_to_game(self,bot_nb):
        for i in range(bot_nb):
            self.connections.game.all_players[f"bot{i}"] = Player(10,f"bot{i}")
            self.connections.game.active_players.append(f"bot{i}")

    async def game_loop(self):
        while self.connections.game.game_status == "active":
            self.ev_players_choose_finish.clear()
            self.connections.game.changing_players.clear()
            self.connections.game.give_all_new_candidate()
            for id in self.connections.game.active_players:
                await self.connections.update_value_all(id,self.connections.game.all_players[id].player_info(self.connections.game.parameters))
            self.timer = asyncio.create_task(self.start_timer(self.connections.game.choose_time))
            await self.ev_players_choose_finish.wait()
            self.timer.cancel()
            self.bot_choose()
            self.calculate_biais()
            self.connections.game.after_choose()
            self.connections.game.tryToMate()
            await self.new_admin_overview()
            self.connections.game.end_turn_clean_up()
            if len(self.connections.game.active_players) == 0  or self.connections.game.round_nb == self.connections.game.round :
                self.add_turn_stats_game(last=self.connections.game.last_chance_option)
                self.connections.game.game_status = "Game end"
            else:
                self.connections.game.game_status = "active"
                self.add_turn_stats_game()
    
    async def start_timer(self,time):
        for i in range(time):
            await asyncio.sleep(1)
            #print(i)
            await self.connections.update_value_all(set(self.connections.lobby.get(0, [])),{"status":(f"time remaining : {time-i} seconds",True)})
        self.connections.game.game_status = "choose_finish"
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
    
    def calculate_biais(self):
        game = self.connections.game
        for id in game.active_players:
            change = True if id in game.changing_players else False
            partner = game.all_players[id].partner
            candidate = game.all_players[id].candidate
            if partner > candidate and change:
                game.admin_overview["bias_neg_step"][0] += 1
            if partner < candidate and not(change):
                game.admin_overview["bias_pos_step"][0] += 1
        game.admin_overview["bias_pos_total"][0] += game.admin_overview["bias_pos_step"][0]
        game.admin_overview["bias_neg_total"][0] += game.admin_overview["bias_neg_step"][0]


    async def new_admin_overview(self):
        game = self.connections.game
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
        game.admin_overview["players_total"][0] = court + celib + mate
        game.admin_overview["steps_remaining"][0] = game.round_nb - game.round
        await self.connections.update_value_all(self.admin_id,self.connections.game.admin_overview)
        game.admin_overview["bias_pos_step"][0] = 0
        game.admin_overview["bias_neg_step"][0] = 0


    def add_turn_stats_game(self,last = False):
        for key,player in self.connections.game.all_players.items():
            line = {"my_value":player.value,
                    "my_id":player.id,
                    "partner_value":player.partner,
                    "partner_id":player.partner_id,
                    "candidate_value":player.candidate,
                    "candidate_id":player.candidate_id,
                    "accept_candidate":(True if not(player.accept_candidate)else False),
                    "courtship_timer":0 if (last and player.courtship_timer >= 0) else player.courtship_timer,
                    "pas de temps":self.connections.game.round}
            #print(line)
            self.connections.game.game_results.append(line)
            if player.mating != "mate":
                player.accept_candidate = True
    
    async def reset_all(self,all=False):
        # Cancel the timer if running
        if self.timer and not self.timer.done():
            self.timer.cancel()
            try:
                await self.timer
            except asyncio.CancelledError:
                pass
        
        self.game_results = self.connections.game.game_results
        if all:
            self.admin_page = "main_menu"
            await self.connections.change_page(self.admin_id, "admin")
            self.game_results = []
            await self.connections.change_page(self.connections.lobby[0],"main_menu")
            await asyncio.sleep(0.05)
            await self.connections.update_value_all(None,{"lobby_status":(self.lobby_state,True)})
        else:
            await self.connections.change_page(self.admin_id, "admin_download")
            self.admin_page = "admin_download"
            await self.connections.change_page(self.connections.lobby[0],"player_result")
            await asyncio.sleep(0.5)
            await self.send_game_results()
        # Reset lobby state
        self.lobby_state = "closed"
        
        
        self.connections.lobby.clear()

        # Reset all games
        self.connections.game = None
        self.games = {}

        # Clear event
        self.ev_players_choose_finish.clear()
    ###
    async def send_game_results(self):
        #print(self.game_results)
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
                    


        


    async def player_change_partner(self,client_id):
        #print(self.connections.game.changing_players)
        if not client_id in self.connections.game.changing_players:
            self.connections.game.changing_players.append(client_id)
            self.connections.game.all_players[client_id].accept_candidate = False
            self.connections.game.all_players[client_id].mating = "candidate accepted"
            await self.connections.update_value_all(client_id,self.connections.game.all_players[client_id].player_info(self.connections.game.parameters))
            #print("change")
            if len(self.connections.game.changing_players) == len(self.connections.game.active_players):
                self.ev_players_choose_finish.set()
    
    async def leave_lobby(self,client_id):
        self.connections.lobby[0].remove(client_id)
        await self.connections.change_page(client_id,"main_menu")
        await asyncio.sleep(0.05)
        await self.connections.update_value_all(self.connections.websockets,{"players_connected":(f"Joueurs connectés : {len(self.connections.lobby.get(0, []))}",True)})

    async def leave_game(self,client_id):
        await self.connections.change_page(client_id,"main_menu")
    
    def get_game_result(self):
        """
        Returns a CSV in-memory file from game_results,
        with game parameters (including visibility) at the top,
        and a file name based on date and time.
        """
        if not self.game_results:
            return None, None  # return tuple for CSV and file name

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

        # 🔥 delete all results AFTER generating the CSV
        self.game_results = []

        return output, file_name
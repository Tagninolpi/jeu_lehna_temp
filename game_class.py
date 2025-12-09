import numpy as np
import math
import random
import asyncio
class Game:
    def __init__(self,player_value_class_nb:int,nb_round:int,time_to_choose_new_partner:int,sigmoid_sigma:float,sigmoid_turn_to_mate:float):

        #Player dict : {id,class}  
        self.all_players = {}

        #Player id list : [P1_id,P2_id, ... ]
        self.active_players = []
        self.mating_players = []
        self.changing_players = []
 
        #Player id pairs list : [(p1_id,p3_id),(p2_id,p4_id), ... ]
        self.previous_pairs = []
        self.current_pairs = []
        
        #Game parameters :
        self.nb_classes = int(player_value_class_nb)
        self.players = 10
        self.choose_time = int(time_to_choose_new_partner)
        self.sigmoid_proba_sigma = float(sigmoid_sigma)
        self.sigmoid_proba_turn_to_mate = float(sigmoid_turn_to_mate)

        self.parameters = {}

        self.round_nb = int(nb_round)

        self.sigmoid_proba_decimal_nb = 3
        self.round = 0
        self.game_status = "active"

        self.sigmoid_proba = self.sigmoid_probability()

        self.game_results = []

    def sigmoid_probability(self)->tuple:
        t=0
        L=[round(1/(1+math.exp(self.sigmoid_proba_turn_to_mate*self.sigmoid_proba_sigma)), 3)]
        while L[t]<1:
            L.append(round(1/(1+math.exp(-1*self.sigmoid_proba_sigma*(t-self.sigmoid_proba_turn_to_mate))), self.sigmoid_proba_decimal_nb))
            t+=1
        return tuple(L)

    def give_all_new_candidate(self):
        #create pairs
        self.current_pairs = self.encounter()
        self.previous_pairs = self.current_pairs
        # change the value of candidat in player class
        for pair in self.current_pairs:
            id_1 = pair[0]
            id_2 = pair[1]
            self.all_players[id_1].candidate = self.all_players[id_2].value
            self.all_players[id_1].candidate_id = self.all_players[id_2].id
            self.all_players[id_2].candidate = self.all_players[id_1].value
            self.all_players[id_2].candidate_id = self.all_players[id_1].id


        #for id in self.active_players:
        #    await server.send_player_update(id)
        #await server.broadcast("You got a new candidate")

    def encounter(self):
        rng = np.random.default_rng()

        def pair_from_ids(lst: list[str]):
            return [(lst[i], lst[i+1]) for i in range(0, len(lst) - len(lst) % 2, 2)]

        if not self.previous_pairs:
            rng.shuffle(self.active_players)
            return pair_from_ids(self.active_players)

        avoid_norm = {tuple(sorted(x)) for x in self.previous_pairs}
        for _ in range(20): 
            rng.shuffle(self.active_players)
            pairs = pair_from_ids(self.active_players)
            if all(tuple(sorted(p)) not in avoid_norm for p in pairs):
                return pairs
        return pair_from_ids(self.active_players)
    
    def after_choose(self):
        # list de tous les ids de joueurs qui veulent changer = changing_players
        # list de tous les ids de joueurs actif = active_players
        remove=[]
        for id in self.changing_players:
            me = self.all_players[id]
            candidate_id = me.candidate_id
            #si je veux changer et mon candidat veux aussi changer
            if candidate_id in self.changing_players:
                me.partner = me.candidate
                me.partner_id = me.candidate_id
                me.courtship_timer = "c"
            else:# sinon je ne peux pas changer enlevé de la list pour changer
                remove.append(id)
        for id in remove:
            self.changing_players.remove(id)
        # pour tous les joueurs
        for player_id in self.active_players:
            me = self.all_players[player_id]
            partner_id = me.partner_id
            # mon partenaire change mais pas moi
            if partner_id in self.changing_players and not(me.id in self.changing_players):
                me.partner = None
                me.partner_id = None
                me.courtship_timer = -1
            else:
                # rien ne change
                #je devien courtship    
                if me.courtship_timer == "c":
                    me.courtship_timer = 1
                    #je suis celib 
                elif me.courtship_timer <= 0:
                    me.courtship_timer -= 1
                    #courtship
                else:
                    me.courtship_timer += 1
                
    def tryToMate(self)->bool:
        pairs = []
        for id in self.active_players:
            if self.all_players[id].partner_id:
                if any(id in t for t in pairs):# if id in pairs
                    pass
                else:#if not in pairs add me and partner to it
                    pairs.append((id,self.all_players[id].partner_id))
        for pair in pairs:
            me = self.all_players[pair[0]]
            partner = self.all_players[pair[1]]
            courtship_time = me.courtship_timer
            if me.partner_id:
                if courtship_time >0 and me.mating != "mate":
                    proba =random.random()
                    mate_threachold = self.sigmoid_proba[courtship_time]
                    if proba < mate_threachold:
                        self.mating_players.append(me.id)
                        self.mating_players.append(partner.id)
                        self.active_players.remove(me.id)
                        self.active_players.remove(partner.id)
                        me.mating = "mate"
                        partner.mating = "mate"
                        me.courtship_timer = 0
                        partner.courtship_timer = 0
                        return me.id,partner.id
        return 0,0
                    
    def end_turn_clean_up(self):
        self.changing_players.clear()
        self.round += 1
        print(self.round)
        for id,player in self.all_players.items():
            if player.mating != "mate":
                player.mating = "waiting"


        #if len(self.active_players) == 0  or self.round == 10:
            #server.game_status = "Game end"
        #self.ev_players_choose_finish.clear()
        #self.ev_players_start_choose.clear()
    
    def reset_game_state(self):
        # reset uniquement ce qui concerne la partie
        self.active_players.clear()
        for id,player in self.all_players.items():
            player.reset_player(self.nb_classes)
            self.active_players.append(id)
        self.mating_players.clear()
        self.previous_pairs.clear()
        self.current_pairs.clear()
        self.changing_players.clear()

        # réinitialise les variables de jeu
        self.game_status = "waiting for player"
        self.round = 0



        # réinitialise les events
        #self.ev_lobby_full.clear()
        #self.ev_players_start_choose.clear()
        #self.ev_players_choose_finish.clear()


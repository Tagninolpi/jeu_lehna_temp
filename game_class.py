import numpy as np
import math
import random
import asyncio
class Game:
    def __init__(self,player_value_class_nb:int,nb_round:int,time_to_choose_new_partner:int,sigmoid_sigma:float,sigmoid_turn_to_mate:float,bot_nb:int):

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

        self.bot_nb = bot_nb

    def sigmoid_probability(self)->tuple:
        t=0
        L=[round(1/(1+math.exp(self.sigmoid_proba_turn_to_mate*self.sigmoid_proba_sigma)), 3)]
        while L[t]<1:
            L.append(round(1/(1+math.exp(-1*self.sigmoid_proba_sigma*(t-self.sigmoid_proba_turn_to_mate))), self.sigmoid_proba_decimal_nb))
            t+=1
        #print(L)
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

        # 1. Shuffle once
        rng.shuffle(self.active_players)
        current_pairs = pair_from_ids(self.active_players)

        if len(current_pairs) == 1:
            # Only 2 players left, keep the single pair as is
            self.previous_pairs = current_pairs.copy()
            return current_pairs

        # 2. Separate good and bad pairs
        prev_set = set(self.previous_pairs)
        good_pairs = []
        bad_pairs = []
        for p in current_pairs:
            if p in prev_set:
                bad_pairs.append(p)
            else:
                good_pairs.append(p)
        #print(f"good{len(good_pairs)}, bad{len(bad_pairs)}")

        # 3. Fix bad pairs
        i = 0
        while i < len(bad_pairs):
            bad = bad_pairs[i]
            first_bad = bad[0]

            if good_pairs:
                # Swap with a random good pair as before
                idx = random.randrange(len(good_pairs))
                first_good, second_good = good_pairs[idx]

                # Swap first elements
                new_good_pair = (first_bad, second_good)
                new_bad_pair = (first_good, bad[1])

                # Replace the chosen good pair with the new one
                good_pairs[idx] = new_good_pair
                # Add the fixed bad pair to good_pairs
                good_pairs.append(new_bad_pair)
                i += 1
            else:
                # No good pairs, swap with the next bad pair (if exists)
                if i + 1 < len(bad_pairs):
                    next_bad = bad_pairs[i + 1]
                    first_next_bad, second_next_bad = next_bad

                    # Swap first elements
                    new_pair_1 = (first_bad, second_next_bad)
                    new_pair_2 = (first_next_bad, bad[1])

                    # Remove the next bad pair and add both fixed pairs to good_pairs
                    bad_pairs.pop(i + 1)
                    good_pairs.extend([new_pair_1, new_pair_2])
                    i += 1  # Skip current as it's now handled
                else:
                    # Last bad pair, nothing to swap with, keep as-is
                    good_pairs.append(bad)
                    i += 1

        # 4. Result
        current_pairs = good_pairs

        # Optional check
        assert all(p not in prev_set for p in current_pairs), "Some pairs still overlap!"

        # Update previous pairs
        self.previous_pairs = current_pairs.copy()
        return current_pairs


        

    """ 
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
        return pair_from_ids(self.active_players) """
    
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
                me.courtship_timer = -999999
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
                me.partner = -1
                me.partner_id = 0
                me.courtship_timer = -1
            else:
                # rien ne change
                #je devien courtship    
                if me.courtship_timer == -999999:
                    me.courtship_timer = 1
                    #je suis celib 
                elif me.courtship_timer <= 0:
                    me.courtship_timer -= 1
                    #courtship
                else:
                    me.courtship_timer += 1
                
    def tryToMate(self)->bool:
        print(f"activeplayer {len(self.active_players)}")
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
                    #print(courtship_time)
                    if courtship_time < len(self.sigmoid_proba):
                        mate_threachold = self.sigmoid_proba[courtship_time]
                    else:
                        mate_threachold = 1.3 
                     
                    if proba < mate_threachold:                            
                        self.mating_players.append(me.id)
                        self.mating_players.append(partner.id)
                        self.active_players.remove(me.id)
                        self.active_players.remove(partner.id)
                        me.mating = "mate"
                        partner.mating = "mate"
                        me.courtship_timer = 0
                        partner.courtship_timer = 0

    def end_turn_clean_up(self):
        self.changing_players.clear()
        self.round += 1
        print(f"round{self.round}")
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


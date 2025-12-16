import numpy as np
import math
import random
import asyncio
class Game:
    def __init__(self,player_value_class_nb:int,nb_round:int,time_to_choose_new_partner:int,sigmoid_sigma:float,sigmoid_turn_to_mate:float,bot_nb:int):

        #Player dict : {id,class}  
        self.all_players = {}

        #Player id list : [P1_id,P2_id, ... ]
        self.active_players = [] #list of non-mating player (in a state of courtship or single)
        self.mating_players = []
        self.changing_players = [] #list of player who want to change their partner for the candidate partner
 
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
        self.last_chance_option = False
        self.bot_nb = bot_nb

        self.admin_overview = {
            "bias_pos_step":[0,True],
            "bias_neg_step":[0,True],
            "players_courtship":[0,True],
            "players_mate":[0,True],
            "players_single":[0,True],
            "players_total":[0, True],
            "bias_pos_total":[0,True],
            "bias_neg_total":[0,True],
            "steps_remaining":[0,True]
            }


    def sigmoid_probability(self)->tuple:
        #return the probability distribution to move up to "mate" state depending on the time passed in "courtship" state
        #in the form of a tuple of probability with one probability for each step of time until the probability is equal to one
        t=0
        L=[round(1/(1+math.exp(self.sigmoid_proba_turn_to_mate*self.sigmoid_proba_sigma)), 3)]
        while L[t]<1:
            L.append(round(1/(1+math.exp(-1*self.sigmoid_proba_sigma*(t-self.sigmoid_proba_turn_to_mate))), self.sigmoid_proba_decimal_nb))
            t+=1
        return tuple(L)

    def give_all_new_candidate(self):
        #create new pairs (different from the previous turn)
        self.current_pairs = self.encounter()
        self.previous_pairs = self.current_pairs
        # change the value and id of each player's candidate
        for pair in self.current_pairs:
            id_1 = pair[0]
            id_2 = pair[1]
            self.all_players[id_1].candidate = self.all_players[id_2].value
            self.all_players[id_1].candidate_id = self.all_players[id_2].id
            self.all_players[id_2].candidate = self.all_players[id_1].value
            self.all_players[id_2].candidate_id = self.all_players[id_1].id


    def encounter(self): #to each player associate randomly a candidate partner (different from the previous turn)
        rng = np.random.default_rng()

        def pair_from_ids(lst: list[str]):
            # from a list of ids return a list of pairs ex. [id1,id3,id2,id4] => [(id1,id3),(id2,id4)]
            #in the case where the number of player is odd (len(lst) % 2!=0) the last player id is ignored
            return [(lst[i], lst[i+1]) for i in range(0, len(lst) - len(lst) % 2, 2)]

        if not self.previous_pairs: # if first time in the game : 
            #no previous turn so no need to take into account the previous pairing
            rng.shuffle(self.active_players)
            return pair_from_ids(self.active_players)

        # 1. Shuffle once
        rng.shuffle(self.active_players) #randomly rearrange active players => [id1,id3,id2,id4]
        current_pairs = pair_from_ids(self.active_players) # => [(id1,id3),(id2,id4)]

        if len(current_pairs) == 1:
            # Only 2 players left, keep the single pair as is
            self.previous_pairs = current_pairs.copy()
            return current_pairs

        # 2. Separate good and bad pairs
        #a pair is bad if and only if it already existed in the previous step of time
        prev_set = set(self.previous_pairs) # (id1,id3) = (id3,id1)
        good_pairs = []
        bad_pairs = []
        for p in current_pairs:
            if p in prev_set:
                bad_pairs.append(p)
            else:
                good_pairs.append(p)

        # 3. Fix bad pairs
        i = 0
        while i < len(bad_pairs):
            bad = bad_pairs[i]
            first_bad, second_bad = bad

            if good_pairs:
                # Fix bad pair using an existing good pair
                idx = random.randrange(len(good_pairs))
                first_good, second_good = good_pairs[idx]

                good_pairs[idx] = (first_bad, second_good)
                good_pairs.append((first_good, second_bad))
                i += 1

            else:
                # No good pairs yet
                if i + 1 < len(bad_pairs):
                    # Use the next bad pair
                    next_bad = bad_pairs[i + 1]
                    first_next, second_next = next_bad

                    good_pairs.append((first_bad, second_next))
                    good_pairs.append((first_next, second_bad))
                    i += 2  # Skip both bad pairs
                else:
                    # Only possible when len(bad_pairs) == 1
                    good_pairs.append(bad)
                    i += 1

        # 4. Result
        current_pairs = good_pairs

        # Optional check
        assert all(p not in prev_set for p in current_pairs), "Some pairs still overlap!"

        # Update previous pairs
        self.previous_pairs = current_pairs.copy()
        return current_pairs

    
    def after_choose(self):
        #update the state of each player depending on their choices (change or not)
        remove=[]

        # sort the players depending on if they can actually change (bilateral choice)
        for id in self.changing_players:
            me = self.all_players[id]
            candidate_id = me.candidate_id

            # I want to change and my candidate also wants to change
            if candidate_id in self.changing_players:
                me.partner = me.candidate
                me.partner_id = me.candidate_id
                me.courtship_timer = -999999 #tmp value to mark this player as in courtship state for this step onwards
            
            else:# candidate doesn't want to change remove me from changing player
                remove.append(id)

        #remove the players from changing
        for id in remove:
            self.changing_players.remove(id)

        # for every player (not mate)
        for player_id in self.active_players:
            me = self.all_players[player_id]
            partner_id = me.partner_id

            # my partner changes but i don't
            if partner_id in self.changing_players and not(me.id in self.changing_players):
                
                # become celib
                me.partner = 0
                me.partner_id = "0"
                me.courtship_timer = -1
                
            else: # nothing changes

                if me.courtship_timer == -999999: # i accepted candidate and they accepted me 
                    # => start courtship
                    me.courtship_timer = 1

                elif me.courtship_timer <= 0: # i am celib
                    me.courtship_timer -= 1

                else: # i am in a courtship
                    me.courtship_timer += 1
                
    def tryToMate(self)->bool:
        '''
        some parts of this function are repetitive and not neccessary
        '''
        #for each player in courstship state apply a probability to move up to mating state

        pairs = []# this pair list might already exist (encounter)
        for id in self.active_players: #register pairs with couples in the form of tuples (id_X, id_partner_of_X)
            if self.all_players[id].partner_id:
                if any(id in t for t in pairs):# if id in pairs
                    pass
                else:#if not in pairs add me and partner to it
                    pairs.append((id,self.all_players[id].partner_id))

        for pair in pairs:
            me = self.all_players[pair[0]]
            courtship_time = me.courtship_timer
            if me.partner_id != "0": # i am not celib
                partner = self.all_players[pair[1]]
                #if in a 'courtship' state (not single (courtship_time<0) or mate (mating = "mate"))
                if courtship_time >0 and me.mating != "mate":
                    proba =random.random()
                    if courtship_time < len(self.sigmoid_proba):
                        mate_threachold = self.sigmoid_proba[courtship_time]
                    else:
                        mate_threachold = 1.3 #if courtship_time>len(self.sigmoid_proba)-->move up to 'mate' state
                     
                    if proba < mate_threachold: #move up to 'mate' state                         
                        self.mating_players.append(me.id)
                        self.mating_players.append(partner.id)
                        #a player in 'mate' state is no longer active
                        self.active_players.remove(me.id)
                        self.active_players.remove(partner.id)
                        me.mating = "mate"
                        partner.mating = "mate"
                        me.courtship_timer = 0
                        partner.courtship_timer = 0

    def end_turn_clean_up(self): #
        self.changing_players.clear()
        self.round += 1
        print(f"round{self.round}")
        for id,player in self.all_players.items():
            if player.mating != "mate":
                player.mating = "waiting"

    
    def reset_game_state(self):
        # reset what is linked only to the game
        self.active_players.clear()
        for id,player in self.all_players.items():
            player.reset_player(self.nb_classes)
            self.active_players.append(id)
        self.mating_players.clear()
        self.previous_pairs.clear()
        self.current_pairs.clear()
        self.changing_players.clear()

        # reset game variables
        self.game_status = "waiting for player"
        self.round = 0

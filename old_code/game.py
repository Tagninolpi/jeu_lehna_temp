import math
import random
import asyncio


def after_choose(server):
    remove = []
    for id in server.changing_players:
        me = server.all_players[id]
        candidate_id = me.candidate_id
        if candidate_id in server.changing_players:
            me.partner = me.candidate
            me.partner_id = me.candidate_id
            me.courtship_timer = 0
        else:
            remove.append(id)
    for id in remove:
        server.changing_players.remove(id)

    for player_id in server.active_players:
        me = server.all_players[player_id]
        partner_id = me.partner_id
        if partner_id in server.changing_players and not (me.id in server.changing_players):
            me.partner = None
            me.partner_id = None
            me.courtship_timer = -1
        else:
            if me.courtship_timer == -1:
                me.courtship_timer = 0
            else:
                me.courtship_timer += 1



def sigmoid_probability(sigma: int, T: int, round_to=3) -> tuple:
    t = 0
    L = [round(1 / (1 + math.exp(T * sigma)), round_to)]
    while L[t] < 1:
        t += 1
        L.append(round(1 / (1 + math.exp(-1 * sigma * (t - T))), round_to))
    return tuple(L)



async def tryToMate(server) -> bool:
    pairs = []
    for id in server.active_players:
        if server.all_players[id].partner_id:
            if any(id in t for t in pairs):
                pass
            else:
                pairs.append((id, server.all_players[id].partner_id))
    for pair in pairs:
        me = server.all_players[pair[0]]
        partner = server.all_players[pair[1]]
        courtship_time = me.courtship_timer
        if me.partner_id:
            if not (courtship_time == -1) and me.mating == "waiting":
                proba = random.random()
                mate_threachold = server.sigmoid_proba[courtship_time]
                if proba < mate_threachold:
                    server.mating_players.append(me.id)
                    server.mating_players.append(partner.id)
                    server.active_players.remove(me.id)
                    server.active_players.remove(partner.id)

                    me.mating = "mate"
                    partner.mating = "mate"
                    await server.send_player_update(me.id)
                    await server.send_player_update(partner.id)



def end_turn_clean_up(server):
    server.changing_players.clear()
    server.round += 1
    if len(server.active_players) == 0 or server.round == 10:
        server.game_status = "Game end"
    server.ev_players_choose_finish.clear()
    server.ev_players_start_choose.clear()



def reset_game_state(server, nb_classes):
    server.active_players.clear()
    for id, player in server.all_players.items():
        player.reset_player(nb_classes)
        server.active_players.append(id)
    server.mating_players.clear()
    server.previous_pairs.clear()
    server.current_pairs.clear()
    server.changing_players.clear()

    server.game_status = "waiting for player"
    server.round = 0

    server.ev_lobby_full.clear()
    server.ev_players_start_choose.clear()
    server.ev_players_choose_finish.clear()



async def end_game(server, nb_classes):
    await server.broadcast("End of the game")
    await asyncio.sleep(3)
    reset_game_state(server, nb_classes)

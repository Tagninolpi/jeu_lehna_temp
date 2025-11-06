import asyncio
import game
players = None
choose_time = None
nb_classes = None
server = None
from test import Player

async def give_all_new_candidate():
    server.current_pairs = Player.encounter(server.active_players,avoid=server.previous_pairs)
    server.previous_pairs = server.current_pairs
    for pair in server.current_pairs:
        id_1 = pair[0]
        id_2 = pair[1]
        server.all_players[id_1].candidate = server.all_players[id_2].value
        server.all_players[id_1].candidate_id = server.all_players[id_2].id
        server.all_players[id_2].candidate = server.all_players[id_1].value
        server.all_players[id_2].candidate_id = server.all_players[id_1].id
    for id in server.active_players:
        await server.send_player_update(id)
    await server.broadcast("You got a new candidate")


async def choose_timer(time):
    for i in range(time):
        await asyncio.sleep(1)
        await server.broadcast(f"time remaining : {time-i} seconds")
    server.ev_players_choose_finish.set()


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
            game.after_choose(server)
            await game.tryToMate(server)
            game.end_turn_clean_up(server)
            await server.broadcast(f"end of round {server.round}")
            await asyncio.sleep(3)
            print(f"end of round {server.round}")
        await game.end_game(server, nb_classes)

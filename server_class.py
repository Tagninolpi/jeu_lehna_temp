
from player_class import Player
from game_class import Game
from connections_class import Connections
import asyncio

class Server:
    def __init__(self):
        self.message_queue = asyncio.Queue()
        self.connections = Connections()
        self.admin_id = None
        self.games = {}
        self.lobby_state = "closed"

        self.ev_players_choose_finish = asyncio.Event()
        
        self.timer = 0

    # on client message recieve 
    async def join_lobby(self,client_id):
        if self.lobby_state == "opened":
            self.connections.lobby[0].append(client_id)
            await self.connections.change_page(client_id,"player_lobby")

    async def become_admin(self,client_id,password):
        print(self.admin_id)
        if password == 'password' and self.admin_id == None:
            self.admin_id = client_id
            await self.connections.change_page(client_id,"admin")
            print("is admin")

    async def create_lobby(self,client_id,parameters):
        print(parameters)
        self.lobby_state = "opened"
        self.connections.lobby[0] = []
        await self.connections.change_page(client_id,"admin_lobby")

    # game functions
    async def start_game(self):
        if len(self.connections.lobby[0]) % 2 == 0:
            self.connections.game.game_status = "active"
            self.lobby_state = "closed"
            print("game start")
            await self.connections.change_page_for_all_in(self.connections.lobby[0],"player")
            await asyncio.sleep(2)
            await self.add_players_to_game()
            await self.game_loop()
            await self.reset_all()

    async def add_players_to_game(self):
        for client_id in self.connections.lobby[0]:
            self.connections.game.all_players[client_id] = Player(10,client_id)
            self.connections.game.active_players.append(client_id)
            await self.connections.update_player_info(client_id)
            

    async def game_loop(self):
        while self.connections.game.game_status == "active":
            self.ev_players_choose_finish.clear()
            self.connections.game.changing_players.clear()
            self.connections.game.give_all_new_candidate()
            for id in self.connections.game.active_players:
                await self.connections.update_player_info(id)
            self.timer = asyncio.create_task(self.start_timer(30))
            await self.ev_players_choose_finish.wait()
            self.timer.cancel()
            self.connections.game.after_choose()
            me_id,partner_id = self.connections.game.tryToMate()
            if me_id and partner_id:
                await self.connections.update_player_info(me_id)
                await self.connections.update_player_info(partner_id)
            self.connections.game.end_turn_clean_up()
            if len(self.connections.game.active_players) == 0  or self.connections.game.round == 10:
                self.connections.game.game_status = "Game end"
            else:
                self.connections.game.game_status = "active"

    async def start_timer(self,time):
        for i in range(time):
            await asyncio.sleep(1)
            print(i)
            #await self.connections.broadcast_game_status_update(f"time remaining : {time-i} seconds")
        self.connections.game.game_status = "choose_finish"
        self.ev_players_choose_finish.set()

    async def player_change_partner(self,client_id):
        print(self.connections.game.changing_players)
        if not client_id in self.connections.game.changing_players:
            self.connections.game.changing_players.append(client_id)
            print("change")
            if len(self.connections.game.changing_players) == len(self.connections.game.active_players):
                self.ev_players_choose_finish.set()

    async def download_game_results(self):
        pass

    async def reset_all(self):
        # Cancel the timer if running
        if self.timer and not self.timer.done():
            self.timer.cancel()
            try:
                await self.timer
            except asyncio.CancelledError:
                pass

        # Reset lobby state
        self.lobby_state = "closed"
        self.connections.lobby.clear()

        # Reset admin
        self.admin_id = None

        # Reset all games
        self.connections.game.reset_game_state()
        self.games.clear()

        # Clear event
        self.ev_players_choose_finish.clear()

        # Send everyone to main_menu
        coros = []
        for client_id, ws in self.connections.websockets.items():
            coros.append(self.connections.change_page(client_id, "home"))
        
        if coros:
            await asyncio.gather(*coros)

        print("✅ All games reset. Players sent to main_menu.")
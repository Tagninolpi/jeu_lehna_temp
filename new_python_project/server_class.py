
from player_class import Player
from game_class import Game
from connections_class import Connections
import asyncio

class Server:
    def __init__(self):
        self.message_queue = asyncio.Queue()
        self.connections = Connections()
        self.games = {}
        self.lobby_state = "closed"
        self.lobby = {}

    def join_lobby(self):
        pass

    def become_admin(self,password):
        pass

    def create_lobby(self):
        pass

    def start_game(self):
        pass

    def player_change_partner(self):
        pass

    def download_game_results(self):
        pass
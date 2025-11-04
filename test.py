import numpy as np
from typing import List, Tuple, Optional

class Player:
    def __init__(self, class_nb: float, ID: str):
        self.id = ID
        self.value = self.set_value(class_nb)
        self.candidate = None #value
        self.candidate_id = None #id
        self.partner = None #value
        self.partner_id = None #id
        self.courtship_timer = -1
        self.mating = "waiting"

    def __repr__(self):
        return f"Joueur({self.id}, affichage={self.display_value:.2f}, classe={self.value_class})"

    def build_class_thresholds(self,nb_classes: int) -> List[Tuple[int, float]]:
        if nb_classes < 1:
            raise ValueError("nb_classes doit être >= 1")
        step = 1.0 / nb_classes
        thresholds = [(i + 1, (i + 1) * step) for i in range(nb_classes)]
        #print(thresholds[-1])
        #thresholds[-1] = (thresholds[-1][0], 1.0)  ligne qui sert à rien
        return thresholds

    def value_to_class(self,v: float, thresholds: List[Tuple[int, float]]) -> int:
        if not (0.0 <= v <= 1.0):
            raise ValueError("v doit être dans [0,1]")
        for cls, sup in thresholds:
            if v <= sup:
                return cls
        return 1
    
    def set_value(self,nb_class):
        beta_value = np.random.beta(3,3)
        #print(beta_value)
        thresholds = self.build_class_thresholds(nb_class)
        #print(thresholds)
        class_value = self.value_to_class(beta_value,thresholds)
        #print(class_value)
        return class_value
    
    def reset_player(self,class_nb):
        self.value = self.set_value(class_nb)
        self.candidate = None #value
        self.candidate_id = None #id
        self.partner = None #value
        self.partner_id = None #id
        self.courtship_timer = -1
        self.mating = "waiting"
    
    @staticmethod
    def encounter(ids: List[str], seed: Optional[int] = None, avoid: Optional[set[tuple[str, str]]] = None):
        rng = np.random.default_rng(seed)

        def pair_from_ids(lst: List[str]):
            return [(lst[i], lst[i+1]) for i in range(0, len(lst) - len(lst) % 2, 2)]

        if not avoid:
            rng.shuffle(ids)
            return pair_from_ids(ids)

        avoid_norm = {tuple(sorted(x)) for x in avoid}
        for _ in range(20): 
            rng.shuffle(ids)
            pairs = pair_from_ids(ids)
            if all(tuple(sorted(p)) not in avoid_norm for p in pairs):
                return pairs
        return pair_from_ids(ids)
    




'''
1groupe = 2pairs

for every player if i yes and candidate yes => yes no change
if i yes and candidate no => no 
if i yes partner = candidate
if partner yes =celib 



'''




# def distribution(nb_players: int, alpha: float = 3.0, beta: float = 3.0, seed: Optional[int] = None):
#     rng = np.random.default_rng(seed)
#     return rng.beta(alpha, beta, nb_players).tolist()


# def population(nb_players: int, nb_classes: int, seed: Optional[int] = None):
#     thresholds = build_class_thresholds(nb_classes)
#     values = distribution(nb_players, seed=seed)
#     population = []
#     for i, v in enumerate(values, start=1):
#         cls = value_to_class(v, thresholds)
#         p = Player(value=v, ID=f"local{i:03d}")
#         p.value_class = cls
#         population.append(p)
#     return population, thresholds




# def assigner_classes(population: List[Player], nb_classes: int):
#     thresholds = build_class_thresholds(nb_classes)
#     for joueur in population:
#         joueur.value_class = value_to_class(joueur.value, thresholds)
#     return population

#test encounter
'''
def create_players(classe,nb_p):
    players = []
    for i in range(nb_p):
        players.append(Player(classe,i))
    return players

    return encounter(players,avoid=previous_list)

def test_2(pl,cls=10):
    players = create_players(cls,pl)
    previous_pairs = encounter(players,[])
    print(previous_pairs)
    for i in range(10):
        next_pairs = encounter(players,avoid=previous_pairs)
        print(next_pairs)
        previous_pairs = next_pairs

#test_2(4)

'''

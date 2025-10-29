import numpy as np
from typing import List, Tuple, Optional

class Player:
    def __init__(self, value: float, ID: str):
        self.id = ID
        self.value = value
        self.display_value = value * 10
        self.value_class: Optional[int] = None
        self.candidate = None
        self.partner = None
        self.step = None

    def __repr__(self):
        return f"Joueur({self.id}, affichage={self.display_value:.2f}, classe={self.value_class})"


def build_class_thresholds(nb_classes: int) -> List[Tuple[int, float]]:
    if nb_classes < 1:
        raise ValueError("nb_classes doit être >= 1")
    step = 1.0 / nb_classes
    thresholds = [(i + 1, (i + 1) * step) for i in range(nb_classes)]
    thresholds[-1] = (thresholds[-1][0], 1.0)
    return thresholds


def value_to_class(v: float, thresholds: List[Tuple[int, float]]) -> int:
    if not (0.0 <= v <= 1.0):
        raise ValueError("v doit être dans [0,1]")
    for cls, sup in thresholds:
        if v <= sup:
            return cls
    return thresholds[-1][0]


def distribution(nb_players: int, alpha: float = 3.0, beta: float = 3.0, seed: Optional[int] = None):
    rng = np.random.default_rng(seed)
    return rng.beta(alpha, beta, nb_players).tolist()


def population(nb_players: int, nb_classes: int, seed: Optional[int] = None):
    thresholds = build_class_thresholds(nb_classes)
    values = distribution(nb_players, seed=seed)
    population = []
    for i, v in enumerate(values, start=1):
        cls = value_to_class(v, thresholds)
        p = Player(value=v, ID=f"local{i:03d}")
        p.value_class = cls
        population.append(p)
    return population, thresholds


def encounter(population: List[Player], seed: Optional[int] = None, avoid: Optional[set[tuple[str, str]]] = None):
    ids = [p.id for p in population]
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


def assigner_classes(population: List[Player], nb_classes: int):
    thresholds = build_class_thresholds(nb_classes)
    for joueur in population:
        joueur.value_class = value_to_class(joueur.value, thresholds)
    return population


if __name__ == "__main__":
    pop, thresholds = population(nb_players=20, nb_classes=12, seed=123)
    print("Seuils:", thresholds)
    for j in pop:
        print(j)
    pairs = encounter(pop, seed=42)
    print("Paires:", pairs)

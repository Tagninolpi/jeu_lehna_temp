import numpy as np
import uuid

def distribution(nb_players, alpha=3, beta=3):
    values = np.random.beta(alpha, beta, nb_players)
    values2= np.round(values*10)
    return values2.tolist()

class Player:
    def __init__(self, value):
        self.id = str(uuid.uuid4())[:8]
        self.value = value
        self.candidate = None
        self.partner = None
        self.step = None

    def __repr__(self):
        return f"Joueur({self.id}, valeur={self.value:.2f}, état={self.candidate})"


def creer_population(nb_players):
    values = distribution(nb_players)
    population = [Player(v) for v in values]
    return population

def encounter(population, seed=None):
    rng = np.random.default_rng(seed)
    shuffled = population[:]         
    rng.shuffle(shuffled)            
    return [(shuffled[i].id, shuffled[i+1].id) for i in range(0, len(shuffled), 2)]

if __name__ == "__main__":
    pop = creer_population(20)       
    for j in pop:
        print(j)
    pairs = encounter(pop, seed=123) 
    print("Paires:", pairs)

def assigner_classes(population, nb_classes=18):
    bornes = np.linspace(0, 10, nb_classes + 1)
    for joueur in population:
        for i in range(nb_classes):
            if bornes[i] <= joueur.value < bornes[i + 1]:
                joueur.value_class = i
                break
        else:
            joueur.value_class = nb_classes - 1
    return population

pop = assigner_classes(pop, nb_classes=18)

print("\n--- Population avec classes ---")
for j in pop:
    print(f"{j.id} → valeur: {j.value}, classe: {j.value_class}")
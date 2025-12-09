import numpy as np
class Player:
    def __init__(self, class_nb: float, ID: str):
        self.id = ID
        self.value = self.set_value(class_nb)
        self.candidate = None #value
        self.candidate_id = None #id
        self.partner = None #value
        self.partner_id = None #id
        self.courtship_timer = 0
        self.mating = "waiting"
        self.accept_candidate = False

    def __repr__(self):
        return f"Joueur({self.id}, affichage={self.display_value:.2f}, classe={self.value_class})"

    def player_info(self):
        player_info = {
                "type": "player_update",
                "payload": {
                    "id": self.id,
                    "value": self.value,
                    "candidate": self.candidate,
                    "candidate_id": self.candidate_id,
                    "partner": self.partner,
                    "partner_id": self.partner_id,
                    "courtship_timer": self.courtship_timer,
                    "mating": self.mating
                }
                }
        return player_info

    def build_class_thresholds(self,nb_classes: int) -> list[tuple[int, float]]:
        if nb_classes < 1:
            raise ValueError("nb_classes doit être >= 1")
        step = 1.0 / nb_classes
        thresholds = [(i + 1, (i + 1) * step) for i in range(nb_classes)]
        #print(thresholds[-1])
        #thresholds[-1] = (thresholds[-1][0], 1.0)  ligne qui sert à rien
        return thresholds

    def value_to_class(self,v: float, thresholds: list[tuple[int, float]]) -> int:
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
        self.courtship_timer = 0
        self.mating = "waiting"
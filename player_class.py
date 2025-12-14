import numpy as np
class Player:
    def __init__(self, class_nb: float, ID: str):
        self.id = ID
        self.value = self.set_value(class_nb) #value
        self.candidate = 0 #value
        self.candidate_id = "0" #id
        self.partner = 0 #value
        self.partner_id = "0" #id
        self.courtship_timer = 0
        self.mating = "waiting"
        self.accept_candidate = True #contain the choice of the player of accept a candidate partner or not

    def __repr__(self):
        return f"Joueur({self.id}, affichage={self.display_value:.2f}, classe={self.value_class})"

    def player_info(self,visibility_dict): #give the player information in the form of a dictionnary
        change = self.accept_candidate
        if self.candidate_id == self.partner_id:
            change = False
        player_info = {
                    "id": (self.id,visibility_dict["id"][1]),
                    "value": (self.value,visibility_dict["value"][1]),
                    "candidate": (self.candidate,visibility_dict["candidate"][1]),
                    "candidate_id": (self.candidate_id,visibility_dict["candidate_id"][1]),
                    "partner": (self.partner,visibility_dict["partner"][1]),
                    "partner_id": (self.partner_id,visibility_dict["partner_id"][1]),
                    "courtship_timer": (self.courtship_timer,visibility_dict["courtship_timer"][1]),
                    "mating": (self.mating,visibility_dict["mating"][1]),
                    "change":(None,change)
                }

        return player_info

    def build_class_thresholds(self,nb_classes: int) -> list[tuple[int, float]]:
        #define N classes with (1 class by tuple) of reproductive values
        #each tuple contain :
        #a reproductive value for individuals (between 1 and N)
        #the upper limit for a random number to correspond with this class (the lower limit is the upper limit of the preceding class)
        if nb_classes < 1:
            raise ValueError("nb_classes doit être >= 1")
        step = 1.0 / nb_classes
        thresholds = [(i + 1, (i + 1) * step) for i in range(nb_classes)]
        #print(thresholds[-1])
        #thresholds[-1] = (thresholds[-1][0], 1.0)  ligne qui sert à rien
        return thresholds

    def value_to_class(self,v: float, thresholds: list[tuple[int, float]]) -> int:
        #receive a random number and return the value of the corresponding classe of values
        if not (0.0 <= v <= 1.0):
            raise ValueError("v doit être dans [0,1]")
        for cls, sup in thresholds:
            #search the class corresponding to the random value and return the corresponding value
            #return 1 if no corresponding class is found
            if v <= sup:
                return cls
        return 1
    
    def set_value(self,nb_class): #set a value to a player
        beta_value = np.random.beta(3,3) #randow draw with a beta distribution close to a normal distribution
        #print(beta_value)
        thresholds = self.build_class_thresholds(nb_class) #define the classes (value and thresold of each class)
        #print(thresholds)
        class_value = self.value_to_class(beta_value,thresholds) #give the reproductive value of the corresponding class
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

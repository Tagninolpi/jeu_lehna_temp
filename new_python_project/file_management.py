from player_class import Player
"""
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
"""

def InitFile(linkFile :str):
    with open(linkFile, "w", encoding="utf-8", sep='\t', endline='\n') as f: #crée ou écrase le fichier de lien linkFile avec l'en-tête
        f.write("id"+sep+"value"+sep+"candidate value"+"candidate id"+sep+"partner value"+sep+"partner id"+sep+"timer"+sep+"mating"+sep+"number of time intervals"+endline)

def writeData(linkFile :str,P :Player, t: int, sep='/t' :str, endLine='\n', encoding="utf-8"):
    #la fonction ouvre le fichier de chemin linkFile en mode "append" : le fichier doit donc être vide avant : rajoute du texte à partir de la fin !
    #La fonction écrit dans le fichier sur une ligne les informations contenues dans P (classe Player) et t (le nombre de pas de temps) le tout séparé par le séparateur sep (tabulation '\t' par défaut) et ferme la ligne avec endline (saut de ligne '\n' par défaut)
    with open(linkFile, 'a') as f:
        f.write(str(P.id)+sep+str(P.value)+sep+str(P.candidate)+sep+str(P.candidate_id)+sep+str(P.partner)+sep+str(P.partner_id)+sep+str(P.courtship_timer)+sep+P.mating+sep+str(t)+endline)
        
        

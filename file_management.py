from player_class import Player

def InitFile(linkFile :str, sep='\t', endline='\n'):
    with open(linkFile, "w", encoding="utf-8") as f: #crée ou écrase le fichier de lien linkFile avec l'en-tête
        f.write("id"+sep+"value"+sep+"candidate value"+sep+"candidate id"+sep+"partner value"+sep+"partner id"+sep+"timer"+sep+"mating"+sep+"number of time intervals"+endline)

def writeData(linkFile :str, P :Player, t :int, sep='\t', endline='\n'):
    #la fonction ouvre le fichier de chemin linkFile en mode "append" : le fichier doit donc être vide avant : rajoute du texte à partir de la fin !
    #La fonction écrit dans le fichier sur une ligne les informations contenues dans P (classe Player) et t (le nombre de pas de temps) le tout séparé par le séparateur sep (tabulation '\t' par défaut) et ferme la ligne avec endline (saut de ligne '\n' par défaut)
    with open(linkFile, 'a', encoding="utf-8") as f:
        f.write(str(P.id)+sep+str(P.value)+sep+str(P.candidate)+sep+str(P.candidate_id)+sep+str(P.partner)+sep+str(P.partner_id)+sep+str(P.courtship_timer)+sep+P.mating+sep+str(t)+endline)
        
        

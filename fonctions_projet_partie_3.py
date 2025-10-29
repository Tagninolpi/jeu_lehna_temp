import math

def SigmoidProba(sigma :int, T :int, round_to=3)->tuple:
	##retourne tuples des valeurs d'1 sigmoide avc 1 pas de tps de 1
	#T : absisse du pt d'inflexion
	#sigma : pente du pt d'inflexion
	#round_to : nb de decimales à qui l'on arrondit
	t=0
	L=[round(1/(1+math.exp(T*sigma)), round_to)]
	while L[t]<1:
		t+=1
		L.append(round(1/(1+math.exp(-1*sigma*(t-T))), round_to))
	return tuple(L)
#test fonction
#print(SigmoidProba(1, 5))

import random

def tryToMating(id_individu, D, Tproba)->bool:
    #id_individu: id de l'individu ds D
    #D:dict contenant individus
    #Tproba:tuple des proba de passer en mate
    print(Tproba)
    if random.random() < Tproba[D[id_individu]['durée']]:
        res=True
    else:
        res=False
    return res


   



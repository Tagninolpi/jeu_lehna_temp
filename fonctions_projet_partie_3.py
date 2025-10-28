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

print(SigmoidProba(1, 5))

import random

def tryToMating(individu, D, Dmate, Tproba):
    if random.random() < Tproba[individu['durée']]:
        keys=[k for k, v in D.items() if D[k]==individu or k==individu['partenaire']]
        print(keys)
        Dmate[keys[0]]=D.pop(keys[0])
        Dmate[keys[1]]=D.pop(keys[1])
    else:
        individu['durée']+=1
    return None

#test fonction
"""
D={0:{'durée':0, 'candidat':3, 'partenaire':1}, 1:{'durée':0, 'candidat':4, 'partenaire':0}, 5:{'durée':0, 'candidat':-1, 'partenaire':-1}}
Dmate={8:{'durée':0, 'candidat':-1, 'partenaire':-1}}
Tproba=SigmoidProba(1, 5)

for i in Tproba:
    try:
        tryToMating(D[0], D, Dmate, Tproba)
        print(Dmate)
    except KeyError:
        break
"""

   



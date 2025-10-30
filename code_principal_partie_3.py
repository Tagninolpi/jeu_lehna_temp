"""
Stockage suggéré :

-	D : dictionnaire stocke avc un jeu de clé d'id uniques les différents individus en courtship ou celib avc diff infos
	→ changer ? : choix du dernier tour
	→ partenaire : partenaire actuel -1 si celib
	→ candidat : celui à qui on a possibilité de s'associer (-1 si aucun candidat)
	→ durée : durée du courtship
-	Dmate : stocke couple en mate

Dans le code suivant :
D[D[i]['partenaire']] : le partenaire de l'individu i
D[D[D[i]['partenaire']]['candidat']] : le candidat partenaire du partenaire de l'individu i

tryToMating(i, D, T)->bool:
#i : id de l'individu
#D : dict contenant l'individu
#T : tuples de probabilités de passer en mate
tente de passer en mating
appelle fonction SigmoidProba(D[i]‘durée_courtship’]) pr tenter de passer en mating
si réussite alors renvoie True et il faut mettre les 2 individus en état « mating » et les transferer de Di à Dmate
sinon (échec) renvoie False
"""
import 	fonctions_projet_partie_3 as FlogACh #Fonctions for LOGic After CHoice

T=FlogACh.SigmoidProba(1, 5)#tuples des proba de mating

#test code
D={1:{'changer ?':False, 'partenaire':2, 'candidat':5, 'durée':7}, 2:{'changer ?':True, 'partenaire':1, 'candidat':-1, 'durée':7}, 3:{'changer ?':False, 'partenaire':4, 'candidat':7, 'durée':0}, 4:{'changer ?':True, 'partenaire':3, 'candidat':6, 'durée':0}, 5:{'changer ?':False, 'partenaire':-1, 'candidat':1, 'durée':0}, 6:{'changer ?':True, 'partenaire':-1, 'candidat':4, 'durée':0}, 7:{'changer ?':False, 'partenaire':-1, 'candidat':3, 'durée':0}}



Dmate={}


for i in D:
    if D[i]['candidat']==-1: #pas de candidat-->on passe au suivant
        continue
    if D[i]['changer ?']==True:
        if D[D[i]['candidat']]['changer ?']==True:
            D[i]['partenaire']=D[i]['candidat']
            D[i]['durée']=0
        elif D[D[i]['candidat']]['changer ?']==False:
            if D[i]['partenaire']==-1:
                D[i]['durée']+=-1
            elif D[D[i]['partenaire']]['changer ?']==False:
                if i in Dmate:
                    continue
                elif FlogACh.tryToMating(i, D, T):
                    keys=[k for k, v in D.items() if D[k]==D[i] or k==D[i]['partenaire']]
                    Dmate[keys[0]]=[keys[0]]
                    Dmate[keys[1]]=D[keys[1]]
                else:
                    D[i]['durée']+=1
            elif D[D[i]['partenaire']]['changer ?']==True:
                if D[D[D[i]['partenaire']]['candidat']]['changer ?']==True:
                    D[i]['partenaire']=-1
                    D[i]['durée']=0
                elif D[D[i]['partenaire']['candidat']]['changer ?']==False:
                    if i in Dmate:
                        continue
                    elif FlogACh.tryToMating(i, D, T):
                        keys=[k for k, v in D.items() if D[k]==D[i] or k==D[i]['partenaire']]
                        Dmate[keys[0]]=D[keys[0]]
                        Dmate[keys[1]]=D[keys[1]]
                    else:
                        D[i]['durée']+=1
    elif D[i]['changer ?']==False:
        if D[i]['partenaire']==-1:
            D[i]['durée']+=-1
        elif D[D[i]['partenaire']]['changer ?']==False:
            if i in Dmate:
                continue
            elif FlogACh.tryToMating(i, D, T):
                keys=[k for k, v in D.items() if D[k]==D[i] or k==D[i]['partenaire']]
                Dmate[keys[0]]=D[keys[0]]
                Dmate[keys[1]]=D[keys[1]]
            else:
                D[i]['durée']+=1
        
        elif D[D[i]['partenaire']]['changer ?']==True:
            if D[D[D[i]['partenaire']]['partenaire']]['changer ?']==False:
                if i in Dmate:
                    continue
                elif FlogACh.tryToMating(i, D, T):
                    keys=[k for k, v in D.items() if D[k]==D[i] or k==D[i]['partenaire']]
                    Dmate[keys[0]]=D[keys[0]]
                    Dmate[keys[1]]=D[keys[1]]
                else:
                    D[i]['durée']+=1
            elif D[D['partenaire']['candidat']]['changer ?']==True:
                D[i]['partenaire']=-1
                D[i]['durée']=0

for i in Dmate:
    del D[i]

print(f"D:{D}")
print(f"Dmate:{Dmate}")

"""
à améliorer :
    -   faire les tâches en pl boucles
    -   commenter plus le code
    -   prsuivre les tests
    (-   commencer à imprimer res ds un fichier)
"""

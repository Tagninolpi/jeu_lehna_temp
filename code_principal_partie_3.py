"""
Stockage suggéré : 

 

-	D : dictionnaire stocke avc un jeu de clé d’id uniques les différents individus en courtship ou celib avc diff infos 

→ changer ? : choix du dernier tour 

→ partenaire : partenaire actuel -1 si celib 

→ candidat : celui à qui on a possibilité de s’associer 

→ durée_courtship : durée du courtship 

-	Dmate : stocke couple en mate 

 """

For i in D : 

if i[‘changer ?’]==True : 

if D[‘i[‘candidat’]’][‘changer ?’]==True: 

i[‘partenaire’]=i[‘partenaire_candidat’] 

i[‘durée_courtship’]=0 

elif D[‘i[‘candidat’]’][‘changer ?’]==False: 

if i[‘partenaire’]==-1 : 

i[‘courtship’]+=-1 

elif D[i[‘partenaire’]][‘changer’]==False : 

if not tryToMating(i, Dmate): 

#tente de passer en mating 

#appelle fonction SigmoidProba(i[‘durée_courtship’]) pr tenter de passer en mating 

#si réussite met les 2 individus en état « mating » et les transfere de Di à Dmate et renvoie True 

#sinon (échec) renvoie False 

else : 

i[‘courtship’]+=1 

elif D[i[‘partenaire’]][‘changer ?’]==True: 

if D[D[i[‘partenaire’]][‘candidat’]][‘changer ?’]==True: 

i[‘partenaire’]=-1 

i[‘durée’]==0 

if D[D[i[‘partenaire’]][‘candidat’]][‘changer ?’]==False: 

if not tryToMating(i, Dmate): 

else : 

i[‘courtship’]+=1 

elif i[‘changer ?’]==False: 

if i[‘partenaire’]==-1 : 

i[‘durée_courtship’]+=-1 

elif D[i[‘partenaire’]][‘changer ?’]==False: 

if not tryToMating(i, Dmate): 

else : 

i[‘courtship’]+=1 

elif D[i[‘partenaire’]][‘changer ?’]==True: 

if D[D[i[‘partenaire’]][‘candidat’]][‘changer ?’]==False: 

if not tryToMating(i, Dmate): 

else : 

i[‘courtship’]+=1 

elif D[D[i[‘partenaire’]][‘candidat’]][‘changer ?’]==True: 

i[‘partenaire’]=-1 

i[‘durée_courtship’]=0 

 

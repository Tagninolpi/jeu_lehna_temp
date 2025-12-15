# Mating Game - LEHNA

## Contexte

Selon la théorie de l’évolution, les individus cherchent à se reproduire avec des partenaires de haute qualité, afin d’augmenter les chances de survie et de reproduction de leur descendance. On sait aujourd’hui que les animaux sont capables d’évaluer la qualité d’un partenaire potentiel et de faire des choix qui maximisent leur succès reproductif.

Cependant, les choix effectués par les individus ne sont pas toujours strictement rationnels. Des études ont montré que, dans certaines situations, un individu peut refuser un partenaire de meilleure qualité que celui avec lequel il est déjà en couple, ou au contraire choisir un nouveau partenaire de qualité inférieure. Ce comportement, en apparence “irrationnel”, constitue en réalité une réponse adaptative : il peut favoriser la stabilité des couples et, sur le long terme, améliorer le succès reproductif. Autrement dit, ce que l’on appelle un biais comportemental n’est pas forcément une erreur de jugement, mais peut être une adaptation évolutive avantageuse, avec un grand impact évolutif.

Les chercheurs du LEHNA ont souhaité créer une situation expérimentale permettant de mettre en évidence ce biais adaptatif, à l'aide d’un jeu interactif reproduisant les mécanismes du modèle, afin d’observer l’existence du biais chez l’humain et d’analyser son comportement au cours de la saison de reproduction simulée.

## Utilité du jeu par rapport au modèle existant

L’objectif de ce projet est de concevoir un jeu interactif simulant une saison de reproduction, dans laquelle chaque joueur doit choisir ses partenaires au fil du temps. Le jeu se base sur un modèle biologique inspiré du travail du LEHNA, dans lequel les individus doivent décider de garder leur partenaire actuel ou de changer pour un nouveau candidat.

Une population composée de plusieurs joueurs interagit pendant la simulation. Les individus sont appariés aléatoirement pour former des couples. À chaque tour, le joueur doit décider s’il souhaite conserver son partenaire actuel ou le changer. En d’autres termes, le joueur doit élaborer une stratégie afin de maximiser la qualité du partenaire avec lequel il se reproduit (mate) avant la fin de la saison.

Ce jeu poursuit deux objectifs principaux :

1. **Un objectif pédagogique et expérimental** : Le jeu doit permettre aux étudiants et aux joueurs de comprendre comment les biais de décision influencent les comportements. Il amène à se questionner sur la manière dont ces biais peuvent être modélisés, et sur le fait qu’un biais optimal n’est pas toujours intuitif. En manipulant les paramètres du jeu (temps restant dans la saison, durée du courtship, etc.), le joueur découvre que la stratégie la plus rationnelle n’est pas toujours la plus efficace à long terme.

2. **Un objectif de médiation scientifique** : Dans un cadre de vulgarisation (forum, exposition ou présentation grand public), le jeu illustre le fait qu’un biais humain, souvent perçu comme irrationnel, peut en réalité avoir une valeur adaptative.

### Description de l'existant

Les chercheurs du LEHNA ont construit un modèle fréquence-dépendant permettant d’estimer les biais émotionnels adaptatifs attendus en fonction de la qualité des individus, du temps restant dans la saison, et du temps déjà passé en courtship.

Dans le modèle, chaque individu peut occuper trois états :
- **Célibataire** : sans partenaire ;
- **Courtship** : en phase d’évaluation du partenaire ;
- **Mate** : partenaire accepté, reproduction réussie.

Ce modèle repose sur une population théorique infinie dont les valeurs de qualité suivent une loi normale tronquée entre 0 et 1, nommée loi beta. Des classes de valeurs ont été définies afin de limiter l’hétérogénéité et de mieux représenter les interactions entre individus de niveaux de qualité similaires.

La probabilité de “mating” (reproduction) entre deux individus en phase de “courtship” (interaction préalable à l’accouplement) est modélisée par une fonction sigmoïde. L’axe des abscisses représente le nombre de pas de temps passés en courtship, et l’axe des ordonnées la probabilité de passage en “mate”. Cette probabilité augmente progressivement avec la durée du courtship, jusqu’à un point d’inflexion au-delà duquel la probabilité de reproduction devient rapidement maximale.

Il faut comprendre que ce biais n’est pas une erreur de jugement, mais une adaptation évolutive. Autrement dit, ce que l’on qualifie de “biais émotionnel” correspond à une stratégie adaptative qui favorise la stabilité des couples et augmente la probabilité de reproduction à long terme. L’émotion, loin d’être une déviation irrationnelle, est donc un mécanisme fonctionnel qui soutient la réussite évolutive des individus.

## Description du jeu

Le jeu interactif simule une saison de reproduction où les joueurs doivent choisir leurs partenaires. Voici les mécanismes principaux :

### Logique de début de jeu
1. **Création du lobby** : L’administrateur crée une partie (le “lobby”) depuis l’interface, en établissant une connexion WebSocket avec le serveur. Grâce à cette connexion, l’admin envoie les paramètres de la partie au serveur. Le serveur crée une instance unique de lobby contenant ces paramètres.
2. **Connexion des joueurs** : En chargeant la page, le joueur fait un GET pour vérifier le statut du lobby. Si un lobby existe, ils peuvent le rejoindre. Le serveur notifie l’admin du nombre de joueurs connectés.
3. **Lancement de la partie** : L’administrateur peut lancer la partie une fois que suffisamment de joueurs sont connectés. Le serveur assigne une valeur à chaque joueur (tirée d’une distribution) et démarre la boucle principale du jeu (tâche asynchrone). L’administrateur accède alors à sa page de visualisation en direct, tandis que les joueurs sont dirigés vers la page de jeu.

### Logique pendant le jeu
Le cœur du jeu se déroule dans une boucle principale côté serveur (asynchrone). Les WebSockets assurent la communication bidirectionnelle en temps réel.

1. **Formation des paires** : Le serveur sélectionne aléatoirement des paires parmi les joueurs actifs (non encore en “mating”). Chaque joueur reçoit via WebSocket la valeur de son partenaire et les informations visibles.
2. **Phase de choix** : Un timer interne démarre (ex. 60 secondes). Chaque joueur peut cliquer sur “accepter”. Le clic envoie un message au serveur via WebSocket.
3. **Fin du timer et évaluation** : À la fin du timer, si les deux joueurs se sont mutuellement acceptés, un courtship est créé. Pour chaque couple en courtship, le serveur calcule une probabilité de passage en mating (fonction sigmoïde). Si atteinte, le couple passe en mating et est retiré du pool actif.

### Fin de la partie
La boucle s’arrête lorsqu’il n’y a plus de joueurs actifs ou à la fin de la saison. Le serveur envoie les résultats finaux via WebSocket. Chaque joueur visualise ses statistiques, l’admin peut télécharger un CSV récapitulatif.

### Paramétrage du jeu
L’administrateur peut configurer :
- Nombre de pas de temps (npt) d’une saison
- Npt de courtship (inflexion de la sigmoïde)
- Temps pour faire son choix
- Autres paramètres par défaut.

Chaque paramètre peut être rendu visible ou non aux joueurs.

## Comment l'utiliser

### Prérequis
- Python 3.8 ou supérieur
- Un navigateur web moderne (Chrome, Firefox, Safari, etc.)
- Connexion Internet pour les WebSockets

### 1) En local avec l'environnement virtuel
1. Clonez ou téléchargez le projet dans un répertoire local.
2. Créez un environnement virtuel :
   ```
   python -m venv venv
   source venv/bin/activate
   ```
3. Installez les dépendances :
   ```
   pip install -r requirements.txt
   ```
4. Lancez le serveur :
   ```
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```
5. Ouvrez votre navigateur et accédez à `http://localhost:8000`.
6. L’administrateur peut ensuite créer un lobby et rejoindre la partie sur d'autres onglets.

### 2) En ligne avec Render
Le projet est configuré pour un déploiement sur Render (voir `render.yaml`).
1. Créez un compte sur Render et liez votre repository GitLab.
2. Déployez l'application en utilisant les paramètres par défaut (port via `$PORT`).
3. Une fois déployé, obtenez l'URL publique (ex. `https://votre-app.onrender.com`).
4. Partagez l'URL : Les utilisateurs accèdent directement via leur navigateur pour jouer.
5. Le serveur reste en ligne en continu (utilisez Uptimerobot pour éviter les interruptions).

## Architecture technique

### Backend (Python/FastAPI)
- **app.py** : Point d’entrée FastAPI, gestion routes et WebSockets.
- **server_class.py** : Logique serveur, gestion messages, lobby, admin.
- **game_class.py** : Cœur du jeu, logique rounds, appariements, probabilités.
- **player_class.py** : Modèle joueurs, calcul valeurs/classes.
- **connections_class.py** : Gestion connexions WebSocket, mises à jour UI.
- **observer_class.py** : Listener asynchrone pour messages en file d’attente.
- **file_management.py** : Gestion fichiers (CSV).

### Frontend (HTML/JS/CSS)
- **index.html** : Conteneur principal, charge styles et scripts.
- **main.js** : Logique JavaScript pour WebSockets, chargement dynamique fragments HTML.
- **Fragments HTML** (dans `static/fragments/`) : Pages pour menu, lobby, résultats.
- **Styles** : `tokens.css` (variables), `components.css` (UI), `hidden.css` (utilitaires).
- **Sons** : Effets audio dans `static/sounds/`.

### Technologies
- **FastAPI** : Framework web asynchrone pour API et WebSockets.
- **Uvicorn** : Serveur ASGI.
- **NumPy** : Calculs mathématiques.
- **WebSockets** : Communication temps réel.
- **JavaScript vanilla** : Gestion front-end.

### Sécurité
- Validation messages WebSocket.
- Anonymisation des données (pas de RGPD applicable).

## Développement et contribution

### Structure du projet
```
/
├── app.py                 # Serveur principal
├── game_class.py          # Logique du jeu
├── player_class.py        # Modèle joueur
├── server_class.py        # Gestion serveur
├── connections_class.py   # Connexions WebSocket
├── observer_class.py      # Traitement messages
├── file_management.py     # Gestion fichiers
├── requirements.txt       # Dépendances
├── render.yaml            # Déploiement
└── static/
    ├── index.html
    ├── main.js
    ├── fragments/         # Pages HTML
    ├── styles/            # CSS
    └── sounds/            # Audio
```

### Tests et débogage
- Lancez en mode `--reload` pour développements.
- Utilisez outils débogage navigateur pour WebSockets.
- Tests manuels à chaque fonctionnalité.

### Contribution
- Forkez le repo GitLab, créez branche pour modifications.
- Respectez style code (PEP 8 Python, conventions JS).
- Testez localement avant PR.

### FAQ
- **Le jeu ne se lance pas ?** Vérifiez port 8000 libre, dépendances installées.
- **Problèmes WebSocket ?** Support navigateur, pas de firewall.
- **Comment ajouter sons ?** Placez dans `static/sounds/`, référencez en JS.
- **Données CSV vides ?** Assurez partie jouée, admin télécharge après fin.

Pour détails techniques, consultez commentaires code source.</content>
<parameter name="filePath">

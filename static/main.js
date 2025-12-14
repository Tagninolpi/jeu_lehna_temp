/*
Rôle :
Fichier central côté client du jeu.

Il gère :
- la communication temps réel avec le backend via WebSocket
- le chargement dynamique des pages (fragments HTML)
- la mise à jour de l’interface utilisateur (UI) en fonction des messages serveur
- l’envoi des actions utilisateur vers le backend (boutons, formulaires, paramètres)

Données reçues :
- main.js ouvre une connexion WebSocket sur l’endpoint /ws.
- Il reçoit des messages JSON envoyés par le backend Python (scripts serveur).
- Ces messages contiennent :
un type (ex: change_page, ui_update)
un payload associé aux données à afficher ou à l’action à effectuer. 


Traitement :
- Les changements de page sont gérés via le chargement de fragments HTML depuis le dossier /fragments.
- Les données reçues (états du jeu, valeurs joueur, paramètres visibles) sont injectées dynamiquement dans le DOM via la fonction updateUI().
- Certains états déclenchent des effets visuels et sonores (ex: timer critique).

Données envoyées :
- Les actions utilisateur (clics, validation de paramètres, lancement de partie) sont envoyées au backend via WebSocket sous forme de messages JSON.
- Ces messages sont ensuite traités par les scripts Python côté serveur pour piloter la logique du jeu (lobby, matchmaking, tours, résultats).

En résumé :
main.js fait le lien entre l’interface web (HTML/CSS),
les interactions utilisateur,
et la logique métier exécutée côté backend Python.
*/


// Indique dans la console que le fichier main.js a bien été chargé
console.log("✅ main.js chargé");

// Choisit le bon protocole WebSocket selon le type de page (http / https)
const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws"; 
const wsHost = window.location.host; // Récupère l’hôte courant (ex: localhost:8000)
const app = document.getElementById("app"); // Récupère le conteneur principal où seront injectées les pages HTML
let ws = new WebSocket(`${wsProtocol}://${wsHost}/ws`); // Ouvre la connexion WebSocket avec le backend Python

// TIC TAC TIMER
const ticTacSound = new Audio("/static/sounds/tictac.mp3"); // Son utilisé lorsque le temps devient critique
ticTacSound.loop = true;
ticTacSound.volume = 0.5;
let ticTacPlaying = false;
let audioUnlocked = false; // Nécessaire pour éviter les blocages audio par les navigateurs

// Cette fonction est appelée à chaque message reçu du serveur
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  const { type, payload } = msg;

  switch (type) {
    case "change_page": // Le serveur demande de changer de page
      loadFragment(payload); // admin_lobby, admin, main_menu, player_lobby, player,admin_result,admin_download,player_result
      break;
    
    case "ui_update": // Le serveur demande une mise à jour de l’interface
      updateUI(payload);
      break;

    default:
      console.warn("Unknown message type:", type);
  }
};

// Met à jour l’affichage à partir des données envoyées par le serveur
// Fonction centrale d’affichage : TOUT ce que le joueur voit à l’écran passe par ici
function updateUI(dict) {
  for (const [id, [text, visible]] of Object.entries(dict)) { // Parcourt toutes les valeurs reçues

    if (id === "change") {
      const el = document.getElementById(id);
      if (!el) continue;

      if (visible !== undefined) { // Le serveur décide si le bouton est visible
        const row = el.closest('div') || el;
        if (visible) row.classList.remove('hidden');
        else row.classList.add('hidden');
      }
      continue;
    }

    const el = document.getElementById(id); // Recherche de l’élément HTML correspondant à l’id
    if (!el) continue;

    if (id === "status") { // Cas spécial : statut du jeu (timer)
      el.textContent = text;

      const match = text.match(/(\d+)\s*seconds?/);  // Recherche d’un nombre de secondes dans le texte

      if (match) {
        const seconds = parseInt(match[1], 10);

        if (seconds <= 10) {
          el.classList.add("timer-urgent");

          if (audioUnlocked && !ticTacPlaying) { // Lancement du son si autorisé
            ticTacSound.currentTime = 0;
            ticTacSound.play().catch(() => {});
            ticTacPlaying = true;
          }

        } else {
          el.classList.remove("timer-urgent");

          if (ticTacPlaying) {
            ticTacSound.pause();
            ticTacSound.currentTime = 0;
            ticTacPlaying = false;
          }
        }

      } else {
        el.classList.remove("timer-urgent");

        if (ticTacPlaying) {
          ticTacSound.pause();
          ticTacSound.currentTime = 0;
          ticTacPlaying = false;
        }
      }

    } else {
      const safeText = // Cas général : affichage de texte simple
        text === null || text === "null" || text === undefined
          ? ""
          : String(text);

      if (id === "candidate") { // Le candidat est affiché sans animation
        el.textContent = safeText;
      } else {
        if (el.textContent !== safeText && safeText !== "") { // Animation seulement si la valeur change
          scrambleText(el, safeText);
        } else {
          el.textContent = safeText;
        }
      }
    }

    const row = el.closest('div') || el; // Gestion de la visibilité (montrer / cacher)
    if (visible !== undefined) {
      if (visible) row.classList.remove('hidden');
      else row.classList.add('hidden');
    }
  }
}

// Envoie une action (clic bouton) au serveur
function button_click(page, button, payload) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      page: page,
      button: button,
      message: payload
    }));
  } else {
    console.warn("WebSocket non connecté — action ignorée");
  }
}

// Construit les paramètres du lobby à partir du formulaire
function getPayload(form) {
  const payload = {};

  form.querySelectorAll(".param-item").forEach(item => { // Chaque .param-item correspond à un paramètre
    const input = item.querySelector("input");
    const toggle = item.querySelector(".toggle");
    const valueBtn = item.querySelector(".value-toggle");

    if (input) {
      // Paramètre numérique + visibilité
      const key = input.name;
      const value = [ Number(input.value), toggle.dataset.value === "true" ];
      payload[key] = value;
    } else if (valueBtn) {
      // Paramètre booléen (ex: last chance)
      const key = valueBtn.dataset.name;
      const value = valueBtn.dataset.value === "true";

      const visibleBtn = item.querySelector(".toggle"); // visibility button
      const visible = visibleBtn ? visibleBtn.dataset.value === "true" : false;

      payload[key] = [value, visible];
    } else if (toggle) {
      // Paramètre uniquement visible / invisible
      const key = toggle.dataset.name;
      const visible = toggle.dataset.value === "true";
      payload[key] = [0, visible];
    }
  });

  return payload;
}


// Charge un fichier HTML et l’insère dans #app (changement de page)
async function loadFragment(name) {
  try {
    const response = await fetch(`./fragments/${name}.html`);
    if (!response.ok) throw new Error("Fragment introuvable");
    const html = await response.text();
    app.innerHTML = html;
  } catch (err) {
    app.innerHTML = `<p style="color:red;text-align:center;">Erreur de chargement : ${err.message}</p>`;
  }
}

// Téléchargement CSV (admin)
async function downloadCSV() {
    try {
        const response = await fetch("/download_csv");
        if (!response.ok) throw new Error("Erreur téléchargement CSV");

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        // Get filename from Content-Disposition header
        let fileName = "results.csv"; // défaut
        const disposition = response.headers.get("Content-Disposition");
        if (disposition && disposition.includes("filename=")) {
            fileName = disposition.split("filename=")[1].replace(/['"]/g, '');
        }

        const a = document.createElement("a");
        a.href = url;
        a.download = fileName; // Nom du fichier dynamique
        a.click();

        URL.revokeObjectURL(url);

        // Après téléchargement, recharger la page admin pour réinitialiser l’état
        loadFragment("admin");
    } catch (err) {
        console.error("❌ Erreur CSV:", err);
    }
}

// Cette fonction informe le serveur que le jeu peut démarrer
async function start_game() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ "page": "pre_game", "button": "load_page", "message": null })); // Envoie un message au serveur pour charger la page de pré-jeu. Le serveur décidera ensuite quoi afficher (menu, lobby, etc.)
  } else {
    console.warn("WebSocket non connecté — action ignorée");
  }
}

// Écoute tous les clics sur la page
document.addEventListener("click", (e) => {
  const btn = e.target; // Élément cliqué
  if (!btn.classList.contains("toggle") && !btn.classList.contains("value-toggle")) return; // On ne traite que les boutons de type toggle

  let value = btn.dataset.value === "true"; // Lecture de la valeur actuelle (true / false)
  value = !value;
  btn.dataset.value = value;

  if (btn.classList.contains("value-toggle")) { // Mise à jour du texte affiché sur le bouton
    btn.textContent = value ? "Enabled" : "Disabled";
  } else {
    btn.textContent = value ? "Visible" : "Invisible";
  }

  btn.style.background = value ? "white" : "black"; // Mise à jour visuelle du bouton (retour utilisateur)
  btn.style.color = value ? "black" : "white";
});

// Fonction appelée une seule fois au chargement de la page
async function init() {
  await loadFragment("main_menu"); // Charge le menu principal dans la page
  await start_game(); // Informe le serveur que le client est prêt
}

// Effet visuel appliqué lorsqu’une valeur change à l’écran. Purement esthétique (aucun impact sur la logique du jeu).
function scrambleText(el, newText) {
  const chars = "!<>-_\\/[]{}—=+*^?#________"; // Liste de caractères utilisés pour l’animation
  const duration = 600;
  const steps = 20;
  let frame = 0;
  const oldText = el.textContent;

  const interval = setInterval(() => {
    let output = "";
    for (let i = 0; i < newText.length; i++) { // Construction progressive du texte final
      if (i < (frame / steps) * newText.length) {
        output += newText[i];
      } else {
        output += chars[Math.floor(Math.random() * chars.length)];
      }
    }

    el.textContent = output;
    frame++;

    if (frame >= steps) {
      clearInterval(interval);
      el.textContent = newText;
    }
  }, duration / steps);
}

// Déblocage du son (navigateur)
document.addEventListener("click", () => {
  if (!audioUnlocked) {
    ticTacSound.play().then(() => {
      ticTacSound.pause();
      ticTacSound.currentTime = 0;
      audioUnlocked = true;
      console.log("🔊 Audio débloqué");
    }).catch(() => {});
  }
}, { once: true });

init();
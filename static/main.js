console.log("✅ main.js chargé");

const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
const wsHost = window.location.host;
const app = document.getElementById("app");
let ws = new WebSocket(`${wsProtocol}://${wsHost}/ws`);

// ---- Incoming messages ----
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  const { type, payload } = msg;

  switch (type) {
    case "change_page":
      loadFragment(payload);//admin_lobby,admin,main_menu,player_lobby,player
      break;

    case "player_update":
      update_player(payload);
      break;

    case "value_update":
      updatevalue(msg.payload.key, msg.payload.value);
      break;

    default:
      console.warn("Unknown message type:", type);
  }
};

function updatevalue(type, newvalue) {
  const statusEl = document.getElementById(type);
  if (statusEl) {
    statusEl.textContent = `Joueurs connectés : ${newvalue}`;
  } else {
    console.warn(`⚠️ Élément #${type} introuvable dans le DOM`);
  }
}

// update player view
function update_player(p) {
  p.id != null && (document.getElementById("id").textContent = p.id);
  p.value != null && (document.getElementById("value").textContent = p.value);
  p.candidate != null && (document.getElementById("candidate").textContent = p.candidate);
  p.candidate_id != null && (document.getElementById("candidate_id").textContent = p.candidate_id);
  p.partner != null && (document.getElementById("partner").textContent = p.partner);
  p.partner_id != null && (document.getElementById("partner_id").textContent = p.partner_id);
  p.courtship_timer != null && (document.getElementById("courtship_timer").textContent = p.courtship_timer);
  p.mating != null && (document.getElementById("mating").textContent = p.mating);
}

function button_click(page,button,payload) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({"page": page,"button": button,"message": payload}));
  } else {
    console.warn("WebSocket non connecté — action ignorée");
  }
}

// reads all form fields and builds a payload object
function getPayload(form) {
  const payload = {};
  const inputs = form.querySelectorAll("input");

  inputs.forEach((input) => {
    const key = input.dataset.key || input.name;
    if (!key) return;

    if (input.type === "radio") {
      if (input.checked) payload[key] = input.value;
    } else {
      payload[key] = input.value;
    }
  });

  return payload;
}

//data = dict {"ClassesNB":valeur, ...}
function display(data){
    const lobbyParameter=["ClassesNb", "duration", "SeasonNb", "MaxTime", "SigmoidProba", "LastOption"]; //doit contenir toutes les id d'infos possible sinon bug !
    lobbyParameter.forEach(id => {
        const prm=document.getElementById(id)
        if (!prm) { //permet d'avertir le developpeur qu'1 des id d'information possible dans lobbyParameter ne correspond à aucune balise (masquée ou non) dans l'HTML, et le script continue quand même
            console.error(`Paramètre #${id} manquant dans le DOM !`);
            return;
        }
        if (id in data) {
            //prm.classList.remove("hidden") //utile seulement si la décision de masquer ou non un élement peut changer en cours de partie
            const span = prm.querySelector("span");
            if (!span) { //si on a pas trouvé de span pour y afficher l'information
                console.error(`Élément #${id} ne contient pas de <span>.`);
                return;
            }
            span.textContent = data[id];
        } else {
            prm.classList.add("hidden")
        }
    });
}

// change de page
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

loadFragment("main_menu");

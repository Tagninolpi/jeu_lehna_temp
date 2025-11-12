//webSocket connection to server
console.log("✅ script.js loaded!");

const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
const wsHost = window.location.host;
let ws = new WebSocket(`${wsProtocol}://${wsHost}/ws`);

ws.addEventListener("error", () => {
  try {
    if (ws && ws.readyState !== WebSocket.OPEN) {
      ws.close();
    }
  } catch (_) {}
  ws = new WebSocket("ws://127.0.0.1:8000/ws");
});

// ---- Incoming messages ----
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  const { type, payload } = msg;
  
  const DisplayData=JSON.parse(event.data)
  
  display(DisplayData)
  
  switch (type) {
    case "status_update":
      update_status(payload);
      break;

    case "player_update":
      update_player(payload);
      break;

    default:
      console.warn("Unknown message type:", type);
  }
};

// ---- Function to update partner and candidate ----
function update_status(message) {
  if (message != null)
    document.getElementById("status").textContent = message;
}

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

// ---- Sending actions ----
function changePartner() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "change_partner" }));
  } else {
    console.warn("WebSocket non connecté — action ignorée");
  }
}

//display parameters

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

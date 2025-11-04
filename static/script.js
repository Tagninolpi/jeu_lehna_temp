//webSocket connection to server
const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
const wsHost = window.location.host; // e.g., "127.0.0.1:8000" or "jeu-lehna-temp.onrender.com"
const ws = new WebSocket(`${wsProtocol}://${wsHost}/ws`);



// ---- Incoming messages ----
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  const { type, payload } = msg;

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
    ws.send(JSON.stringify({ type: "change_partner" }));
}

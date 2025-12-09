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
      loadFragment(payload); // admin_lobby, admin, main_menu, player_lobby, player,admin_result
      break;

    case "player_update":
      update_player(payload);
      break;

    case "value_update":
      updatevalue(msg.payload.key, msg.payload.value);
      break;

    case "player_parameters":
      display(payload);
      break;
    
    case "game_end":
      showCSVButton();
      break;

    default:
      console.warn("Unknown message type:", type);
  }
};

function updatevalue(type, newvalue) {
  const statusEl = document.getElementById(type);
  if (statusEl) {
    statusEl.textContent = newvalue;
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

  if (p.button) {
    document.getElementById("change").style.display = "none";
  } else {
    document.getElementById("change").style.display = "inline-block";
  }
}

function button_click(page, button, payload) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ "page": page, "button": button, "message": payload }));
  } else {
    console.warn("WebSocket non connecté — action ignorée");
  }
}

// reads all form fields and builds a payload object
function getPayload(form) {
  const payload = {};

  form.querySelectorAll(".param-item").forEach(item => {
    const input = item.querySelector("input");
    const toggle = item.querySelector(".toggle");

    const key = input.name;

    payload[key] = {
      value: input.value,
      visible: toggle.dataset.value === "true"
    };
  });

  return payload;
}

// data = { "NbClass": { value: 10, visible: true }, ... }
function display(data) {
  const lobbyParameter = ["NbClass", "nb_tours_saison", "TmaxTour", "sigma", "npt_moy_before_mating"]; // must match admin parameter names

  lobbyParameter.forEach(id => {
    const prm = document.getElementById(id);
    if (!prm) {
      console.error(`Paramètre #${id} introuvable dans le DOM !`);
      return;
    }

    const span = prm.querySelector("span");
    if (!span) {
      console.error(`Élément #${id} ne contient pas de <span>.`);
      return;
    }

    if (id in data) {
      span.textContent = data[id].value;

      // toggle hidden class based on visibility
      if (data[id].visible) {
        prm.classList.remove("hidden"); // show
      } else {
        prm.classList.add("hidden");    // hide
      }
    } else {
      prm.classList.add("hidden"); // hide if missing
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
    if (name =="player"){
      document.getElementById("change").style.display = "none"
    }
  } catch (err) {
    app.innerHTML = `<p style="color:red;text-align:center;">Erreur de chargement : ${err.message}</p>`;
  }
}

loadFragment("main_menu");

// ---- Toggle TRUE/FALSE buttons ----
document.addEventListener("click", (e) => {
  if (!e.target.classList.contains("toggle")) return;

  const btn = e.target;

  // read current state
  let value = btn.dataset.value === "true";

  // toggle it
  value = !value;

  // save it
  btn.dataset.value = value;

  // update text
  btn.textContent = value ? "Visible" : "Invisible";

  // update visual color
  if (value) {
    btn.style.background = "white";
    btn.style.color = "black";
  } else {
    btn.style.background = "black";
    btn.style.color = "white";
  }
});

async function downloadCSV() {
    try {
        const response = await fetch("/download_csv");
        if (!response.ok) throw new Error("Erreur téléchargement CSV");

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = "results.csv";
        a.click();

        URL.revokeObjectURL(url);

        // Switch page AFTER download
        loadFragment("admin");
    } catch (err) {
        console.error("❌ Erreur CSV:", err);
    }
}


function showCSVButton() {
    const btn = document.getElementById("download_csv_btn");
    if (btn) {
        btn.style.display = "inline-block"; // or "block"
    }
}

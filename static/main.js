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
      loadFragment(payload); // admin_lobby, admin, main_menu, player_lobby, player,admin_result,admin_download
      break;
    
    case "ui_update":
      updateUI(payload);
      break;

    default:
      console.warn("Unknown message type:", type);
  }
};

function updateUI(dict) {
  for (const [id, [text, visible]] of Object.entries(dict)) {
    const el = document.getElementById(id);

    if (!el) {
      console.warn(`⚠️ Element #${id} not found`);
      continue;
    }

    // Update the text of the element
    if (text !== null && text !== undefined) {
      el.textContent = text;
    }

    // Update visibility using the .hidden class
    const row = el.closest('div') || el;  // nearest parent div
    if (visible !== undefined) {
      if (visible) row.classList.remove('hidden');
      else row.classList.add('hidden');
  }
}}

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

    // KEY = input.name (always present in your HTML)
    const key = input.name;

    payload[key] = [
      Number(input.value),             // send numeric value correctly
      toggle.dataset.value === "true"  // visibility boolean
    ];
  });

  return payload;
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

async function start_game() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ "page": "pre_game", "button": "load_page", "message": null }));
  } else {
    console.warn("WebSocket non connecté — action ignorée");
  }
}

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

async function init() {
  await loadFragment("main_menu");
  await start_game(); // now sends message after fragment exists
}
init();
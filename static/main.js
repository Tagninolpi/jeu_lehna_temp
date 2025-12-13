console.log("✅ main.js chargé");

const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
const wsHost = window.location.host;
const app = document.getElementById("app");
let ws = new WebSocket(`${wsProtocol}://${wsHost}/ws`);

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  const { type, payload } = msg;

  switch (type) {
    case "change_page":
      loadFragment(payload); // admin_lobby, admin, main_menu, player_lobby, player,admin_result,admin_download,player_result
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

      if (id === "change") {
        const el = document.getElementById(id);
        if (!el) continue;

        if (visible !== undefined) {
          const row = el.closest('div') || el;
          if (visible) row.classList.remove('hidden');
          else row.classList.add('hidden');
        }
        continue;
      }

      const el = document.getElementById(id);
      if (!el) continue;

    // Update the text of the element
    if (id === "status") {
      el.textContent = text;

      // Try to extract remaining seconds
      const match = text.match(/(\d+)\s*seconds?/);

      if (match) {
        const seconds = parseInt(match[1], 10);

        if (seconds <= 10) {
          el.classList.add("timer-urgent");
        } else {
          el.classList.remove("timer-urgent");
        }
      } else {
        // Not a timer anymore (mate / waiting)
        el.classList.remove("timer-urgent");
      }

      } else {
        // Sécurité anti-null / anti-"null"
        const safeText =
          text === null || text === "null" || text === undefined
            ? ""
            : String(text);

        if (el.textContent !== safeText) {
          el.textContent = safeText;

          // Animation UNIQUEMENT si on a du vrai texte
          if (safeText !== "") {
            el.classList.add("pixel-text");
            setTimeout(() => el.classList.remove("pixel-text"), 500);
          }
        }
      }

    const row = el.closest('div') || el;
    if (visible !== undefined) {
      if (visible) row.classList.remove('hidden');
      else row.classList.add('hidden');
  }
}}

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


function getPayload(form) {
  const payload = {};

  form.querySelectorAll(".param-item").forEach(item => {
    const input = item.querySelector("input");
    const toggle = item.querySelector(".toggle");
    const valueBtn = item.querySelector(".value-toggle"); // our new value button

    if (input) {
      // Numeric parameter + visibility
      const key = input.name;
      const value = [ Number(input.value), toggle.dataset.value === "true" ];
      payload[key] = value;
    } else if (valueBtn) {
      // Last Chance (or any value-only button) + associated visibility button
      const key = valueBtn.dataset.name;
      const value = valueBtn.dataset.value === "true";

      const visibleBtn = item.querySelector(".toggle"); // visibility button
      const visible = visibleBtn ? visibleBtn.dataset.value === "true" : false;

      payload[key] = [value, visible];
    } else if (toggle) {
      // Visibility-only parameter
      const key = toggle.dataset.name;
      const visible = toggle.dataset.value === "true";
      payload[key] = [0, visible];
    }
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

        // Get filename from Content-Disposition header
        let fileName = "results.csv"; // default
        const disposition = response.headers.get("Content-Disposition");
        if (disposition && disposition.includes("filename=")) {
            fileName = disposition.split("filename=")[1].replace(/['"]/g, '');
        }

        const a = document.createElement("a");
        a.href = url;
        a.download = fileName; // use dynamic filename
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
  const btn = e.target;
  if (!btn.classList.contains("toggle") && !btn.classList.contains("value-toggle")) return;

  let value = btn.dataset.value === "true";
  value = !value;
  btn.dataset.value = value;

  // Update text based on type
  if (btn.classList.contains("value-toggle")) {
    btn.textContent = value ? "Enabled" : "Disabled";
  } else {
    btn.textContent = value ? "Visible" : "Invisible";
  }

  // Optional styling
  btn.style.background = value ? "white" : "black";
  btn.style.color = value ? "black" : "white";
});


async function init() {
  await loadFragment("main_menu");
  await start_game(); // now sends message after fragment exists
}

function scrambleText(el, newText) {
  const chars = "!<>-_\\/[]{}—=+*^?#________";
  const duration = 600;
  const steps = 20;
  let frame = 0;
  const oldText = el.textContent;

  const interval = setInterval(() => {
    let output = "";
    for (let i = 0; i < newText.length; i++) {
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

init();


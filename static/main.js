/*
Role:
Client-side central file of the game.

It handles:
- real-time communication with the backend through WebSocket
- dynamic loading of pages (HTML fragments)
- updating the user interface (UI) based on server messages
- sending user actions to the backend (buttons, forms, parameters)

Data received:
- main.js opens a WebSocket connection on the /ws endpoint.
- It receives JSON messages sent by the Python backend (server scripts).
- These messages contain:
  a type (e.g., change_page, ui_update)
  a payload associated with the data to display or the action to perform.

Processing:
- Page changes are handled by loading HTML fragments from the /fragments folder.
- Received data (game states, player values, visible parameters) is injected dynamically into the DOM via the updateUI() function.
- Certain states trigger visual and audio effects (e.g., critical timer).

Data sent:
- User actions (clicks, parameter validation, game launch) are sent to the backend via WebSocket as JSON messages.
- These messages are then processed by the Python scripts on the server side to drive the game logic (lobby, matchmaking, turns, results).

In summary:
main.js links the web interface (HTML/CSS),
user interactions,
and the business logic executed on the Python backend.
*/


// Indicates in the console that the main.js file has loaded correctly
console.log("✅ main.js chargé");

// Chooses the correct WebSocket protocol depending on the page type (http / https)
const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws"; 
const wsHost = window.location.host; // Retrieves the current host (e.g., localhost:8000)
const app = document.getElementById("app"); // Retrieves the main container where HTML pages will be injected
let ws = new WebSocket(`${wsProtocol}://${wsHost}/ws`); // Opens the WebSocket connection with the Python backend

// TIC TAC TIMER
const ticTacSound = new Audio("/static/sounds/tictac.mp3"); // Sound used when time becomes critical
ticTacSound.loop = true;
ticTacSound.volume = 0.5;
let ticTacPlaying = false;
let audioUnlocked = false; // Needed to avoid audio blocks by browsers

// This function is called for each message received from the server
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  const { type, payload } = msg;

  switch (type) {
    case "change_page": // The server requests a page change
      loadFragment(payload); // admin_lobby, admin, main_menu, player_lobby, player, admin_result, admin_download, player_result
      break;
    
    case "ui_update": // The server requests a UI update
      updateUI(payload);
      break;

    default:
      console.warn("Unknown message type:", type);
  }
};

// Updates the display based on the data sent by the server
// Core display function: EVERYTHING the player sees on screen goes through here
function updateUI(dict) {
  for (const [id, [text, visible]] of Object.entries(dict)) { // Iterates over all received values

    if (id === "change") {
      const el = document.getElementById(id);
      if (!el) continue;

      if (visible !== undefined) { // The server decides whether the button is visible
        const row = el.closest('div') || el;
        if (visible) row.classList.remove('hidden');
        else row.classList.add('hidden');
      }
      continue;
    }

    const el = document.getElementById(id); // Finds the HTML element corresponding to the id
    if (!el) continue;

    if (id === "status") { // Special case: game status (timer)
      el.textContent = text;

      const match = text.match(/(\d+)\s*seconds?/);  // Looks for a number of seconds in the text

      if (match) {
        const seconds = parseInt(match[1], 10);

        if (seconds <= 10) {
          el.classList.add("timer-urgent");

          if (audioUnlocked && !ticTacPlaying) { // Starts the sound if allowed
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
      const safeText = // General case: simple text display
        text === null || text === "null" || text === undefined
          ? ""
          : String(text);

      if (id === "candidate") { // The candidate is displayed without animation
        el.textContent = safeText;
      } else {
        if (el.textContent !== safeText && safeText !== "") { // Animation only if the value changes
          scrambleText(el, safeText);
        } else {
          el.textContent = safeText;
        }
      }
    }

    const row = el.closest('div') || el; // Manages visibility (show / hide)
    if (visible !== undefined) {
      if (visible) row.classList.remove('hidden');
      else row.classList.add('hidden');
    }
  }
}

// Sends an action (button click) to the server
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

// Builds the lobby parameters from the form
function getPayload(form) {
  const payload = {};

  form.querySelectorAll(".param-item").forEach(item => { // Each .param-item corresponds to a parameter
    const input = item.querySelector("input");
    const toggle = item.querySelector(".toggle");
    const valueBtn = item.querySelector(".value-toggle");

    if (input) {
      // Numeric parameter + visibility
      const key = input.name;
      const value = [ Number(input.value), toggle.dataset.value === "true" ];
      payload[key] = value;
    } else if (valueBtn) {
      // Boolean parameter (e.g., last chance)
      const key = valueBtn.dataset.name;
      const value = valueBtn.dataset.value === "true";

      const visibleBtn = item.querySelector(".toggle"); // visibility button
      const visible = visibleBtn ? visibleBtn.dataset.value === "true" : false;

      payload[key] = [value, visible];
    } else if (toggle) {
      // Parameter that is only visible / invisible
      const key = toggle.dataset.name;
      const visible = toggle.dataset.value === "true";
      payload[key] = [0, visible];
    }
  });

  return payload;
}


// Loads an HTML file and inserts it into #app (page change)
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

// CSV download (admin)
async function downloadCSV() {
    try {
        const response = await fetch("/download_csv");
        if (!response.ok) throw new Error("Erreur téléchargement CSV");

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        // Get filename from Content-Disposition header
        let fileName = "error_empty_results.csv"; // default
        const disposition = response.headers.get("Content-Disposition");
        if (disposition && disposition.includes("filename=")) {
            fileName = disposition.split("filename=")[1].replace(/['"]/g, '');
        }

        const a = document.createElement("a");
        a.href = url;
        a.download = fileName; // Dynamic file name
        a.click();

        URL.revokeObjectURL(url);

        // After downloading, reload the admin page to reset the state
        loadFragment("admin");
    } catch (err) {
        console.error("❌ Erreur CSV:", err);
    }
}

// This function informs the server that the game can start
async function start_game() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ "page": "pre_game", "button": "load_page", "message": null })); // Sends a message to the server to load the pre-game page. The server will then decide what to display (menu, lobby, etc.)
  } else {
    console.warn("WebSocket non connecté — action ignorée");
  }
}

// Listens to every click on the page
document.addEventListener("click", (e) => {
  const btn = e.target; // Clicked element
  if (!btn.classList.contains("toggle") && !btn.classList.contains("value-toggle")) return; // Only handle toggle-type buttons

  let value = btn.dataset.value === "true"; // Read the current value (true / false)
  value = !value;
  btn.dataset.value = value;

  if (btn.classList.contains("value-toggle")) { // Update the text displayed on the button
    btn.textContent = value ? "Enabled" : "Disabled";
  } else {
    btn.textContent = value ? "Visible" : "Invisible";
  }

  btn.style.background = value ? "white" : "black"; // Visual update of the button (user feedback)
  btn.style.color = value ? "black" : "white";
});

// Function called once when the page loads
async function init() {
  await loadFragment("main_menu"); // Loads the main menu into the page
  await start_game(); // Informs the server that the client is ready
}

// Visual effect applied when a value changes on screen. Purely aesthetic (no impact on game logic).
function scrambleText(el, newText) {
  const chars = "!<>-_\\/[]{}—=+*^?#________"; // List of characters used for the animation
  const duration = 600;
  const steps = 20;
  let frame = 0;
  const oldText = el.textContent;

  const interval = setInterval(() => {
    let output = "";
    for (let i = 0; i < newText.length; i++) { // Progressive construction of the final text
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

// Audio unlocking (browser)
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

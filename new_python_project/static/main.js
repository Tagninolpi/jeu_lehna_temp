console.log("✅ main.js chargé");

const app = document.getElementById("app");

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

function setupNavigation() {
  document.body.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-fragment]");
    if (btn) {
      const fragmentName = btn.getAttribute("data-fragment");
      loadFragment(fragmentName);
      e.preventDefault();
    }
  });
}

setupNavigation();

loadFragment("home");

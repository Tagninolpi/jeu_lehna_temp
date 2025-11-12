//webSocket connection to server
const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
const wsHost = window.location.host;
let ws = new WebSocket(`${wsProtocol}://${wsHost}/ws`);


//---- Access to data form ----

const form = document.getElementById('param'); //defini le formulaire d'id=param en JavaScript (déjà pst ds HTML)

form.addEventListener('submit', (event) => { //se declenche si sousmission formulaire
    event.preventDefault(); //prevent usual form of being sent
    
    const formData = new FormData(form);
    //utilise l'objet formData pour récupérer données sous forme de clés-valeurs id-value sauf pour boutons radio ou l'on a : name-value
    
    //conversion en objet :
    
    const data = Object.fromEntries(formData.entries());
    
    SendParamLobby(data)
    
});

//function to sending data
function SendParamLobby(DataParam) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(DataParam));
    } else {
        console.warn("WebSocket non connecté — action ignorée");
        }
}

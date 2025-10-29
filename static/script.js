//webSocket connection to server
const ws = new WebSocket("ws://127.0.0.1:8000/ws");


// ---- Incoming messages ----
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    const type = msg.type;
    const payload = msg.payload;

    switch(type) {
        case "up_val": 
            // Only update fields that exist in payload
            update_values(
                payload.status,       // may be undefined
                payload.my_value,     // may be undefined
                payload.currentPartner, // may be undefined
                payload.candidate     // may be undefined
            );
            break;

        default:
            console.warn("Unknown message type:", type);
    }
};



// ---- Function to update partner and candidate ----
function update_values(status, my_value, currentPartner, candidate) {
    status != null && (document.getElementById("status").textContent = status);
    my_value != null && (document.getElementById("my_value").textContent = my_value);
    currentPartner != null && (document.getElementById("currentPartner").textContent = currentPartner);
    candidate != null && (document.getElementById("candidate").textContent = candidate);
}

// ---- Sending actions ----
function ChangePartner() {
    ws.send(JSON.stringify({ type: "change_partner" }));
}
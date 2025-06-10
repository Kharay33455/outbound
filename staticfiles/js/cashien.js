const auth_cookie = document.getElementById("auth_cookie").innerHTML.toString().trim();
const trade_id = document.getElementById("trade_id").innerHTML.toString().trim();
let ws;


const appendNewMessage = (message) => {
    const msgBox = document.getElementById("messages");
    const wrapper = document.createElement("div");
    wrapper.classList.add("msgWrapper");
    const bh = document.getElementById("bh").innerHTML.toString().trim();

    const sender = document.createElement("p");
    sender.classList.add("sender");
    sender.innerHTML = "From " + message.sender;
    wrapper.appendChild(sender);

    if (message.image !== null) {
        const imgDiv = document.createElement("img");
        imgDiv.src = bh + message.image;
        imgDiv.classList.add("msgImg")
        wrapper.appendChild(imgDiv);
        msgBox.appendChild(wrapper);
    }
    const textBox = document.createElement("p")
    textBox.innerHTML = message.text;
    wrapper.appendChild(textBox);
    msgBox.appendChild(wrapper);
    document.getElementById("msgBox").scrollTo({
        top: msgBox.scrollHeight,
        behavior: "smooth"
    })
}


const SendNewMessage = () => {
    const text = document.getElementById("inputText").value.trim();
    const img = document.getElementById("inputImg").files[0];
    const send = (imageToSend) => {
        if (text.length === 0 && imageToSend === null) {
            return;
        }
        const msg_id = Math.floor(1000000000 + Math.random() * 9000000000).toString();
        ws.send(JSON.stringify({ "text": text, "img": imageToSend, "type": "newMessage", "msg_id": msg_id }));
        document.getElementById("inputText").value = "";
        document.getElementById("inputImg").value = "";
    }

    if (img) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const imageToSend = e.target.result;
            send(imageToSend);
        }
        reader.readAsDataURL(img);
    }
    else {
        send(null);
    }


}


const Init = () => {
    console.log(window.location.protocol)

    if (window.location.protocol === "http:") {
        ws = new WebSocket("ws://" + window.location.host + "/ws/cashien/dispute/" + trade_id + "/" + auth_cookie + "/");

    } else {
        ws = new WebSocket("wss://" + window.location.host + "/ws/cashien/dispute/" + trade_id + "/" + auth_cookie + "/");
    }
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        switch (data['type']) {
            case "dispute_data":
                document.getElementById("msgBox").removeChild(document.getElementById("spinner"));
                document.getElementById("newMessage").style.opacity = "1";
                data.data.messages.forEach((item) => {
                    appendNewMessage(item);
                });
                break;
            case "new_message":
                appendNewMessage(data.data);
                break;
            default:
                break;
        }
    }
}

Init();

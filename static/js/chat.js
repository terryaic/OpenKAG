document.getElementById('send-button').addEventListener('click', function() {
    const input = document.getElementById('message-input');
    const message = input.value;
    if (message) {
        addToChatBox('You: ' + message);
        input.value = ''; // 清空输入框
        sendMessageToAPI(message);
    }
});

function addToChatBox(text) {
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += '<p>' + text + '</p>';
    chatBox.scrollTop = chatBox.scrollHeight; // 滚动到底部
}

function sendMessageToAPI_json(message) {
    // 示例API请求，实际使用时替换为相应的API
    fetch('http://localhost:8000/search', {
        method: 'POST',
        body: JSON.stringify({ message: message }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        addToChatBox('AI: ' + data.response);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function sendMessageToAPI(message) {
    // 示例API请求，实际使用时替换为相应的API
    const formData = new FormData();
    formData.append('message', message);

    fetch('http://localhost:8000/search', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        addToChatBox('AI: ' + data.response);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
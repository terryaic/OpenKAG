document.addEventListener('DOMContentLoaded', function() {
    // Define your base URL
    const baseUrl = 'http://localhost:8000/streamingsearch';

    // Define the parameters you want to pass
    const params = {
        message: 'how to use agent'
    };

    // Create a query string from the parameters
    const queryString = new URLSearchParams(params).toString();

    // Combine the base URL with the query string
    const urlWithParams = `${baseUrl}?${queryString}`;

    // Pass the full URL including parameters to the EventSource constructor
    const eventSource = new EventSource(urlWithParams);

    // 监听服务器发送的消息
    eventSource.onmessage = function(event) {
        console.log('Message received:', event.data);
        const data = JSON.parse(event.data);
        displayMessage(data);
    };

    // 处理可能的错误
    eventSource.onerror = function(error) {
        console.error('EventSource Error:', error);
        eventSource.close(); // 关闭连接
    };

    // 显示消息的函数
    function displayMessage(data) {
        const messagesDiv = document.getElementById('messages');
        const messageElement = document.createElement('div');
        messageElement.textContent = JSON.stringify(data);
        messagesDiv.appendChild(messageElement);
    }
});

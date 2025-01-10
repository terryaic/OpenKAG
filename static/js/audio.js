const audioContext = new (window.AudioContext || window.webkitAudioContext)();
let audioQueue = []; // 音频缓冲区队列
let isPlaying = false; // 当前是否正在播放

const auidosocket = new WebSocket('ws://localhost:8000/audio');
auidosocket.binaryType = 'arraybuffer';

auidosocket.onmessage = function(event) {
    const audioData = event.data;
    audioContext.decodeAudioData(audioData, function(buffer) {
        audioQueue.push(buffer);
        if (!isPlaying) {
            playNextAudio();
        }
    }, function(e) {
        console.log("Error with decoding audio data" + e.err);
    });
};

function playNextAudio() {
    if (audioQueue.length > 0) {
        const buffer = audioQueue.shift(); // 从队列中取出下一个音频片段
        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        source.start(0);
        isPlaying = true;
        source.onended = function() {
            isPlaying = false;
            playNextAudio(); // 当一段音频播放完毕后，播放下一段
        };
    }
}

let tt = null;
auidosocket.onopen = function() {
    console.log("Connected to the WebSocket server.");
    tt = setInterval(function(){
        auidosocket.send("HELLO");
    }, 50);
};

auidosocket.onerror = function(error) {
    console.log("WebSocket Error: " + error);
};

auidosocket.onclose = function(){
    clearInterval(tt);
}
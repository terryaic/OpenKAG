var domain = window.location.host;
var asr_url = `${window.location.protocol}//${domain}/audiochat`;
console.log(asr_url)

// 获取必要的元素
const cookieButton = document.getElementById('cookieButton');
const loadingAnimation = document.getElementById('loadingAnimation');

let mediaRecorder;
let audioChunks = [];
let audioStream = null;
let callback = null;
var audioEnabled=false;
function guid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
    return v.toString(16);
  });
}
var session_id=guid();
var mode = 'chat';
function set_mode(value){
    console.log("set mode to:" + value);
    //showToast("mode set to"+value,"info",5000); 
    mode = value;
}
function get_mode(){
    return mode;
}
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
let audioQueue = []; // 音频缓冲区队列
let isPlaying = false; // 当前是否正在播放
var currentAudio = null;

let isTouchDevice = false;
// 绑定事件监听器
cookieButton.addEventListener('mousedown', (e) => {
    if (!isTouchDevice) { // 如果不是触摸设备
        e.preventDefault(); // 防止默认行为
        startRecording();
    }
});

cookieButton.addEventListener('mouseup', (e) => {
    if (!isTouchDevice) { // 如果不是触摸设备
        stopRecording();
    }
});

cookieButton.addEventListener('touchstart', (e) => {
    isTouchDevice = true; // 标记为触摸设备
    e.preventDefault(); // 防止默认行为，如长按出现菜单
    startRecording();
}, { passive: false });

cookieButton.addEventListener('touchend', (e) => {
    stopRecording();
});

function permission_req(){
    navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };
    });
}

function startRecording() {
    if (isPlaying){
        stopVoice();
    }
    audioEnabled=true;
    audioChunks = [];
    mediaRecorder.start();
}

function stopRecording() {
    // 显示加载动画
    loadingAnimation.style.display = 'block';
    // 停止录音
    mediaRecorder.stop();

    mediaRecorder.onstop = () => {
        // 生成音频 Blob
        const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg-3' });

        // 发送音频到服务器
        sendAudioToServer(audioBlob);

    };
}

function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append("session_id", session_id);
    formData.append("mode", mode);
    formData.append("locale", language);
    formData.append("file", audioBlob, "recording.mp3");

    // 替换为你的服务器API
    fetch(asr_url, {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        loadingAnimation.style.display = 'none';
        console.log(data);
        if (callback != null){
            callback(data.text)
        }
    })
    .catch(error => {
        loadingAnimation.style.display = 'none';
        console.error(error);
    });
}

function playAudioResponse(audioBlob) {
    // 停止加载动画
    loadingAnimation.style.display = 'none';
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.play();
}

function playNextAudio() {
    if (audioQueue.length > 0) {
        const buffer = audioQueue.shift(); // 从队列中取出下一个音频片段
        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        source.start(0);
        isPlaying = true;
        currentAudio = source;
        source.onended = function() {
            isPlaying = false;
            currentAudio = null;
            playNextAudio(); // 当一段音频播放完毕后，播放下一段
        };
        document.getElementById('stopButton').style="visibility: inherited;"
    }else{
        document.getElementById('stopButton').style="visibility: hidden;"
    }
}

function on_audio(event){
    if (!audioEnabled)
        return;
    console.log("receive audio event")
    console.log(event)
    var reader = new FileReader();
    reader.onload = function(){
        var audioData = reader.result
        console.log(audioData);
        audioContext.decodeAudioData(audioData, function(buffer) {
            audioQueue.push(buffer);
            if (!isPlaying) {
                playNextAudio();
            }
        }, function(e) {
            console.log("Error with decoding audio data" + e.err);
        });
    }
    reader.readAsArrayBuffer(event.data);
}

function init_audio_socket(){
    var ws_url = `ws://${domain}/audio`
    if (window.location.protocol.endsWith('https:'))
        ws_url = `wss://${domain}/audio`;
    ausocket = new WebSocket(ws_url);
    ausocket.addEventListener('open', function (event) {
        console.log('Connected to audio Server');
        cmd = {"mode":"cmd", "message":{"session_id":session_id}};
        text = JSON.stringify(cmd)
        ausocket.send(text)
    });

    ausocket.addEventListener('message', on_audio);

    ausocket.addEventListener('close', function (event) {
        console.log('Disconnected from audio Server');
        init_audio_socket();
    });
}

function reset_audioQueue(){
    while (audioQueue.length > 0)
        audioQueue.shift()
}


function stopVoice() {
    console.log("stop audio!!")

    audioEnabled = false;

    const formData = new FormData();
    var request = new XMLHttpRequest();
    var STOP_URL = `${window.location.protocol}//${domain}/stop_audio`;

    request.open("POST", STOP_URL, true);
    request.send(formData);

    reset_audioQueue();

    if (currentAudio != null)
        currentAudio.stop();
    
};
language = "mandarin";
function setLanguage(lang){
    language = lang;
}

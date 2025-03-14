var domain = window.location.host;
var asr_url = `${window.location.protocol}//${domain}/avatarchat`;
console.log(asr_url)


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

let audioQueue = []; // 音频缓冲区队列
var currentAudio = null;

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
    audioEnabled=true;
    audioChunks = [];
    mediaRecorder.start();
}

function stopRecording() {
    // 停止录音
    mediaRecorder.stop();

    mediaRecorder.onstop = () => {
        // 生成音频 Blob
        const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg-3' });

        // 发送音频到服务器
        sendAudioToServer(audioBlob);

    };
}

async function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append("session_id", session_id);
    formData.append("mode", mode);
    formData.append("locale", language);
    formData.append("kdb_id", kdb_id);
    formData.append("prompt_name", prompt_name);
    formData.append("speaker_id", speaker_id);
    formData.append("file", audioBlob, "recording.mp3");

    // 替换为你的服务器API
    const response = await fetch(asr_url, {
        method: "POST",
        body: formData
    })
    if (callback != null){
        await callback(response)
    }
}

language = "mandarin";
function setLanguage(lang){
    language = lang;
}

function set_audio_callback(cb){
    callback = cb;
}

var kdb_id = "";
function set_kdb_id(id){
    kdb_id = id;
}
function set_asr_url(url){
    asr_url = url;
}
function set_session_id(sid){
    console.log("session_id:"+sid);
    session_id = sid;
}
var prompt_name = "";
function set_prompt_name(name){
    prompt_name = name;
}
var speaker_id= "";
function set_speaker_id(name){
    speaker_id = name;
}

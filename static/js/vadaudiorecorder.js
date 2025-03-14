var domain = window.location.host;
var asr_url = `${window.location.protocol}//${domain}/avatarchat`;
console.log(asr_url)


let mediaRecorder;
let audioChunks = [];
let audioStream = null;
let callback = null;
let callback_start = null;
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
var myvad = null;

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
    if (myvad == null){
        processAudioStream();
    }else{
        myvad.start()
    }
}

function stopRecording() {
    myvad.pause();
}

var interruptCallback = null;
function set_interrupt_callback(cb){
    interruptCallback = cb;
}
async function processAudioStream() {
    myvad = await vad.MicVAD.new({
      model: "v5",
      frameSamples:512,
      preSpeechPadFrames:3,
      redemptionFrames:24,
      minSpeechFrames:9,
      userSpeakingThreshold:0.6,
      //stream:micStream,
      onSpeechStart: () => {
        console.log("Speech start detected")
        if (interruptCallback){
            interruptCallback();
        }
      },
      onSpeechEnd: (micStream) => {
        console.log("Speech End detected");
        // Function to encode Float32Array into WAV format
        function encodeWAV(samples, sampleRate) {
          const buffer = new ArrayBuffer(44 + samples.length * 2);
          const view = new DataView(buffer);
      
          // Write WAV header
          function writeString(view, offset, string) {
            for (let i = 0; i < string.length; i++) {
              view.setUint8(offset + i, string.charCodeAt(i));
            }
          }
      
          writeString(view, 0, "RIFF"); // ChunkID
          view.setUint32(4, 36 + samples.length * 2, true); // ChunkSize
          writeString(view, 8, "WAVE"); // Format
          writeString(view, 12, "fmt "); // Subchunk1ID
          view.setUint32(16, 16, true); // Subchunk1Size
          view.setUint16(20, 1, true); // AudioFormat (1 = PCM)
          view.setUint16(22, 1, true); // NumChannels
          view.setUint32(24, sampleRate, true); // SampleRate
          view.setUint32(28, sampleRate * 2, true); // ByteRate (SampleRate * NumChannels * BytesPerSample)
          view.setUint16(32, 2, true); // BlockAlign (NumChannels * BytesPerSample)
          view.setUint16(34, 16, true); // BitsPerSample
          writeString(view, 36, "data"); // Subchunk2ID
          view.setUint32(40, samples.length * 2, true); // Subchunk2Size
      
          // Write PCM samples
          let offset = 44;
          for (let i = 0; i < samples.length; i++, offset += 2) {
            const s = Math.max(-1, Math.min(1, samples[i])); // Clamp to [-1, 1]
            view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true); // Convert to 16-bit PCM
          }
      
          return buffer;
        }
      
        // Convert Float32Array to WAV and create a Blob
        const audioBuffer = encodeWAV(micStream, 16000);
        const audioBlob = new Blob([audioBuffer], { type: "audio/wav" });
        //const audioUrl = URL.createObjectURL(audioBlob);
        sendAudioToServer(audioBlob);
      }
    })
    myvad.start();
  }

async function sendAudioToServer(audioBlob) {
    if (callback_start){
        callback_start();
    }
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

function set_audio_callback_start(cb){
    callback_start = cb;
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

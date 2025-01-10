let mediaRecorder;
let audioChunks = [];
let asr_url = "http://13902254981.tpddns.cn:8089/api/generate";
var domain = window.location.host;
var pos = window.location.href.length - window.location.pathname.length
var base_url = window.location.href.substring(0, pos);
parts = window.location.pathname.split("/")
if (parts.length > 3){
    base_url += "/" + parts[1]
}
console.log(base_url)
var hostname=domain.split(":")[0]
//asr_url = `${window.location.protocol}//${hostname}:8089/api/generate`;
//asr_url = `${window.location.protocol}//${hostname}:8443/asr/api/generate`;
asr_url = `${window.location.protocol}//${domain}/asr/generate`;

console.log(asr_url)

function startRecording() {
    audioChunks = [];
    navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };
        mediaRecorder.start();
    });

}

function stopRecording(callback=null) {
    mediaRecorder.stop();
    mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg-3' });
        // 判断语言的长度
        console.log("录音的长度:",audioBlob)
        
        // 检查录音文件大小，假设小于 1000 字节表示时间太短
        if (audioBlob.size < 1000) {
            alert(resources["re_mes"]);
            return;
        }
        const formData = new FormData();
        formData.append("file", audioBlob, "recording.mp3");

        

        // 替换为你的服务器API
        fetch(asr_url, {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            if (callback != null){
                callback(data.text)
            }
        })
        .catch(error => {
            console.error(error);
        });
    }
}

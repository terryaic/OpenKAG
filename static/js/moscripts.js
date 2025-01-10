let isRecording = false;
let mediaRecorder;
let chunks = [];
let record_callback = null;
var domain = window.location.host;
asr_url = `${window.location.protocol}//${domain}/asr/generate`;

// Get the record button
const recordButton = document.getElementById('recordButton');

// Check for browser support
if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    console.log('getUserMedia supported.');

    // Add event listener for button click
    recordButton.addEventListener('click', toggleRecording);

} else {
    console.log('getUserMedia not supported on your browser!');
}

function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

function startRecording() {
    chunks = [];
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            isRecording = true;
            recordButton.classList.add('recording');

            mediaRecorder.ondataavailable = e => {
                chunks.push(e.data);
            };

            mediaRecorder.onstop = e => {
        const audioBlob = new Blob(chunks, { type: 'audio/mpeg-3' });
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
            if (record_callback != null){
                record_callback(data.text)
            }
        })
        .catch(error => {
            console.error(error);
        });
            };
        })
        .catch(err => {
            console.log('The following error occurred: ' + err);
        });
}

function stopRecording() {
    mediaRecorder.stop();
    isRecording = false;
    recordButton.classList.remove('recording');
}

function setup_record_cb(callback){
    record_callback = callback;
}

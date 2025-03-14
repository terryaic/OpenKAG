async function setupAudioVisualization() {
  /*
  // 获取音频上下文
  const audioContext = new AudioContext();
  const constraints = {
    audio: {
      echoCancellation: true, // Enable echo cancellation
      noiseSuppression: true,  // Enable noise suppression
      autoGainControl: true    // Enable automatic gain control
    }
  };
  // 获取麦克风音频流
  const micStream = await navigator.mediaDevices.getUserMedia(constraints);
  this.processAudioStream(micStream)
  */
  this.processAudioStream()
}

let audioChunks=[]

async function processAudioStream() {
  const myvad = await vad.MicVAD.new({
    model: "v5",
    frameSamples:512,
    preSpeechPadFrames:3,
    redemptionFrames:24,
    minSpeechFrames:9,
    userSpeakingThreshold:0.6,
    //stream:micStream,
    onSpeechStart: () => {
      console.log("Speech start detected")
    },
    onSpeechEnd: (micStream) => {
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
      const audioUrl = URL.createObjectURL(audioBlob);
    
      // Create an audio element to play the recorded audio
      const audio = document.createElement("audio");
      audio.src = audioUrl;
      audio.controls = true; // Add playback controls
      document.getElementById("audioContainer").appendChild(audio); // Append audio element to the page
    
      console.log("Speech End detected");
    }
  })
myvad.start()
}
// 合并麦克风和扬声器音频流


// 调用函数设置可视化
const audioContainer = document.getElementById("audioContainer");
setupAudioVisualization();


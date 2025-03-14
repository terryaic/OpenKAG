const SAMPLE_RATE = 22050;

var complete_callback = null;
function set_complete_callback(cb){
    complete_callback = cb;
}

async function playStreamedPCM(response) {
    console.log("play stream pcm")
    const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: SAMPLE_RATE });
    
    if (!response.body) {
        throw new Error("Readable stream not supported in this browser.");
    }

    const reader = response.body.getReader();
    const sampleSize = 2; // 16-bit PCM = 2 bytes per sample
    let leftover = new Uint8Array(0);
    let playbackOffset = audioContext.currentTime; // Track playback offset

    async function processAudioStream() {
        var totalBytes = 0;
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            totalBytes += value.length

            // 合并未对齐的剩余数据和新数据
            const chunk = new Uint8Array(leftover.length + value.length);
            chunk.set(leftover, 0);
            chunk.set(value, leftover.length);

            // 计算对齐后的长度（必须是 2 的倍数）
            const alignedLength = chunk.length - (chunk.length % sampleSize);

            // 提取对齐部分
            const alignedData = chunk.slice(0, alignedLength);

            // 保存未对齐部分
            leftover = chunk.slice(alignedLength);

            // 解码 PCM 数据
            const audioBuffer = await decodePCM(alignedData, audioContext);

            // Schedule playback at the correct time
            playbackOffset = playAudioBuffer(audioBuffer, audioContext, playbackOffset);
        }

        console.log("Audio streaming complete. len:" + totalBytes);
        if (complete_callback){
            complete_callback();
        }
    }

    await processAudioStream();
}

// Decode PCM data into AudioBuffer
function decodePCM(data, audioContext) {
    const float32Array = new Float32Array(data.length / 2);
    const view = new DataView(data.buffer);
    for (let i = 0; i < float32Array.length; i++) {
        const sample = view.getInt16(i * 2, true); // 小端字节序
        float32Array[i] = sample / 32768; // 归一化到 [-1, 1]
    }

    const audioBuffer = audioContext.createBuffer(1, float32Array.length, audioContext.sampleRate);
    audioBuffer.copyToChannel(float32Array, 0);
    return audioBuffer;
}

// Play the decoded AudioBuffer sequentially
function playAudioBuffer(audioBuffer, audioContext, playbackOffset) {
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);

    // Schedule playback at the next available time
    const startTime = Math.max(playbackOffset, audioContext.currentTime);
    source.start(startTime);

    // Update playback offset for the next chunk
    return startTime + audioBuffer.duration;
}

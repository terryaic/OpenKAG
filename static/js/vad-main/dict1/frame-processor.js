"use strict";
/*
Some of this code, together with the default options found in index.ts,
were taken (or took inspiration) from https://github.com/snakers4/silero-vad
*/
Object.defineProperty(exports, "__esModule", { value: true });
exports.FrameProcessor = exports.validateOptions = exports.defaultV5FrameProcessorOptions = exports.defaultLegacyFrameProcessorOptions = void 0;
const logging_1 = require("./logging");
const messages_1 = require("./messages");
const RECOMMENDED_FRAME_SAMPLES = [512, 1024, 1536];
exports.defaultLegacyFrameProcessorOptions = {
    positiveSpeechThreshold: 0.5,
    negativeSpeechThreshold: 0.5 - 0.15,
    preSpeechPadFrames: 1,
    redemptionFrames: 8,
    frameSamples: 1536,
    minSpeechFrames: 3,
    submitUserSpeechOnPause: false,
};
exports.defaultV5FrameProcessorOptions = {
    positiveSpeechThreshold: 0.5,
    negativeSpeechThreshold: 0.5 - 0.15,
    preSpeechPadFrames: 3,
    redemptionFrames: 24,
    frameSamples: 512,
    minSpeechFrames: 9,
    submitUserSpeechOnPause: false,
};
function validateOptions(options) {
    if (!RECOMMENDED_FRAME_SAMPLES.includes(options.frameSamples)) {
        logging_1.log.warn("You are using an unusual frame size");
    }
    if (options.positiveSpeechThreshold < 0 ||
        options.positiveSpeechThreshold > 1) {
        logging_1.log.error("positiveSpeechThreshold should be a number between 0 and 1");
    }
    if (options.negativeSpeechThreshold < 0 ||
        options.negativeSpeechThreshold > options.positiveSpeechThreshold) {
        logging_1.log.error("negativeSpeechThreshold should be between 0 and positiveSpeechThreshold");
    }
    if (options.preSpeechPadFrames < 0) {
        logging_1.log.error("preSpeechPadFrames should be positive");
    }
    if (options.redemptionFrames < 0) {
        logging_1.log.error("redemptionFrames should be positive");
    }
}
exports.validateOptions = validateOptions;
const concatArrays = (arrays) => {
    const sizes = arrays.reduce((out, next) => {
        out.push(out.at(-1) + next.length);
        return out;
    }, [0]);
    const outArray = new Float32Array(sizes.at(-1));
    arrays.forEach((arr, index) => {
        const place = sizes[index];
        outArray.set(arr, place);
    });
    return outArray;
};
class FrameProcessor {
    constructor(modelProcessFunc, modelResetFunc, options) {
        this.modelProcessFunc = modelProcessFunc;
        this.modelResetFunc = modelResetFunc;
        this.options = options;
        this.speaking = false;
        this.redemptionCounter = 0;
        this.speechFrameCount = 0;
        this.active = false;
        this.reset = () => {
            this.speaking = false;
            this.audioBuffer = [];
            this.modelResetFunc();
            this.redemptionCounter = 0;
            this.speechFrameCount = 0;
        };
        this.pause = () => {
            this.active = false;
            if (this.options.submitUserSpeechOnPause) {
                return this.endSegment();
            }
            else {
                this.reset();
                return {};
            }
        };
        this.resume = () => {
            this.active = true;
        };
        this.endSegment = () => {
            const audioBuffer = this.audioBuffer;
            this.audioBuffer = [];
            const speaking = this.speaking;
            this.reset();
            const speechFrameCount = audioBuffer.reduce((acc, item) => {
                return acc + +item.isSpeech;
            }, 0);
            if (speaking) {
                if (speechFrameCount >= this.options.minSpeechFrames) {
                    const audio = concatArrays(audioBuffer.map((item) => item.frame));
                    return { msg: messages_1.Message.SpeechEnd, audio };
                }
                else {
                    return { msg: messages_1.Message.VADMisfire };
                }
            }
            return {};
        };
        this.process = async (frame) => {
            if (!this.active) {
                return {};
            }
            const probs = await this.modelProcessFunc(frame);
            const isSpeech = probs.isSpeech >= this.options.positiveSpeechThreshold;
            this.audioBuffer.push({
                frame,
                isSpeech,
            });
            if (isSpeech) {
                this.speechFrameCount++;
            }
            if (probs.isSpeech >= this.options.positiveSpeechThreshold &&
                this.redemptionCounter) {
                this.redemptionCounter = 0;
            }
            if (probs.isSpeech >= this.options.positiveSpeechThreshold &&
                !this.speaking) {
                this.speaking = true;
                return { probs, msg: messages_1.Message.SpeechStart, frame };
            }
            if (this.speaking &&
                this.speechFrameCount === this.options.minSpeechFrames) {
                return { probs, msg: messages_1.Message.SpeechRealStart, frame };
            }
            if (probs.isSpeech < this.options.negativeSpeechThreshold &&
                this.speaking &&
                ++this.redemptionCounter >= this.options.redemptionFrames) {
                this.redemptionCounter = 0;
                this.speaking = false;
                const audioBuffer = this.audioBuffer;
                this.audioBuffer = [];
                const speechFrameCount = audioBuffer.reduce((acc, item) => {
                    return acc + +item.isSpeech;
                }, 0);
                if (speechFrameCount >= this.options.minSpeechFrames) {
                    const audio = concatArrays(audioBuffer.map((item) => item.frame));
                    return { probs, msg: messages_1.Message.SpeechEnd, audio, frame };
                }
                else {
                    return { probs, msg: messages_1.Message.VADMisfire, frame };
                }
            }
            if (!this.speaking) {
                while (this.audioBuffer.length > this.options.preSpeechPadFrames) {
                    this.audioBuffer.shift();
                }
                this.speechFrameCount = 0;
            }
            return { probs, frame };
        };
        this.audioBuffer = [];
        this.reset();
    }
}
exports.FrameProcessor = FrameProcessor;
//# sourceMappingURL=frame-processor.js.map
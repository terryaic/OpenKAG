"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PlatformAgnosticNonRealTimeVAD = exports.defaultNonRealTimeVADOptions = void 0;
const frame_processor_1 = require("./frame-processor");
const messages_1 = require("./messages");
const models_1 = require("./models");
const resampler_1 = require("./resampler");
exports.defaultNonRealTimeVADOptions = {
    ...frame_processor_1.defaultLegacyFrameProcessorOptions,
    ortConfig: undefined,
};
class PlatformAgnosticNonRealTimeVAD {
    static async _new(modelFetcher, ort, options = {}) {
        const fullOptions = {
            ...exports.defaultNonRealTimeVADOptions,
            ...options,
        };
        if (fullOptions.ortConfig !== undefined) {
            fullOptions.ortConfig(ort);
        }
        const vad = new this(modelFetcher, ort, fullOptions);
        await vad.init();
        return vad;
    }
    constructor(modelFetcher, ort, options) {
        this.modelFetcher = modelFetcher;
        this.ort = ort;
        this.options = options;
        this.init = async () => {
            const model = await models_1.SileroLegacy.new(this.ort, this.modelFetcher);
            this.frameProcessor = new frame_processor_1.FrameProcessor(model.process, model.reset_state, {
                frameSamples: this.options.frameSamples,
                positiveSpeechThreshold: this.options.positiveSpeechThreshold,
                negativeSpeechThreshold: this.options.negativeSpeechThreshold,
                redemptionFrames: this.options.redemptionFrames,
                preSpeechPadFrames: this.options.preSpeechPadFrames,
                minSpeechFrames: this.options.minSpeechFrames,
                submitUserSpeechOnPause: this.options.submitUserSpeechOnPause,
            });
            this.frameProcessor.resume();
        };
        this.run = async function* (inputAudio, sampleRate) {
            const resamplerOptions = {
                nativeSampleRate: sampleRate,
                targetSampleRate: 16000,
                targetFrameSize: this.options.frameSamples,
            };
            const resampler = new resampler_1.Resampler(resamplerOptions);
            let start = 0;
            let end = 0;
            let frameIndex = 0;
            for await (const frame of resampler.stream(inputAudio)) {
                const { msg, audio } = await this.frameProcessor.process(frame);
                switch (msg) {
                    case messages_1.Message.SpeechStart:
                        start = (frameIndex * this.options.frameSamples) / 16;
                        break;
                    case messages_1.Message.SpeechEnd:
                        end = ((frameIndex + 1) * this.options.frameSamples) / 16;
                        yield { audio, start, end };
                        break;
                    default:
                        break;
                }
                frameIndex++;
            }
            const { msg, audio } = this.frameProcessor.endSegment();
            if (msg == messages_1.Message.SpeechEnd) {
                yield {
                    audio,
                    start,
                    end: (frameIndex * this.options.frameSamples) / 16,
                };
            }
        };
        (0, frame_processor_1.validateOptions)(options);
    }
}
exports.PlatformAgnosticNonRealTimeVAD = PlatformAgnosticNonRealTimeVAD;
//# sourceMappingURL=non-real-time-vad.js.map
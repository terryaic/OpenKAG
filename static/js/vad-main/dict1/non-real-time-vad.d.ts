import { FrameProcessorInterface, FrameProcessorOptions } from "./frame-processor";
import { ModelFetcher, OrtModule, OrtOptions } from "./models";
interface NonRealTimeVADSpeechData {
    audio: Float32Array;
    start: number;
    end: number;
}
export interface NonRealTimeVADOptions extends FrameProcessorOptions, OrtOptions {
}
export declare const defaultNonRealTimeVADOptions: NonRealTimeVADOptions;
export declare class PlatformAgnosticNonRealTimeVAD {
    modelFetcher: ModelFetcher;
    ort: OrtModule;
    options: NonRealTimeVADOptions;
    frameProcessor: FrameProcessorInterface | undefined;
    static _new<T extends PlatformAgnosticNonRealTimeVAD>(modelFetcher: ModelFetcher, ort: OrtModule, options?: Partial<NonRealTimeVADOptions>): Promise<T>;
    constructor(modelFetcher: ModelFetcher, ort: OrtModule, options: NonRealTimeVADOptions);
    init: () => Promise<void>;
    run: (inputAudio: Float32Array, sampleRate: number) => AsyncGenerator<NonRealTimeVADSpeechData>;
}
export {};
//# sourceMappingURL=non-real-time-vad.d.ts.map
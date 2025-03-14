import { FrameProcessor, FrameProcessorOptions } from "./frame-processor";
import { Message } from "./messages";
import { NonRealTimeVADOptions, PlatformAgnosticNonRealTimeVAD } from "./non-real-time-vad";
import { arrayBufferToBase64, audioFileToArray, encodeWAV, minFramesForTargetMS } from "./utils";
export interface NonRealTimeVADOptionsWeb extends NonRealTimeVADOptions {
    modelURL: string;
    modelFetcher: (path: string) => Promise<ArrayBuffer>;
}
export declare const defaultNonRealTimeVADOptions: {
    modelURL: string;
    modelFetcher: (path: string) => Promise<ArrayBuffer>;
};
declare class NonRealTimeVAD extends PlatformAgnosticNonRealTimeVAD {
    static new(options?: Partial<NonRealTimeVADOptionsWeb>): Promise<NonRealTimeVAD>;
}
export declare const utils: {
    audioFileToArray: typeof audioFileToArray;
    minFramesForTargetMS: typeof minFramesForTargetMS;
    arrayBufferToBase64: typeof arrayBufferToBase64;
    encodeWAV: typeof encodeWAV;
};
export { AudioNodeVAD, DEFAULT_MODEL, MicVAD, getDefaultRealTimeVADOptions, } from "./real-time-vad";
export type { RealTimeVADOptions } from "./real-time-vad";
export { FrameProcessor, Message, NonRealTimeVAD };
export type { FrameProcessorOptions, NonRealTimeVADOptions };
//# sourceMappingURL=index.d.ts.map
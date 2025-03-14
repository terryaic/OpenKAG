"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.NonRealTimeVAD = exports.Message = exports.FrameProcessor = exports.getDefaultRealTimeVADOptions = exports.MicVAD = exports.DEFAULT_MODEL = exports.AudioNodeVAD = exports.utils = exports.defaultNonRealTimeVADOptions = void 0;
const ort = __importStar(require("onnxruntime-web"));
const asset_path_1 = require("./asset-path");
const default_model_fetcher_1 = require("./default-model-fetcher");
const frame_processor_1 = require("./frame-processor");
Object.defineProperty(exports, "FrameProcessor", { enumerable: true, get: function () { return frame_processor_1.FrameProcessor; } });
const messages_1 = require("./messages");
Object.defineProperty(exports, "Message", { enumerable: true, get: function () { return messages_1.Message; } });
const non_real_time_vad_1 = require("./non-real-time-vad");
const utils_1 = require("./utils");
exports.defaultNonRealTimeVADOptions = {
    modelURL: asset_path_1.baseAssetPath + "silero_vad_legacy.onnx",
    modelFetcher: default_model_fetcher_1.defaultModelFetcher,
};
class NonRealTimeVAD extends non_real_time_vad_1.PlatformAgnosticNonRealTimeVAD {
    static async new(options = {}) {
        const { modelURL, modelFetcher } = {
            ...exports.defaultNonRealTimeVADOptions,
            ...options,
        };
        return await this._new(() => modelFetcher(modelURL), ort, options);
    }
}
exports.NonRealTimeVAD = NonRealTimeVAD;
exports.utils = {
    audioFileToArray: utils_1.audioFileToArray,
    minFramesForTargetMS: utils_1.minFramesForTargetMS,
    arrayBufferToBase64: utils_1.arrayBufferToBase64,
    encodeWAV: utils_1.encodeWAV,
};
var real_time_vad_1 = require("./real-time-vad");
Object.defineProperty(exports, "AudioNodeVAD", { enumerable: true, get: function () { return real_time_vad_1.AudioNodeVAD; } });
Object.defineProperty(exports, "DEFAULT_MODEL", { enumerable: true, get: function () { return real_time_vad_1.DEFAULT_MODEL; } });
Object.defineProperty(exports, "MicVAD", { enumerable: true, get: function () { return real_time_vad_1.MicVAD; } });
Object.defineProperty(exports, "getDefaultRealTimeVADOptions", { enumerable: true, get: function () { return real_time_vad_1.getDefaultRealTimeVADOptions; } });
//# sourceMappingURL=index.js.map
/*********************************************************************************
 * The MIT License (MIT)
 *
 * Copyright (c) 2020 NVIDIA Corporation
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of
 * this software and associated documentation files (the "Software"), to deal in
 * the Software without restriction, including without limitation the rights to
 * use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 * the Software, and to permit persons to whom the Software is furnished to do so,
 * subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
 * FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
 * COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
 * IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 *********************************************************************************/

class StreamClientModel {

    constructor(url = undefined) {
        this.url = url;
        this.videosocket = null;
        this.frame = -1;
        this.mostRecentFrame = null;
        this.nviews = 0;
        this.reconnecting = false;
        this.eventListeners = {};
        this.timeAtLastAvg = 0;
        this.printToConsole = false;
    }

    //methods
    debug(msg) {
        if (this.printToConsole) {
            console.log(`[model]: ${msg}`);
        }
    }

    on(event, callback, thisArg = null) {
        if (!this.eventListeners.hasOwnProperty(event)) {
            this.eventListeners[event] = new Array();
        }
        this.eventListeners[event].push({callbackFn: callback, thisArg: thisArg});
    }

    trigger(event) {
        if (!this.eventListeners.hasOwnProperty(event)) {
            return;
        }

        var callbackArgs = new Array(arguments.length - 1);
        for (var i = 1; i < arguments.length; ++i) {
            callbackArgs[i-1] = arguments[i];
        }
        var callbackSpecs = this.eventListeners[event];
        for (var i = 0; i < callbackSpecs.length; ++i) {
            var callbackSpec = callbackSpecs[i];
            callbackSpec.callbackFn.apply(callbackSpec.thisArg, callbackArgs);
        }
    }

    get(varname) {
        if (!this.hasOwnProperty(varname)) {
            return undefined;
        }
        return this[varname];
    }

    set(varname, value) {
        this[varname] = value;
        this.trigger("change:"+varname);
    }

    /**
     * Provide an estimated FPS of the client browser window.
     *
     * @returns {Promise<number>} A Promise to be fulfilled with an estimated FPS of the client browser, based on the
     * approximation provided by successive calls to `requestAnimationFrame()`.
     */
    getFPS() {
        return new Promise(resolve => {
            requestAnimationFrame(t1 => {
                requestAnimationFrame(t2 => {
                    resolve(1000.0 / (t2 - t1));
                });
            });
        });
    }

    /**
     * Return the port number of the WebSocket server.
     *
     * @returns {Promise<Object>} A Promise to be fulfilled with information of the WebSocket server port number, and
     * whether it supports secure `wss://` connections.
     */
    async getWebSocketServerInformation() {
        const response = await fetch('/streaming/websocket-server-information');
        return response.json();
    }

    /**
     * Initialize the Model, by configuring the URL of the WebSocket server which will deliver the streamed frames.
     *
     * @return {Promise<void>} A Promise to be fulfilled once the Model has been initialized.
     */
    async initialize() {
        if (this.get('url') === undefined) {
            //attempt to get server name from URL
            var link = document.createElement('a');
            link.href = window.location.href;
            var servername = link.hostname;
            if (servername) {
                const { port, supportsSecureConnections } = await this.getWebSocketServerInformation();
                this.debug(`Setting url based on server name: \"${servername}\"`);
                const url = `${supportsSecureConnections ? 'wss' : 'ws'}://${servername}:${port}`;
                this.set('url', url);
            }
        }

        // Force the use of WebSocket secure (`wss://`) when content is served over HTTPS:
        const url = this.get('url');
        if (window.location.protocol === 'https:' && url.startsWith('ws:')) {
            this.set('url', url.replace('ws:', 'wss:'));
        }

        this._drawWebSocketURLInformation(this.get('url'));
    }

    connectToServer() {
        if ("WebSocket" in window) {
            if (this.videosocket == null) { // first connect call
                var that = this;
                document.addEventListener('visibilitychange', function () {
                    if (document.visibilityState === 'hidden') {
                        that.debug("document is now hidden; disconnecting");
                        that.disconnect();
                    } else {
                        that.debug("document is now visible; reconnecting");
                        that.connectToServer();
                    }
                });
            }

            // var url = get_appropriate_ws_url() + "/index_app";
            var url = this.get("url"); //"ws://localhost:9002";
            this.debug(`Connecting to: ${url}`);
            this.videosocket = new WebSocket(url);
            try {
                // Register callback functions on the WebSocket
                this.videosocket.binaryType = "arraybuffer";
                var that = this;
                this.videosocket.onopen = function(result){that.onConnected();};
                this.videosocket.onmessage = function(indata){that.onMessage(indata);};
                this.videosocket.onerror = function(obj){that.onError();};
                this.videosocket.onclose = function(obj){that.onDisconnected();};
            } catch (exception) {
                alert('Exception: ' + exception );
            }
        } else {
            alert("WebSockets NOT supported..");
            return;
        }

        //try
        //{
        //    this.video.play(); //for android devices
        //}
        //catch (exception)
        //{

        //}
    }

    /**
     * Draw information about the URL of the WebSocket server.
     *
     * @param {string} url URL of the WebSocket server.
     */
    _drawWebSocketURLInformation(url) {
        const websocketURLElement = document.getElementById('info-websocket-url');
        if (websocketURLElement !== null) {
            websocketURLElement.innerText = url;
        }
    }

    /**
     * Draw framerate-related information about the video stream in an informational container.
     *
     * @param {number} fps Framerate of the video.
     * @param {number} totalFramesReceived Total number of frames received.
     */
    _drawFrameInformation(fps = 0.0, totalFramesReceived = 0) {
        const fpsElement = document.getElementById('info-fps');
        if (fpsElement !== null) {
            fpsElement.innerText = fps.toFixed(2);
        }

        const framesReceivedElement = document.getElementById('info-frames-received');
        if (framesReceivedElement !== null) {
            framesReceivedElement.innerText = totalFramesReceived.toLocaleString();
        }
    }

    connected() {
        return this.videosocket != null && this.videosocket.readyState == 1; //CONNECTED
    }

    onMessage(indata) {
        // If the server sends any error message, display it on the console.
        if (typeof indata.data === "string") {
            this.debug(indata.data);
        }

        var measurementInterval = 100;
        if (this.frame === 0) {
            var tnow = performance.now();
            this.timeAtLastAvg = tnow;
        } else if(this.frame % measurementInterval === 0) {
            var tnow = performance.now();
            var dt = (tnow - this.timeAtLastAvg) / measurementInterval / 1000.;
            var avgFrameRate = 1./dt;
            this.debug(`At frame ${this.frame}; framerate: ${avgFrameRate} fps`);
            this.timeAtLastAvg = tnow;

            this._drawFrameInformation(avgFrameRate, this.frame);
        }
        this.trigger('frame', indata);
        ++this.frame;
    }

    onConnected() {
        var start_button = document.getElementById('overlaycontinue');
        start_button.hidden = true;
        this.frame = 0;
        this.trigger('connected');
    }

    onDisconnected() {
        var start_button = document.getElementById('overlaycontinue');
        start_button.hidden = false;
        this.trigger('disconnected');
        if (this.reconnecting) {
            this.reconnecting = false;
            this.connectToServer();
        }
    }

    onError() {
        this.trigger('error');
    }

    // If the user click on the button "disconnect", close the websocket to the
    // video streaming server.
    disconnect() {
        if (!this.connected()) {
            return;
        }
        // var command = {
        //     "command": "disconnect"
        // }
        // this.videosocket.send(JSON.stringify(command));
        this.videosocket.close();
    }

    reconnect() {
        if (this.connected()) {
            this.reconnecting = true;
            this.disconnect();
        } else {
            this.connectToServer();
        }
    }

    // Send a command to the video streaming server
    sendCommand(command) {
        if (this.connected()) {
            this.videosocket.send(JSON.stringify(command));
        }
    }
};

// Custom View. Renders the widget model.
class StreamClientView {

    constructor(model, el) {
        this.model = model;
        this.el = el;
        this.video = null;
        this.vframe = null;
        this.sourceBuffer = null;
        this.mediaSource = null;
        this.bufArray = null;
        this.arraySize = null;
        this.width = 512;
        this.height = 512;
        this.viewId = null;
        this.bodyMargin = 0;

        const bodyElement = document.querySelector('body');
        if (bodyElement !== null && 'margin' in bodyElement.style) {
            const parsedBodyMargin = parseInt(bodyElement.style.margin, 10);
            if (!isNaN(parsedBodyMargin) && parsedBodyMargin >= 0) {
                this.bodyMargin = parsedBodyMargin;
            }
        }

        this.buttonConnect =null;
        this.buttonDisconnect =null;
        this.pUrl = null;
    }

    debug(msg) {
        if (this.model.printToConsole) {
            console.log(`[view ${this.viewId}]: ${msg}`);
        }
    }

    initialize() {
        this.viewId = this.model.nviews;
        ++this.model.nviews;
        // this.debug("render (was:"+old_viewId+")");
    }

    render() {
        this.construct_ui();
        this.url_changed();

        var that = this;
        this.model.on('change:url', function(){ that.url_changed(); }, this);
        this.model.on('frame', function(indata){ that.onModelFrame(indata); });
        this.model.on('connected', function(){ that.onModelConnected(); });
        this.model.on('error', function(){ that.onModelError(); });
        this.model.on('disconnected', function(){ that.onModelDisconnected(); });

        //terrylin modify to auto conn
        this.model.reconnect();
        /*
        if (this.model.connected()) {
            // new view requires new connection; otherwise, streaming will not work.
            this.model.reconnect();
        }
        */
    }

    construct_ui() {
        this.stream_area = document.createElement('div');
        this.el.appendChild(this.stream_area);
        //this.el.parentNode.height = "512";

        var button_area = document.createElement('div');
        this.stream_area.appendChild(button_area);

        var that = this;

        this.buttonConnect = document.getElementById('overlaycontinue');
        this.buttonConnect.addEventListener('click', function(){ that.model.reconnect(); });

        this.buttonDisconnect = document.getElementById('stop');
        this.buttonDisconnect.addEventListener('click', function(){ that.model.disconnect(); });

        this.pUrl = document.createElement('label');
        this.pUrl.style.marginLeft = "5px";
        button_area.appendChild(this.pUrl);

        this.vframe = document.createElement('div');
        // this.vframe.setAttribute("tabindex", "0");
        this.vframe.width = this.width;
        this.vframe.height = this.height;

        // this.vframe.style.resize = 'both';
        // this.vframe.style.overflow = 'auto';
        // this.vframe.style.border = '2px solid';

        const throttleResize = this._throttle(e => this.resizeHandler(e), 25);
        window.addEventListener("resize", throttleResize);
        this.stream_area.appendChild(this.vframe);


        // Toggle the "info" panel displaying framerate and frame count information:
        const infoIcon = document.getElementById('info-icon');
        const infoPanel = document.getElementById('info-panel');
        if (infoIcon !== null && infoPanel !== null) {
            infoIcon.addEventListener('click', () => {
                const isInfoPanelHidden = infoPanel.classList.contains('d-none');
                if (isInfoPanelHidden) {
                    infoPanel.classList.remove('d-none');
                } else {
                    infoPanel.classList.add('d-none');
                }
            });
        }
    }

    url_changed() {
        this.pUrl.textContent = this.model.get("url");
        if (this.model.connected()) {
            this.model.reconnect();
        }
    }

    attach_listeners() {

    }

    onModelFrame(indata) {
        var arrayBuffer = indata.data;
        var bs = new Uint8Array( arrayBuffer );

        var nHeaderBytes = 0
        for (var i = 0; i < 2; ++i) {
            var b = bs[2-i-1];
            // console.log(b)
            nHeaderBytes = nHeaderBytes << 8;
            nHeaderBytes += b;
        }
        // console.log(`Expecting header of size ${nHeaderBytes}`);
        var header = bs.subarray(2, 2 + nHeaderBytes);
        // console.log(`header: ${header}`);
        bs = bs.subarray(2 + nHeaderBytes);
        // console.log(`data size: ${bs.length}`);
        this.bufArray.push(bs);
        this.arraySize += bs.length;
        // this.debug("entering decodeAndDisplay");

        if (this.sourceBuffer != null && !this.sourceBuffer.updating) {
            if (this.sourceBuffer.buffered.length > 0) {
                var begin = this.sourceBuffer.buffered.start(0);
                var end = this.sourceBuffer.buffered.end(this.sourceBuffer.buffered.length - 1);
                var currentTime = this.video.currentTime;
                var lag = end - currentTime;

                function r2(f) {
                    return Math.round((f + Number.EPSILON) * 100.) / 100.
                }

                if (lag > 0.1) {
                    this.video.currentTime = end;
                    // this.video.playbackRate = 1.1; //2.0 + lag / 0.01;
                    // this.debug(`-^${'-'.repeat(Math.round(lag * 10.))}] Playback lags behind stream: currentTime=${r2(currentTime)}; end=${r2(end)} ( dt = ${r2(lag)} ) -> pbr:=${r2(this.video.playbackRate)}`);
                } else if (lag < 0.) {
                    this.video.currentTime = end;
                    // this.video.playbackRate = 1.1;
                    // this.debug(`--]${' '.repeat(Math.round(-lag * 10.))}^ Playback is ahead of stream: currentTime=${r2(currentTime)}; end=${r2(end)} ( dt = ${r2(end-currentTime)} )`);
                }

                // trim buffer to one second
                if (end - begin > 6.0) {
                    this.sourceBuffer.remove(begin, end - 5.0);
                }
            }
        }

        if (this.sourceBuffer != null && !this.sourceBuffer.updating) {
            var streamBuffer = new Uint8Array(this.arraySize);
            var i = 0;
            while (this.bufArray.length > 0) {
                var b = this.bufArray.shift();
                streamBuffer.set(b, i);
                i += b.length
            }
            this.arraySize = 0;
            // Add the received data to the source buffer
            try {
                this.sourceBuffer.appendBuffer(streamBuffer);
                // var logmsg = 'Frame: ' + this.model.frame;
                // var tnow = performance.now();
                // if (this.timeAtLastFrame >= 0)
                // {
                //     var dt = Math.round(tnow - this.timeAtLastFrame);
                //     logmsg += '; dt = ' + dt + 'ms';
                //     logmsg += '\n' + Array(Math.round(dt/10)).join('*');
                // }
                // this.timeAtLastFrame = tnow;
            } catch (err) {
                console.error(err);
                this.debug("failed to append buffer; reconnecting.");
                this.model.reconnect();
            }

            // this.debug(logmsg);
        }

        if (this.video.paused) {
            this.debug("Playback was paused; resuming");
            this.video.play();
        }
    }

    // The WebSocket connection to the video streaming server has been established.
    // We are now ready to play the video stream.
    onModelConnected(result) {
        this.debug("Connected")
        if (this.video != null) {
            this.debug("video already exists; skipping");
            return;
        }
        this.buttonDisconnect.disabled = false;
        this.buttonDisconnect.hidden = false;

        this.video = document.createElement('video');

        var that = this;
        this.video.addEventListener('mousemove',  function(event){that.mouseMoveHandler(event);});
        this.video.addEventListener('mouseout',   function(event){that.mouseOutHandler(event);});
        this.video.addEventListener('mousedown',  function(event){that.mouseDownHandler(event); });
        this.video.addEventListener('contextmenu',function(event){that.contextMenuHandler(event); });
        this.video.addEventListener('mouseup',    function(event){that.mouseUpHandler(event);});
        this.video.addEventListener('mousewheel', function(event){that.mouseWheelHandler(event);});

        //this.video.width = "auto";
        //this.video.height = "auto";
        this.video.width = this.width;
        this.video.height = this.height;
        this.video.autoplay = false;
        while (this.vframe.children.length > 0) {
            this.vframe.removeChild(this.vframe.children[0]);
        }
        this.vframe.appendChild(this.video);
        this.video.addEventListener("resize", function(event){that.videoResizeHandler(event);});
        this.video.setAttribute("tabindex", "0");

        var that = this;
        var keyDownFn = function(event){that.keyDownHandler(event);};
        var keyUpFn = function(event){that.keyUpHandler(event);};
        var keyPressFn = function(event){that.keyPressHandler(event);};

        let addKeyListeners = function (e) {
            that.debug("add keyboard listeners");
            document.addEventListener('keydown', keyDownFn, true);
            document.addEventListener('keyup', keyUpFn, true);
            document.addEventListener('keypress', keyPressFn, true);
        };

        let removeKeyListeners = function(e) {
            that.debug("remove keyboard listeners");
            document.removeEventListener('keydown', keyDownFn, true);
            document.removeEventListener('keyup', keyUpFn, true);
            document.removeEventListener('keypress', keyPressFn, true);
        };

        var pasteFn = function(event){that.pasteHandler(event)};
        document.addEventListener('paste', pasteFn, true);

        this.video.addEventListener('focusin', addKeyListeners, false);
        this.video.addEventListener('focusout', removeKeyListeners, false);

        this.bufArray = new Array();
        this.arraySize = 0;

        this.mediaSource = new MediaSource();
        this.video.src = window.URL.createObjectURL(this.mediaSource);
        var that = this;

        //var mimecodec = 'video/mp4;codecs="avc1.64001E"';// 'video/mp4; codecs="avc1.42E01E"';
        //var mimecodec = 'video/mp4; codecs="avc1.42E01E"';
        // 0x64=100 "High Profile"; 0x00 No constraints; 0x1F=31 "Level 3.1"
        var mimecodec = 'video/mp4; codecs="avc1.64001F"';

        this.mediaSource.addEventListener('sourceopen', function () {
            // that.debug(" sourceOpen...");
            // get a source buffer to contain video data this we'll receive from the server
            // that.debug(that.video.canPlayType(mimecodec));
            that.sourceBuffer = that.mediaSource.addSourceBuffer(mimecodec);

            // // if the view is created after streaming has already begun (i.e., as a second view), replay the first frame (init segment).
            // if(that.model.firstFrame != null)
            // {
            //     that.onModelFrame(that.model.firstFrame);
            // }

        });

        this.mediaSource.addEventListener('sourceclose', function () {
            // that.debug(" sourceClose...");
            // get a source buffer to contain video data this we'll receive from the server
            // that.debug(that.video.canPlayType(mimecodec));
            that.sourceBuffer = null;
        });


        this.mediaSource.addEventListener('webkitsourceopen', function () {
            that.debug(" webkitsourceopen...");
            // get a source buffer to contain video data this we'll receive from the server
            that.sourceBuffer = that.mediaSource.addSourceBuffer(mimecodec);
            //that.sourceBuffer = that.mediaSource.addSourceBuffer('video/mp4;codecs="avc1.64001E"');
        });

        this.resizeHandler();
        this.fpsHandler();

        var playPromise = this.video.play();
        if (playPromise !== undefined) {
            this.debug("Got play promise; waiting for fulfilment...");
            var that = this;
            playPromise.then(function() {
                that.debug("Play promise fulfilled! Starting playback.");
                that.vframe.width = that.width;
                that.vframe.height = that.height;

                that.video.currentTime = 0;
            }).catch(function(error) {
                that.debug("Failed to start playback: "+error);
            });
        }
    }

    // If there is an error on the WebSocket, reset the buttons properly.
    onModelError(obj) {
        this.debug('error: ' + obj);
    }

    // If there the WebSocket is closed, reset the buttons properly.
    onModelDisconnected(obj) {
        this.debug("disconnected");
        this.buttonConnect.disabled = false;
        this.buttonDisconnect.disabled = true;
        this.buttonDisconnect.hidden = true;
        this.mediaSource = null;
        this.sourceBuffer = null;
        if (this.video != null) {
            this.vframe.removeChild(this.video);
        }
        this.video = null;
    }

    // The mouse has moved, we send command "mouse_move" to the video streaming server.
    mouseMoveHandler(event) {
        //this.debug("mousemove "+event.button);

        var xy = this.mouseToVideo(event.offsetX, event.offsetY);
        var x = xy[0];
        var y = xy[1];

        var command = {
            "command": "mouse_move",
            "mouse_move" : {
                "button": event.button,
                //"mouse_x": event.clientX,
                //"mouse_y": event.clientY,
                "x": x,
                "y": y,
            },
        };
        this.model.sendCommand(command);
        //this.debug(command);
    }

    // The mouse has moved out of the window image, this is equivalent to an event
    // in which the user releases the mouse button
    mouseOutHandler(event) {
    }

    mouseToVideo(x, y) {
        var scale = this.video.videoWidth / this.video.offsetWidth;
        var result = [ x * scale, y * scale ];
        return result;
    }

    // convert key event to json object
    getMouseEventJson(mouseevent) {
        var xy = this.mouseToVideo(mouseevent.offsetX, mouseevent.offsetY);
        var x = xy[0];
        var y = xy[1];

        var mouse_json = {
            "button":   mouseevent.button,
            "shiftKey": mouseevent.shiftKey,
            "ctrlKey":  mouseevent.ctrlKey,
            "altKey":   mouseevent.altKey,
            "metaKey":  mouseevent.metaKey,
            "x":        x,
            "y":        y,
        };

        return mouse_json;
    }

    // The user has pressed a mouse button, we send command "mouse_down" to
    // the video streaming server.
    mouseDownHandler(event) {
        this.debug("mousedown "+event.button);
        event.preventDefault();
        event.stopPropagation();
        this.video.focus({ preventScroll: true });

        var command = {
            "command" : "mouse_down",
            "mouse_down" : this.getMouseEventJson(event),
        };
        this.model.sendCommand(command);
        // this.vframe.requestPointerLock();
        return false;
    }

    // The user has released a mouse button, we send command "mouse_up" to the
    // video streaming server.
    mouseUpHandler(event) {
        this.debug("mouseup "+event.button);
        event.preventDefault();
        event.stopPropagation();
        this.video.focus({ preventScroll: true });
        //this.video.focus();
        var command = {
            "command" : "mouse_up",
            "mouse_up": this.getMouseEventJson(event),
        };
        this.model.sendCommand(command);
        // document.exitPointerLock();
        return false;
    }

    // mouse wheel input
    mouseWheelHandler(event) {
        var delta = 0;
        if (event.wheelDelta >= 120) {
            delta = 1;
        } else if (event.wheelDelta <= -120) {
            delta = -1;
        }
        var event_json = this.getMouseEventJson(event);
        event_json.delta = delta
        var command = {
            "command": "mouse_wheel",
            "mouse_wheel": event_json,
        };
        this.model.sendCommand(command);
        event.preventDefault();
        event.stopPropagation();
        this.video.focus({ preventScroll: true });
    }

    // The user has pressed a mouse button, we send command "mouse_down" to
    // the video streaming server.
    contextMenuHandler(event) {
        event.preventDefault();
        return false;
    }


    // convert key event to json object
    getKeyEventJson(keyevent) {
        var key_json = {
            "key":      keyevent.key,
            "keyCode":  keyevent.keyCode,
            "which":    keyevent.which,
            "charCode": keyevent.charCode,
            "char":     String.fromCharCode(keyevent.which),
            "shiftKey": keyevent.shiftKey,
            "ctrlKey":  keyevent.ctrlKey,
            "altKey":   keyevent.altKey,
            "metaKey":  keyevent.metaKey,
        };

        return key_json;
    }

    // A key has been pressed (special keys)
    keyDownHandler(event) {
        var command = {
            "command": "key_down",
            "key_down" : this.getKeyEventJson(event),
        };
        command.key_down.x = 0;
        command.key_down.y = 0;
        this.model.sendCommand(command);
        // this.debug(command);
        event.stopPropagation();
        event.preventDefault();
    }

    // A key has been pressed (char keys)
    keyPressHandler(event) {
        // this.debug(event);
        var command = {
            "command": "key_press",
            "key_press" : this.getKeyEventJson(event),
        };
        command.key_press.x = 0;
        command.key_press.y = 0;
        this.model.sendCommand(command);
        // this.debug(command);
        event.stopPropagation();
        event.preventDefault();
    }

    // A key has been released (for special keys)
    keyUpHandler(event) {
        var command = {
            "command": "key_up",
            "key_up" : this.getKeyEventJson(event),
        };
        command.key_up.x = 0;
        command.key_up.y = 0;
        this.model.sendCommand(command);
        // this.debug(command);
        event.stopPropagation();
    }

    // clipboard paste
    pasteHandler(event) {
        var cbData = event.clipboardData;
        var text = cbData.getData('Text');

        var command = {
            "command": "paste",
            "paste": {
                "text" : text,
            },
        };
        this.debug(JSON.stringify(command));
        this.model.sendCommand(command);
    }

    // window / element resize
    resizeHandler() {
        let dpr = window.devicePixelRatio;
        // var element_w = Math.round(this.vframe.scrollWidth * dpr);
        // var element_h = Math.round(this.vframe.scrollHeight * dpr);
        var element_w = Math.round(window.innerWidth * dpr);
        var element_h = Math.round(window.innerHeight * dpr);

        var minWidth = 400;
        var minHeight = 300;

        if (element_w < minWidth) {
            element_w = minWidth;
        }
        if (element_h < minHeight) {
            element_h = minHeight;
        }

        this.debug(`resize: ${element_w}x${element_h}`);
        var command = {
            "command": "video_resize",
            "video_resize" : {
                "video_width":  element_w,
                "video_height": element_h,
            },
        };
        this.debug(JSON.stringify(command));
        this.model.sendCommand(command);
        // this.debug("video_width: " + video_w + ", video_height: " + video_h);

        fetch('/streaming/resize-stream', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                width: element_w - this.bodyMargin * dpr,
                height: element_h - this.bodyMargin * dpr,
            }),
        });

        // Restart the video player here
        // sourceBuffer.remove(0, 10000000);

        // var element = document.getElementById('video');
        // var positionInfo = element.getBoundingClientRect();
        // var height = positionInfo.height;
        // var width = positionInfo.width;
        // this.debug("width: " + width + ", height: " + height);
    }

    async fpsHandler() {
        const fps = await this.model.getFPS();
        const command = {
            'command': 'set_fps',
            'set_fps': {
                'fps': Math.round(fps),
            },
        };
        this.debug(JSON.stringify(command));
        this.model.sendCommand(command);
    }

    videoResizeHandler() {
        let dpr = window.devicePixelRatio;
        let w = this.video.videoWidth / dpr;
        let h = this.video.videoHeight / dpr;
        if (w && h) {
            this.debug(`video resize: ${w}x${h}`);
            this.vframe.style.width = w;
            this.vframe.style.height = h;
            this.video.width = w;
            this.video.height = h;
            this.video.style.width = w;
            this.video.style.height = h;
        }
    }

    /**
     * Throttle the given function callback to avoid executing it at too frequent intervals. This is especially
     * important for actions involving user input, such as dynamic screen resizing, which can cause events to fire at
     * great frequency, and cause issues with async or serialized events.
     *
     * @param {Function} callback Callback function to throttle.
     * @param {number} delay Delay between successive calls to the given callback function (in milliseconds).
     * @returns {Function} A higher-order function to call on behalf of the given callback in order to throttle its
     * execution.
     */
    _throttle(callback, delay = 100) {
        let isInProgress = false;
        return (...args) => {
            if (isInProgress) {
                return;
            }
            isInProgress = true;
            callback(...args);
            setTimeout(() => {
                isInProgress = false;
            }, delay);
        }
    }
};

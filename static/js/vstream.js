// Custom View. Renders the widget model.
class VStream {

    constructor(url,el) {
        this.url = url;
        this.el = el;

        this.sourceBuffer = {};
        //this.videosocket = {};
        this.mouseDown = [false, false, false];
        this.bufArray = new Array();
        this.arraySize = 0;
        this.frame = -1;
        this.timeAtLastFrame = -1;
        this.mostRecentFrame = {};
        this.mediaSource = {};
        this.video = document.createElement('video');
        this.vframe = {};
        this.mouse_x = {};
        this.mouse_y = {};
        this.width = 512;
        this.height = 512;
    }

    render() {
        //console.log("Rendering VStream UI...");

        this.mediaSource = new MediaSource();

        this.construct_ui();
        this.attach_listeners();
    }

    construct_ui () {
        this.stream_area = document.createElement('div');
        this.stream_area.id="stream_area";
        this.el.appendChild(this.stream_area);
        //this.el.parentNode.height = "512";

        var button_area = document.createElement('div');
        this.stream_area.appendChild(button_area);

        var that = this;

        var cbutton = document.createElement('input');
        cbutton.id = 'connect';
        cbutton.type = 'button';
        cbutton.value = 'Connect';
        cbutton.addEventListener('click', function(){that.connectToServer();});
        button_area.appendChild(cbutton);

        var dbutton = document.createElement('input');
        dbutton.id = 'disconnect';
        dbutton.type = 'button';
        dbutton.value = 'Disconnect';
        dbutton.addEventListener('click', function(){that.disconnect();});
        button_area.appendChild(dbutton);
        this.stream_area.appendChild(document.createElement('p'));

        var urlinput = document.createElement('input');
        urlinput.id = 'urlinput';
        urlinput.type = 'url';
        urlinput.value = this.url;
        urlinput.addEventListener('change', function(event){that.url = event.target.value;});
        this.stream_area.append(urlinput);
        this.stream_area.appendChild(document.createElement('p'));

        this.vframe = document.createElement('div');
        this.vframe.id = "videoframe";
        this.vframe.setAttribute("tabindex","0");
        this.vframe.width = this.width;
        this.vframe.height = this.height;
        this.vframe.addEventListener('mousemove',  function(event){that.mouseMoveHandler(event);});
        this.vframe.addEventListener('mouseout',   function(event){that.mouseOutHandler(event);});
        this.vframe.addEventListener('mousedown',  function(event){that.mouseDownHandler(event); });
        this.vframe.addEventListener('contextmenu',function(event){that.contextMenuHandler(event); });
        this.vframe.addEventListener('mouseup',    function(event){that.mouseUpHandler(event);});
        this.vframe.addEventListener('mousewheel', function(event){that.mouseWheelHandler(event);});
        this.vframe.addEventListener("keydown",    function(event){that.keyDownHandler(event);});
        this.vframe.addEventListener("keyup",      function(event){that.keyUpHandler(event);});
        this.vframe.addEventListener("keypress",   function(event){that.keyPressHandler(event);});
        window.addEventListener("resize",     function(event){that.resizeHandler(event);});
        this.stream_area.appendChild(this.vframe);

        this.video.id = "video";
        //this.video.width = "auto";
        //this.video.height = "auto";
        this.video.width = this.width;
        this.video.height = this.height;
        this.video.autoplay = false;
        this.video.src = window.URL.createObjectURL(this.mediaSource);
        this.vframe.appendChild(this.video);

    }

    attach_listeners (){
        //'this' pointer does not point to this object when invoked as a callback
        //https://stackoverflow.com/a/134149
        //because of this peculiarity, we cannot use object methods as callbacks
        //if they need access to 'this'.
        var that = this;

        //var mimecodec = 'video/mp4;codecs="avc1.64001E"';// 'video/mp4; codecs="avc1.42E01E"';
        //var mimecodec = 'video/mp4; codecs="avc1.42E01E"';
        // 0x64=100 "High Profile"; 0x00 No constraints; 0x1F=31 "Level 3.1"
        var mimecodec = 'video/mp4; codecs="avc1.64001F"';

        this.mediaSource.addEventListener('sourceopen', function() {
            //console.log("sourceOpen...");
            // get a source buffer to contain video data this we'll receive from the server
            //console.log (that.video.canPlayType(mimecodec));
            that.sourceBuffer = that.mediaSource.addSourceBuffer(mimecodec);
        });

        this.mediaSource.addEventListener('webkitsourceopen', function() {
            //console.log("webkitsourceopen...");
            // get a source buffer to contain video data this we'll receive from the server
            that.sourceBuffer = that.mediaSource.addSourceBuffer(mimecodec);
            //that.sourceBuffer = that.mediaSource.addSourceBuffer('video/mp4;codecs="avc1.64001E"');
        });
    }

    set_url(url) {
        this.url = url;
        this.el.textContent = this.url;
    }

    connectToServer (){
        if( "WebSocket" in window )
        {
            // var url = get_appropriate_ws_url() + "/index_app";
            var url = this.url; //"ws://localhost:9002";
            console.log("Connecting to: "+url);
            this.videosocket = new WebSocket( url );
            try
            {
                // Register callback functions on the WebSocket
                this.videosocket.binaryType = "arraybuffer";
                var that = this;
                this.videosocket.onopen = function(result){that.onVideoConnectedCallback(result);};
                this.videosocket.onmessage = function(indata){that.decodeAndDisplayVideo(indata);};
                this.videosocket.onerror = function(obj){that.onerror(obj);};
                this.videosocket.onclose = function(obj){that.onVideoClose(obj)};
            }
            catch( exception )
            {
                alert('Exception: ' + exception );
            }
        }
        else
        {
            alert("WebSockets NOT supported..");
            return;
        }
    }

    // If the user click on the button "disconnect", close the websocket to the
    // video streaming server.
    disconnect  (){
        if (this.video.connected)
        {
            var command = {
                "command": "disconnect"
            }
            this.videosocket.send(JSON.stringify(command));
        }

        this.video.connected = false;
        this.videosocket.close();

        document.getElementById('connect').   disabled = true;
        document.getElementById('disconnect').disabled = false;
    }

    decodeAndDisplayVideo ( indata ){

        // If the server sends any error message, display it on the console.
        if (typeof indata.data === "string")
            console.log(indata.data);

        var arrayBuffer = indata.data;
        var bs = new Uint8Array( arrayBuffer );
        this.bufArray.push(bs);
        this.arraySize += bs.length;

        if (!this.sourceBuffer.updating)
        {
            var streamBuffer = new Uint8Array(this.arraySize);
            var i=0;
            var nchunks=0;
            while (this.bufArray.length > 0)
            {
                var b = this.bufArray.shift();
                streamBuffer.set(b, i);
                i += b.length;
                nchunks+=1;
            }
            this.arraySize = 0;
            // Add the received data to the source buffer
            this.sourceBuffer.appendBuffer(streamBuffer);
            var tnow = performance.now();
            var logmsg = 'Frame: ' + this.frame+ '(in '+nchunks+' chunks)';
            if (this.timeAtLastFrame >= 0)
            {
                var dt = Math.round(tnow - this.timeAtLastFrame);
                logmsg += '; dt = ' + dt + 'ms (' + 1000/dt + ' fps)' ;
                logmsg += '\n' + Array(Math.round(dt/10)).join('*');
            }
            this.timeAtLastFrame = tnow;

            document.getElementById('logarea').value = logmsg;
            //console.log(logmsg);
        }

        ++this.frame;
        if (this.video.paused)
        {
            this.video.play();
        }
        //TODO: Figure out a smarter way to manage the frame size (i.e. cache it?)
        this.video.width = this.video.videoWidth;
        this.video.height = this.video.videoHeight;
    }


    start (){
        document.getElementById('connect').   disabled = true;
        document.getElementById('disconnect').disabled = false;
    }

    // Send a command to the video streaming server
    sendCommand (command){
        if (this.video.connected)
        {
            var message = {
                "command": command,
            }
            this.videosocket.send(JSON.stringify(message));
        }
    }

    // The WebSocket connection to the video streaming server has been established.
    // We are now ready to play the video stream.
    onVideoConnectedCallback ( result ){
        console.log("Connected!");

        this.resizeHandler();

        // https://stackoverflow.com/a/40238567
        var playPromise = this.video.play();
        if ( playPromise !== undefined) {
            console.log("Got play promise; waiting for fulfilment...");
            var that = this;
            playPromise.then(function() {
                console.log("Play promise fulfilled! Starting playback.");
                that.video.connected = true;
                that.vframe.width = that.width;
                that.vframe.height = that.height;
                document.getElementById('connect').   disabled = true;
                document.getElementById('disconnect').disabled = false;

                that.start();
                that.video.currentTime = 0;
            }).catch(function(error) {
                console.log("Failed to start playback: "+error);
            });
        }

    }

    // If there is an error on the WebSocket, reset the buttons properly.
    onerror ( obj ){
        console.log(obj)
        this.video.connected = false;
        document.getElementById('connect').   disabled = true;
        document.getElementById('disconnect').disabled = false;
    }

    // If there the WebSocket is closed, reset the buttons properly.
    onVideoClose ( obj ){
        this.video.connected = false;
        document.getElementById('connect').   disabled = false;
        document.getElementById('disconnect').disabled = true;

        this.sourceBuffer.remove(0, 10000000);
    }

    // The mouse has moved, we send command "mouse_move" to the video streaming server.
    mouseMoveHandler (event){
        //console.log("mousemove "+event.button);
        this.mouse_x = event.offsetX;
        this.mouse_y = event.offsetY;
        if (this.video.connected)// && this.mouseDown.some( function(val){ return val } ))
        {
            //this.mouse_x += event.movementX;
            //this.mouse_y += event.movementY;
            var command = {
                "command": "mouse_move",
                "mouse_move" : {
                    "button": event.button,
                    //"mouse_x": event.clientX,
                    //"mouse_y": event.clientY,
                    "x": this.mouse_x,
                    "y": this.mouse_y
                }
            };
            this.videosocket.send(JSON.stringify(command));
            //console.log(command);
        }
        else
        {
            this.mouse_x = event.offsetX;
            this.mouse_y = event.offsetY;
        }
    }

    // The mouse has moved out of the window image, this is equivalent to an event
    // in which the user releases the mouse button
    mouseOutHandler (event){
        this.mouseDown[event.button] = false;
    }

    // The user has pressed a mouse button, we send command "mouse_down" to
    // the video streaming server.
    mouseDownHandler (event){
        //console.log("mousedown "+event.button);
        //event.preventDefault();
        //event.stopPropagation();
        //this.video.focus();
        this.mouseDown[event.button] = true;
        this.mouse_x = event.offsetY;
        this.mouse_y = event.offsetX;
        if (this.video.connected)
        {
            var command = {
                "command" : "mouse_down",
                "mouse_down" : {
                    "button": event.button,
                    //"mouse_x": event.clientX,
                    //"mouse_y": event.clientY,
                    "x": this.mouse_x,
                    "y": this.mouse_y
                }
            };
            this.videosocket.send(JSON.stringify(command));
            //this.vframe.requestPointerLock();
            return false;
        }
    }

    // The user has released a mouse button, we send command "mouse_up" to the
    // video streaming server.
    mouseUpHandler (event){
        //console.log("mouseup "+event.button);
        event.preventDefault();
        //event.stopPropagation();
        //this.video.focus();
        this.mouseDown[event.button] = false;
        if (this.video.connected)
        {
            var command = {
                "command" : "mouse_up",
                "mouse_up": {
                    "button": event.button,
                    //"mouse_x": event.clientX,
                    //"mouse_y": event.clientY,
                    "x": this.mouse_x,
                    "y": this.mouse_y
                }
            };
            this.videosocket.send(JSON.stringify(command));
            //document.exitPointerLock();
            return false;
        }
    }

    // mouse wheel input
    mouseWheelHandler (event){
        var delta = 0;
        if (event.wheelDelta >= 120)
        {
            delta = 1;
        }
        else if (event.wheelDelta <= -120)
        {
            delta = -1;
        }

        if (this.video.connected)
        {
            var command = {
                "command": "mouse_wheel",
                "mouse_wheel": {
                    //"mouse_x": event.clientX,
                    //"mouse_y": event.clientY,
                    "mouse_x": event.offsetX,
                    "mouse_y": event.offsetY,
                    "delta": delta
                }
            };
            this.videosocket.send(JSON.stringify(command));
        }
    }

    // The user has pressed a mouse button, we send command "mouse_down" to
    // the video streaming server.
    contextMenuHandler (event){
        event.preventDefault();
        return(false);
    }


    // convert key event to json object
    getKeyEventJson (keyevent){
        var key_json = {
            "key":      keyevent.key,
            "keyCode":  keyevent.keyCode,
            "which":    keyevent.which,
            "charCode": keyevent.charCode,
            "char":     String.fromCharCode(keyevent.which),
            "shiftKey": keyevent.shiftKey,
            "ctrlKey":  keyevent.ctrlKey,
            "altKey":   keyevent.altKey,
            "metaKey":  keyevent.metaKey
        };

        return key_json;
    }

    // A key has been pressed (special keys)
    keyDownHandler (event){
        if (this.video.connected)
        {
            var command = {
                "command": "key_down",
                "key_down" : this.getKeyEventJson(event)
            };
            command.key_down.x = this.mouse_x;
            command.key_down.y = this.mouse_y;
            this.videosocket.send(JSON.stringify(command));
            //console.log(command);
            event.stopPropagation();
        }
    }

    // A key has been pressed (char keys)
    keyPressHandler (event){
        //console.log(event);
        if (this.video.connected)
        {
            var command = {
                "command": "key_press",
                "key_press" : this.getKeyEventJson(event)
            };
            command.key_press.x = this.mouse_x;
            command.key_press.y = this.mouse_y;
            this.videosocket.send(JSON.stringify(command));
            //console.log(command);
            event.stopPropagation();
        }
    }

    // A key has been released (for special keys)
    keyUpHandler (event){
        if (this.video.connected)
        {
            var command = {
                "command": "key_up",
                "key_up" : this.getKeyEventJson(event)
            };
            command.key_up.x = this.mouse_x;
            command.key_up.y = this.mouse_y;
            this.videosocket.send(JSON.stringify(command));
            //console.log(command);
            event.stopPropagation();
        }
    }

    resizeHandler (){
        var element_w = this.vframe.scrollWidth;
        var element_h = this.vframe.scrollHeight;
        if (element_w <= 0)
        {
            element_w = 1;
        }
        if (element_h <= 0)
        {
            element_h = 1;
        }
        //console.log("resize: "+element_w+" "+element_h);
        var command = {
            "command": "video_resize",
            "video_resize" : {
                "video_width" :  element_w,
                "video_height" : element_h
            }
        };
        if(this.videosocket)
            this.videosocket.send(JSON.stringify(command));
        //console.log(JSON.stringify(command));
        // console.log("video_width: " + video_w + ", video_height: " + video_h);

        // Restart the video player here
        // sourceBuffer.remove(0, 10000000);

        // var element = document.getElementById('video');
        // var positionInfo = element.getBoundingClientRect();
        // var height = positionInfo.height;
        // var width = positionInfo.width;
        // console.log("width: " + width + ", height: " + height);
    }
};


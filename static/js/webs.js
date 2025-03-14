let web_icon = {
    success: 
    '<span class="material-symbols-outlined">task_alt</span>', 
    danger: 
    '<span class="material-symbols-outlined">error</span>', 
    warning: 
    '<span class="material-symbols-outlined">warning</span>', 
    info: 
    '<span class="material-symbols-outlined">info</span>', 
}; 

// 创建一个新的renderer
const renderer = new marked.Renderer();

// 自定义 `<img>` 标签的渲染方法
renderer.image = function(href, title, text) {
    // 确保 href.raw 是一个字符串，且进行适当处理
    if (typeof href.raw !== 'string') {
        console.error('Invalid href:', href);
        return ''; // 如果 href 无效，返回空字符串
    }
    // 使用 URLSearchParams 获取 `image_name` 参数
    const urlParams = new URLSearchParams(href.raw.split('?')[1]); // 获取查询部分
    // 获取 `image_name` 参数
    const imageNameWithParam = urlParams.get('image_name'); // 获取 image_name 参数

    // 从 `image_name` 提取文件名部分
    const imageName = imageNameWithParam.split('/').pop(); // 获取文件名部分
    const doc_id = imageName.split('_')[1]
    if(isNaN(doc_id)){
        return ""
    }
    // 基于原始文件名生成新链接
    const apiUrl = `${window.location.origin}/kdb/get_image?image_name=${imageName}&doc_id=${doc_id}&kdb_id=${new URLSearchParams(window.location.search).get('kdb_id')}&session_id=${session_id}&resize=False`;

    // 为 `<img>` 标签添加 `onclick` 事件
    return `<img src="${apiUrl}" alt="" class="chat-image" onclick="showModal('${apiUrl}')">`;
};

var grapg_suffix = 0
let messageContainer = null;
let currentMessageWrapper = null;
let currentParagraph = null;
let FileContainer = null;
let currentText = "";
let lastRole='user'
const showToast = ( 
    message = "Sample Message", 
    toastType = "info", 
    duration = 5000) => { 
    if ( 
        !Object.keys(web_icon).includes(toastType))
        toastType = "info"; 
  
    let box = document.createElement("div"); 
    box.classList.add( 
        "toast", `toast-${toastType}`); 
    box.innerHTML = ` <div class="toast-content-wrapper"> 
                      <div class="toast-icon"> 
                      ${web_icon[toastType]}
                      </div> 
                      <div class="toast-message">${message}</div> 
                      <div class="toast-progress"></div> 
                      </div>`; 
    duration = duration || 5000; 
    box.querySelector(".toast-progress").style.animationDuration = 
            `${duration / 1000}s`; 
  
    let toastAlready =  
        document.body.querySelector(".toast"); 
    if (toastAlready) { 
        toastAlready.remove(); 
    } 
  
    document.body.appendChild(box)}; 

var TTS_ENABLED=true;
var USING_AU_WEBS=true;
var TTS_URL = 'http://13902254981.tpddns.cn:8087/api/generate';
var AGENT_URL = `http://192.168.1.14:8014/`;
var domain = window.location.host;
var pos = window.location.href.length - window.location.pathname.length
var base_url = window.location.href.substring(0, pos);
parts = window.location.pathname.split("/")
if (parts.length > 3){
    base_url += "/" + parts[1]
}
console.log(base_url)
TTS_URL = `${window.location.protocol}//${domain}/audio`;

var mode = 'faq';
function set_mode(value){
    console.log("set mode to:" + value);
    //showToast("mode set to"+value,"info",5000); 
    mode = value;
    const uploadFileBtn = document.getElementById("uploadfile")
    if(uploadFileBtn){
        if(mode === "faq" || mode === "graphrag"){
            uploadFileBtn.classList.add('disabled');
            uploadFileBtn.disabled = true;
        }else{
            uploadFileBtn.classList.remove('disabled');
            uploadFileBtn.disabled = false;
        }
    }
}
function setup_tts(value){
    TTS_ENABLED = value;
}

var current_codes = "";
var mtype='ws';
var socket;
var socket_status='init';

var kdb_id = '';
function set_kdb_id(kid){
    kdb_id = kid;
}

var codeBlockCB=null;

function setCodeBlockCB(cb){
    codeBlockCB = cb;
}

var prompt_name = '';
function set_prompt_name(pname){
    prompt_name = pname;
}
var currentLanguage ='';

function set_language() {
    // 发送获取请求
    fetch(`${window.location.protocol}//${domain}/get_current_language`, {
        method: 'POST',
        credentials: 'include', // 发送 cookie
        headers: {
            'Content-Type': 'application/json' // 设置请求体的内容类型为 JSON
        }
    })
    .then(response => response.json())
    .then(result => {
        currentLanguage = result.language;
        console.log("获得到的语言:",currentLanguage);
    })
}

function init_socket(){
    var ws_url = `ws://${domain}/ws`
    if (window.location.protocol.endsWith('https:'))
        ws_url = `wss://${domain}/ws`;
    socket = new WebSocket(ws_url);
    socket.addEventListener('open', function (event) {
        console.log('Connected to WS Server')
        socket_status='connected';
        cmd = {"mode":"cmd", "current_language": currentLanguage, "message":{"session_id":session_id}};
        text = JSON.stringify(cmd)
        socket.send(text)
    });

    socket.addEventListener('message', on_message);

    socket.addEventListener('close', function (event) {
        console.log('Disconnected from WS Server');
        socket_status='closed';
    });
}

function send_cmd(message){
        var obj = {message:message, mode:'cmd'};
        text = JSON.stringify(obj)
        socket.send(text);
}
function init_audio_socket(){
    var ws_url = `ws://${domain}/audio`
    if (window.location.protocol.endsWith('https:'))
        ws_url = `wss://${domain}/audio`;
    ausocket = new WebSocket(ws_url);
    ausocket.addEventListener('open', function (event) {
        console.log('Connected to audio Server');
        cmd = {"mode":"cmd", "message":{"session_id":session_id}};
        text = JSON.stringify(cmd)
        ausocket.send(text)
    });

    ausocket.addEventListener('message', on_audio);

    ausocket.addEventListener('close', function (event) {
        console.log('Disconnected from audio Server');
        init_audio_socket();
    });
}
function on_audio(event){
    console.log("receive audio event")
    console.log(event)
    var reader = new FileReader();
    reader.onload = function(){
        var audioData = reader.result
        console.log(audioData);
        audioContext.decodeAudioData(audioData, function(buffer) {
            audioQueue.push(buffer);
            if (!isPlaying) {
                playNextAudio();
            }
        }, function(e) {
            console.log("Error with decoding audio data" + e.err);
        });
    }
    reader.readAsArrayBuffer(event.data);
}

var token = (Math.random ()* Math.random ()).toString();
function init_event(){
        // 创建一个新的 EventSource 实例来连接到服务器的流端点
    const eventSource = new EventSource(base_url+'/stream?token='+token);

    // 监听来自服务器的消息
    eventSource.onmessage = on_message;

    // 监听错误事件
    eventSource.onerror = function(error) {
        console.error('EventSource failed:', error);
        eventSource.close(); // 关闭连接
        setTimeout(init_event, 1000);
    };
}

function sendMessageToServer(obj) {
    fetch(base_url+'/streamrequest', {
        method: 'POST', // 或 'GET' 根据你的 API 设计
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(obj)
    })
    .then(response => response.json())
    .then(data => console.log('Success:', data))
    .catch((error) => console.error('Error:', error));
}

function sendMessage(data){
    // 创建一个 XMLHttpRequest 对象
    var xhr = new XMLHttpRequest();

    // 配置请求
    xhr.open('POST', base_url+'/streamrequest', true);
    xhr.setRequestHeader('Content-Type', 'application/json');

    // 发送 JSON 数据
    xhr.send(JSON.stringify(data));

    // 监听请求的状态
    xhr.onreadystatechange = function() {
    if (xhr.readyState === 4 && xhr.status === 200) {
        console.log(xhr.responseText);
    }
    };
}

function setup(type){
    mtype = type;
    console.log("setup:" + mtype);
    init_conn();
}

function init_conn(){
    if (mtype == 'ws'){
        init_socket();
        if (USING_AU_WEBS)
            init_audio_socket();
    }else if (mtype=='event'){
        init_event();
    }
}
function send_reference(fileDetails) {
    if (mtype == 'ws') {
        var obj = {message:'', mode:mode, current_language:currentLanguage, tts_enabled:TTS_ENABLED, kdb_id: kdb_id, prompt_name: prompt_name,reference: fileDetails};
        var text = JSON.stringify(obj);
        console.log("发送refer在chatbox",text)
        socket.send(text);
    }
}


function send_text(message){
    console.log("发送消息到py===============")
    if (mtype=='event'){
        var obj = {message:message, token:token};
        sendMessage(obj);
    }
    else if (mtype=='ws'){
        var obj = {message:message, mode:mode, current_language:currentLanguage, tts_enabled:TTS_ENABLED, kdb_id: kdb_id, prompt_name: prompt_name, rag_node: rag_node};
        text = JSON.stringify(obj)
        socket.send(text);
    }
}


// 点击关闭按钮时，隐藏模态窗口
document.getElementById("node-close-btn").addEventListener('click', () => {
    document.getElementById("node-modal-overlay").style.display = 'none';
});


function shownodecontext(kdbId, node_id){
    const requestData = {
        kdb_id: kdbId,
        node_id: node_id
    };
    fetch(`${window.location.protocol}//${domain}/kdb/get_node_context`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(ndoe_content => {
        let nodeContentElement = document.getElementById('node-content');

        // 显示文件内容到模态窗口
        nodeContentElement.textContent = ndoe_content;
 
        // 使用 requestAnimationFrame 重置滚动条
        requestAnimationFrame(() => {
            nodeContentElement.scrollTop = 0;
        });

        // let modalOverlay = document.getElementById('modal-overlay');
        // // 显示模态窗口
        document.getElementById("node-modal-overlay").style.display = 'flex';
    })
    .catch(error => {
        console.error("error")
    });
}


function add_rag_node(nodes_info){
    console.log("nodes_info",nodes_info)

    // 检查 nodes_info 是否为空对象或 null/undefined
    if (!nodes_info || Object.keys(nodes_info).length === 0) {
        return;  // 如果为空，直接返回
    }

    const chatBox = document.getElementById('chat-box');

    const messageWrappers = chatBox.querySelectorAll('.message-wrapper');  // 选择所有 message-wrapper 元素
    // 获取最后一个 message-wrapper 元素
    const lastMessageWrapper = messageWrappers[messageWrappers.length - 1];
    const messageContainer = lastMessageWrapper.querySelector('.message-container')

    const node_show_area = document.createElement('div');

    // 创建 <p> 元素
    const paragraph = document.createElement('h3');
    paragraph.textContent = '查询使用到的文件中的信息:'; // 设置段落的文本内容

    // 将 <p> 插入到 node_area 中
    node_show_area.appendChild(paragraph);

    const node_area = document.createElement('div');
    node_area.className = 'node-area'

    Object.entries(nodes_info).forEach(([key, value]) => {
        const fileDiv = document.createElement('div');
        fileDiv.className = 'file-display';
        fileDiv.style.width = '17%';

        const fileIcon = document.createElement('img');
        fileIcon.src = '/static/images/file.png'; // 替换为你的文件图标路径
        fileIcon.alt = 'file icon';
        fileIcon.className = 'file-icon';
        fileIcon.style.width="35px";
        fileIcon.style.height="35px";

        // 创建内容区域 div
        const fileContent = document.createElement('div');
        fileContent.className = 'file-content';

        // 创建文件名和文件类型 div
        const fileNameDiv = document.createElement('div');
        fileNameDiv.className = 'file-name';
        fileNameDiv.id = value.name
        fileNameDiv.textContent = getTruncatedFileName(value.name)

        const fileTypeDiv = document.createElement('div');
        fileTypeDiv.className = 'file-type';
        fileTypeDiv.id = value.type;
        fileTypeDiv.textContent = `${mimeTypeMap[value.type]}, ${formatSize(value.size)}` || '未知类型'; 
        fileTypeDiv.style.display = 'block';

        fileDiv.addEventListener("click", () => {
            console.log("点击了node",value.id)
            shownodecontext(kdb_id, value.id);
        });

        fileContent.appendChild(fileNameDiv);
        fileContent.appendChild(fileTypeDiv);
        
        fileDiv.appendChild(fileIcon);
        fileDiv.appendChild(fileContent);
        node_area.appendChild(fileDiv)
    });
    node_show_area.appendChild(node_area);

    messageContainer.appendChild(node_show_area)

    // 滚动到底部
    chatBox.scrollTop = chatBox.scrollHeight;
}

function send_to_stop_svg(){
    const send_btn = document.getElementById("sendButton")
    send_btn.setAttribute('data-btn-type', 'stop'); // 修改自定义属性值

    // 获取现有的SVG元素
    const existingSVG = send_btn.querySelector('svg');

    // 定义新的SVG内容
    const newSVG = `
        <svg t="1736223005043" class="stop-icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="1453" xmlns:xlink="http://www.w3.org/1999/xlink" width="20" height="20">
            <path d="M722.9375 933.875H301.0625a210.9375 210.9375 0 0 1-210.9375-210.9375V301.0625a210.9375 210.9375 0 0 1 210.9375-210.9375h421.875a210.9375 210.9375 0 0 1 210.9375 210.9375v421.875a210.9375 210.9375 0 0 1-210.9375 210.9375z" p-id="1454"></path>
        </svg>
    `;

    // 用新的SVG替换现有的SVG
    existingSVG.outerHTML = newSVG;  // 替换整个SVG
}

function stop_to_send_svg(){
    const send_btn = document.getElementById("sendButton")
    const btnType = send_btn.getAttribute('data-btn-type');
    if(btnType !== "stop"){
        // 发送停止请求
        return;
    }

    send_btn.setAttribute('data-btn-type', 'send'); // 修改自定义属性值

    // 获取现有的SVG元素
    const existingSVG = send_btn.querySelector('svg');

    // 定义新的SVG内容
    const newSVG = `
    <svg t="1733282301774" class="send-icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="24" height="24">
        <path d="M535.06048 895.0784m-40.96 0l0 0q-40.96 0-40.96-40.96l0-573.44q0-40.96 40.96-40.96l0 0q40.96 0 40.96 40.96l0 573.44q0 40.96-40.96 40.96Z"></path>
        <path d="M493.03552 242.21696L289.792 445.44a40.96 40.96 0 1 1-57.93792-57.93792L463.58528 155.81184a40.96 40.96 0 0 1 58.44992-0.45056l231.69024 231.69024a40.96 40.96 0 1 1-57.91744 57.93792l-202.77248-202.77248z"></path>
    </svg>
    `;

    // 用新的SVG替换现有的SVG
    existingSVG.outerHTML = newSVG;  // 替换整个SVG
}

function on_message(event) {
    console.log('Message from server ', event.data);
    let jsonObject = JSON.parse(event.data);

    // 删除rag的加载圈
    let rag_spinner_gen = document.getElementById("rag_spinner_gen"); // 获取 id 为 myElement 的元素
    if (rag_spinner_gen) { // 确保元素存在，避免报错
        rag_spinner_gen.remove(); // 删除该元素
    }

    // 修改按钮svg为停止按钮
    if(jsonObject.text_type !== 'rag_node'){
        send_to_stop_svg()
    }

    if(jsonObject.text_type === 'stat'){
        return;
    }

    if (typeof jsonObject.text === 'string') {
        // 替换连续的4个空格为2个空格
        // jsonObject.text = jsonObject.text.replace(/    /g, '  ');
        // jsonObject.text = jsonObject.text.replace(/\n|\\n/g, '<br>')
    }
    if (jsonObject.text_type === 'redirect') {
        // 如果收到重定向指令，则跳转到登录页面
        window.location.href = '/login';  // 跳转到登录页
        return;  // 不继续处理其他消息
    }
    // jsonObject.text=processInMarkdowm(jsonObject.text);

    if (jsonObject.text_type == 'code'){
        console.log("lastrole",lastRole);
        if (lastRole === 'user') { // 只有在角色从 You 切换到 AI 时调用
            createMessageContainer();
            lastRole='assistant'
            }
        console.log("messagecon   :",messageContainer);
        addCodeBlock(jsonObject.text); // 调用 addCodeBlock 函数处理普通代码块
        current_codes += "\n" + jsonObject.text;
        if (jsonObject.text.trim().startsWith('maid') || jsonObject.text.trim().startsWith('ermaid')) {
            console.log("messagecon   :",messageContainer);
            addMaid(jsonObject.text); // 调用 addMaid 函数处理 Mermaid 流程图
        }
        currentParagraph === null
    } else if (jsonObject.text_type == 'file'){
        if (!FileContainer) {
            createFileContainer();  // 创建新的文件容器
        }
        addFilesToChatBox(jsonObject.text);

    }else if (jsonObject.text_type == 'link') {
        let url = findURL(jsonObject.text);
        if (url) {
            if (url.toLowerCase().endsWith(".jpg") || url.toLowerCase().endsWith(".jpeg") || url.toLowerCase().endsWith(".png"))
                addImageToChatbox(url);
            else
                addLinkToChatbox(url);
        }
    }
    else if (jsonObject.text_type == 'code_begin'){

        addCodeBlock("");
    }
    else if (jsonObject.text_type == 'code_continue'){
        addToExisting(jsonObject.text)
    }
    else if (jsonObject.text_type == 'code_end'){

    }
    else if (jsonObject.text_type == 'char'){
        if (jsonObject.text == '\n'){
            createParagraph();
            addToChatBox(jsonObject.text);
        }
        else
            addToExisting(jsonObject.text);
    }
    else if (jsonObject.text_type == 'json'){ // 添加新的 text_type
        // 以JSON格式显示数据
        let data_ = JSON.parse(jsonObject.text); // 解析 link 信息
        if (data_.datatype === 'link') {
            console.log("进入link")
            addlinkBlock(data_.data); // 调用处理 link 的函数
        }
        else
        {
            console.log('未知的 datatype:', linkInfo.datatype);
        }
    }
    else if (jsonObject.text_type == 'Markdown'){ // 添加新的 text_type
        addMarkdownBlock(jsonObject.text);
        // 获取prompt信息
    }
    else if (jsonObject.text_type == 'Graph'){

        let tomarkdowmContent = jsonObject.text
        // 将 <br> 标签替换成 Markdown 中的换行符
        tomarkdowmContent = marked.parse(tomarkdowmContent);
        // tomarkdowmContent = tomarkdowmContent.replace(/<strong>(.*?)<\/strong>：/g, '<strong>$1：</strong>'); // 把“：”放到 <strong> 内

        // tomarkdowmContent = show_data_el_rg(tomarkdowmContent)
        addGraphBlock(tomarkdowmContent, grapg_suffix.toString());
        // add_el_listener('.clickable-number')

        const targetDiv = document.getElementById(`chat-message-${grapg_suffix.toString()}`);
        if (targetDiv) {
            // 获取目标 <div> 的父级容器
            const parentContainer = targetDiv.closest(".message-container");
        
            if (parentContainer) {
                // 在同一个父级容器中查找 <p> 元素
                const messageParagraph = parentContainer.querySelector("p.chat-message");
        
                if (targetDiv && messageParagraph) {
                    // 获取 <p> 元素的内容
                    const messageContent = messageParagraph.innerHTML;
                
                    // 将内容插入到目标 div 的顶部
                    targetDiv.insertAdjacentHTML("afterbegin", messageContent);
                
                    // 移除原始 <p> 元素的内容（保留空的 <p> 元素，或删除元素）
                    messageParagraph.remove(); // 完全移除 <p> 元素
                }
            }
        }
        // 滚动到底部
        const chatBox = document.getElementById('chat-box');
        chatBox.scrollTop = chatBox.scrollHeight;
        show_data_el(targetDiv.textContent,grapg_suffix.toString())

        grapg_suffix++; // 更新 grapg_suffix
    }
    else if (jsonObject.text_type == 'rag_node'){
        add_rag_node(jsonObject.text)
    }
    else if (jsonObject.text_type == 'status'){ // 添加新的 text_type
        // 根据 status 的值调用不同的函数
        switch (jsonObject.text) {
            case 'searching sites':
                addMessageWrapperToChatBox();
                addAvatarToChatBox("/static/images/haifeng.jpeg");
                addhideBu(textObject.text);
                break; // 处理“searching sites”

            case 'chat_end':
                stop_to_send_svg()
                // RemoveAndShow();
                break;

            default:
                console.log('未知的 status:', textObject.text);
        }
    }else{
        if (jsonObject.role === 'assistant') {
            FileContainer=null;
            if (lastRole !== 'assistant') { 
                addMessageWrapperToChatBox();
                addAvatarToChatBox("/static/images/haifeng.jpeg");
                createMessageContainer() ;
                createParagraph();
            }

            addToChatBox(jsonObject.text);
            lastRole = 'assistant'; // 更新上次的 role
        } else if (jsonObject.role === 'user') {
            addToChatBoxUser(jsonObject.text, "userMessage");
            lastRole = 'user'; // 更新上次的 role
            currentParagraph = null;
            currentText = "";
        } else {
            if(messageContainer === null)
            {
                createMessageContainer();
                createParagraph();
            }
            if(currentParagraph === null)
            {
            createParagraph();
            }
            // console.log("add chat box ======",jsonObject.text)
            FileContainer=null;
            let tomarkdowmContent = jsonObject.text;
            // 将 <br> 标签替换成 Markdown 中的换行符
            // tomarkdowmContent = tomarkdowmContent.replace(/<br\s*\/?>/g, '  \n');  // 注意这里的两个空格和换行符
            // 传递处理过的文本给后端
            currentText += tomarkdowmContent;
            console.log("原始的文本是 :",currentText);
            let htmlContent = currentText
            htmlContent = processInMarkdowm(htmlContent)
            htmlContent = htmlContent.replace(/<strong>(.*?)<\/strong>：/g, '<strong>$1：</strong>'); // 把“：”放到 <strong> 内
            // htmlContent = htmlContent.replace(/^(\d+\.)\s?(<strong>.*?<\/strong>)/, '<strong>$1 $2</strong>');
            renewChatBox(htmlContent);
            // add_el_listener('.clickable-number')
            lastRole = 'assistant';
        }
    }
    
    // 渲染数学公式的函数
    renderMathInElement(document.body, {
        delimiters: [
            {left: "\\(", right: "\\)", display: false},  // 行内公式
            {left: "\\[", right: "\\]", display: true}    // 块级公式
        ]
    });

    updateHideButtonFunctionality();
    push_tts(jsonObject);

    // 滚动到底部
    const chatBox = document.getElementById('chat-box');
    chatBox.scrollTop = chatBox.scrollHeight;
}


function read_send(){
    const input = document.getElementById('userInput');  // 获取 contenteditable 的 p 元素
    const message = input.textContent.trim();

    const fileDivs = document.querySelectorAll('#userInputContainer .file-display');
    const fileDetails = Array.from(fileDivs).map(fileDiv => {
        const fileId = fileDiv.getAttribute('data-file-id'); // 获取 data-file-id
        const fileName = fileDiv.querySelector('.file-name').id;
        const fileType = fileDiv.querySelector('.file-type').id;
        const fileSize = fileDiv.querySelector('.file-type').dataset.size;
        return { file_id: fileId, filename: fileName, filetype: fileType, filesize: fileSize};
    });
    if (fileDetails.length > 0) {
        send_reference(fileDetails);
    }

    if (message) {
        addToChatBoxUser(message, "userMessage");
        lastRole='user'
        input.textContent = '';// 清空输入框
        currentParagraph = null;
        addMessageWrapperToChatBox();
        addAvatarToChatBox("/static/images/haifeng.jpeg");
        if (mode == "graphrag"){
            //加载圈
            showGraphLoadingSpinner()
            createMessageContainer(if_graphrag=true);
        }else if(mode == "faq"){
            //加载圈
            createMessageContainer(if_graphrag=false,if_faq=true);
        }else{
            createMessageContainer();
        }

        /* agent to control avatar*/
        if (mode == 'agent_avatar'){
            agent_exec(message);
        }else{
            send_text(message);
            if(fileDetails.length > 0){
                addFilesToChatBox(fileDetails);
                fileDivs.forEach(fileDiv => fileDiv.remove());
                setHeightDifTcb()
            }
        }
    }
}

function showGraphLoadingSpinner(text= resources["graphrag_anwser_text"], have_kdb=true) {
    // 存放加载圈文字和回答的div
    const loadingMaessageContainer = document.createElement('div');
    loadingMaessageContainer.id = 'graph-loading-message-container'; // 为容器设置 ID
    loadingMaessageContainer.className = "graph-loading-message-container";

    if(have_kdb){
        // 创建加载圈容器
        const loadingContainer = document.createElement('div');
        loadingContainer.id = 'graph-loading-container'; // 为容器设置 ID
        loadingContainer.style.display = "flex"; // 使用 flexbox 布局
        loadingContainer.style.alignItems = "center"; // 垂直居中

        // 创建旋转圈元素
        const spinner = document.createElement('div');
        spinner.id = 'spinner_gen';
        spinner.className = "spinner-answer";
        spinner.style.display = "inline-block";

        // 创建文本节点
        const loadingText = document.createElement('span');
        loadingText.id = "span_gen"
        loadingText.innerText = text; // 设置文本内容
        loadingText.className = "span-answer"
        // loadingText.style.marginLeft = "10px"; // 设置文本与加载圈之间的间距
        // loadingText.style.marginTop = ""

        // 将旋转圈和文本添加到加载圈容器中
        loadingContainer.appendChild(spinner);
        loadingContainer.appendChild(loadingText);
        loadingMaessageContainer.appendChild(loadingContainer);
    }
    // 将加载圈容器添加到聊天框中
    currentMessageWrapper.appendChild(loadingMaessageContainer);
}

// 移除加载圈和文本的函数
function removeLoadingSpinner() {
    const loadingContainer = document.getElementById('graph-loading-container');
    if (loadingContainer) {
        loadingContainer.remove(); // 移除加载圈容器
    }
}


function stop_session_gen(current_session_id){
    // 发送获取请求
    fetch(`/stop_gen/${current_session_id}`, {
        method: 'POST', // 使用 POST 请求
        headers: {
            'Content-Type': 'application/json', // 通常是 JSON 请求体类型
        },
    })
    .then(response => response.json())
    .then(result => {
        console.log("停止:",result);
    })
    .catch((error) => console.error('Error:', error));
}


document.getElementById('sendButton').addEventListener('click', function() {
    const userInputElement = document.getElementById('userInput');
    const userInput = userInputElement.textContent.trim(); // 获取 <p> 的文本内容并去掉前后空格

    // 判断是否有输入
    if (!userInput) {
        console.log("没有输入");
        return;
    }

    // 判断是否有文件正在分析中
    // 获取所有具有 'file-overlay' 类的元素
    const elements = document.querySelectorAll('.file-overlay');

    // 过滤出 style.display 为 'none' 的元素
    const countNotNone = Array.from(elements).filter(element => element.style.display !== 'none').length;

    if (countNotNone !== 0) {
        showPopup(resources.analyzing_file)
        return;
    }
    
    if (socket_status==='connected'){
        // 判断是否正在生成
        const btnType = sendButton.getAttribute('data-btn-type');
        if(btnType === "stop"){
            // 发送停止请求
            stop_session_gen(session_id)
        }else{
            // 删除之前的图谱
            removeGraph()
            read_send();
        }
    }else{
        init_conn();
        setTimeout(read_send, 1000);
    }
});


if (document.getElementById('stopButton'))
document.getElementById('stopButton').addEventListener('click', function() {

    if (currentAudio != null)
        currentAudio.stop();

    reset_audioQueue();

    const formData = new FormData();
    var request = new XMLHttpRequest();
    var STOP_URL = `${window.location.protocol}//${domain}/stop_audio`;

    request.open("POST", STOP_URL, true);
    request.send(formData);
    
});

//function addToChatBox(text) {
//    const chatBox = document.getElementById('chat-box');
//    chatBox.innerHTML += '<p>' + text + '</p>';
//    chatBox.scrollTop = chatBox.scrollHeight; // 滚动到底部
//}
//更新p段落
function addToChatBox(text) {
    // 追加文本到当前的 <p> 元素
    const chatBox = document.getElementById('chat-box');
    // 移除所有 alt="undefined" 的 img 标签
    document.querySelectorAll('img[alt="undefined"]').forEach(img => {
        img.remove();  // 删除该 img 标签
    });

    // console.log("当前的p是：",currentParagraph.textContent);
    // 滚动到底部
    currentParagraph.innerHTML += text;
    chatBox.scrollTop = chatBox.scrollHeight;
}

function renewChatBox(text) {
    // 追加文本到当前的 <p> 元素
    const chatBox = document.getElementById('chat-box');
    currentParagraph.innerHTML = text;
    // console.log("当前的p是：",currentParagraph.textContent);
    // 滚动到底部
    chatBox.scrollTop = chatBox.scrollHeight;
}

function detectFormat(text) {
    // Simple checks for CSV
    const csvPattern = /(?:[^,]*,){2,}/; // At least 2 commas in a line
    const lines = text.split('\n');

    if (lines.every(line => csvPattern.test(line.trim()) || line.trim() === '')) {
        return 'csv';
    }

    // Simple checks for Markdown
    const mdPattern = /(^# .+|^## .+|^### .+|^[-*] .+|^\|.+\|$)/m;
    if (mdPattern.test(text)) {
        return 'markdown';
    }

    return 'unknown';
}
function addCodeBlock(text) {
    const chatBox = document.getElementById('chat-box');
    // 创建一个新的 chat-message 容器
    const codediv = document.createElement('div');
    // 创建并添加 <pre> 元素来显示代码块
    const codeBlock = document.createElement('pre');
    codeBlock.classList.add('code-block');
    codeBlock.textContent = text;
    codediv.append(codeBlock);
    // 创建并添加保存按钮
    const saveBtn = document.createElement('button');
    saveBtn.classList.add('save-btn');
    saveBtn.textContent = resources["save"];
    codediv.append(saveBtn);
    messageContainer.appendChild(codediv)
    // 将 messageContainer 添加到 chatBox//messageContainer
    // 滚动到 chatBox 底部
    chatBox.scrollTop = chatBox.scrollHeight;
    currentParagraph=null
}

function addImageToChatbox(imageUrl) {
    // 获取聊天框元素
    var chatbox = document.getElementById('chat-box');

    // 创建一个新的<img>元素
    var img = document.createElement('img');
    img.src = imageUrl;
    img.alt = 'Chat Image';

    // 设置图片样式（可选）
    img.style.maxWidth = '80%'; // 确保图片不会超过聊天框宽度
    img.style.height = 'auto';   // 保持图片的原始比例

    // 将图片添加到聊天框中
    chatbox.appendChild(img);
}

function addLinkToChatbox(url, text='link'){
    // 获取聊天框元素
    var chatbox = document.getElementById('chat-box');

    // 创建一个新的<img>元素
    var link = document.createElement('a');
    link.setAttribute("href", url);
    link.textContent = text;
    chatbox.appendChild(link);
}
// 示例：添加一个指定URL的图片
//addImageToChatbox('http://appincloud.cn/terrylin.jpg');


async function get_audio_data(url) {
    // 示例API请求，实际使用时替换为相应的API
    const formData = new FormData();
    formData.append('url', url);
    const response = await fetch(`http://${domain}/audio`, {
        method: 'POST',
        body: formData
    });;
    console.log(response);
    const data = response.arrayBuffer();
    console.log(data);
    de(data);
    /*
    fetch('http://localhost:8000/audio', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        const data = response.arrayBuffer();
        de(data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
    */
}

const sleep = (delay) => new Promise((resolve) => setTimeout(resolve, delay))
let TTSQueue = []; // 音频缓冲区队列
let TTSRequesting = false;
async function push_tts(jsonObject){
    if (USING_AU_WEBS || !TTS_ENABLED){
        return;
    }
    await sleep(300);
    TTSQueue.push(jsonObject);
    if (!TTSRequesting){
        playNextTTS();
    }
}

function playNextTTS() {
    if (TTSQueue.length > 0) {
        const jsonObject = TTSQueue.shift(); // 从队列中取出下一个音频片段
        tts2(jsonObject);
    }
}

function tts(text){
    const formData = new FormData();
    formData.append('content', text);
    fetch(TTS_URL, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        const audioData = response.arrayBuffer();
        audioContext.decodeAudioData(audioData, function(buffer) {
            audioQueue.push(buffer);
            if (!isPlaying) {
                playNextAudio();
            }
        }, function(e) {
            console.log("Error with decoding audio data" + e.err);
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });
}


function tts2(jsonObject){
    TTSRequesting = true;
    const formData = new FormData();
    formData.append('content', jsonObject.text);
    formData.append('language', jsonObject.language);
    var request = new XMLHttpRequest();

    request.open("POST", TTS_URL, true);
    request.responseType = "arraybuffer";
    request.send(formData);
  
    request.onload = function () {
        TTSRequesting = false;
        var audioData = request.response;
        audioContext.decodeAudioData(audioData, function(buffer) {
            audioQueue.push(buffer);
            if (!isPlaying) {
                playNextAudio();
            }
        }, function(e) {
            console.log("Error with decoding audio data" + e.err);
        });
        playNextTTS();
    }
}

function tts3(url){
    const formData = new FormData();
    formData.append('content', url);
    var request = new XMLHttpRequest();

    request.open("POST", 'http://localhost:8000/audio', true);
    request.responseType = "arraybuffer";
    request.send(formData);
  
    request.onload = function () {
      var audioData = request.response;
      audioContext.decodeAudioData(audioData, function(buffer) {
          audioQueue.push(buffer);
          if (!isPlaying) {
              playNextAudio();
          }
      }, function(e) {
          console.log("Error with decoding audio data" + e.err);
      });
    }
}

async function digestMessage(message) {
    const msgUint8 = new TextEncoder().encode(message); // encode as (utf-8) Uint8Array
    const hashBuffer = await crypto.subtle.digest("SHA-256", msgUint8); // hash the message
    const hashArray = Array.from(new Uint8Array(hashBuffer)); // convert buffer to byte array
    const hashHex = hashArray
      .map((b) => b.toString(16).padStart(2, "0"))
      .join(""); // convert bytes to hex string
    return hashHex;
  }
  
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
let audioQueue = []; // 音频缓冲区队列
let isPlaying = false; // 当前是否正在播放

function reset_audioQueue(){
    while (audioQueue.length > 0)
        audioQueue.shift()
}

function de(audioData) {
    audioContext.decodeAudioData(audioData, function(buffer) {
        audioQueue.push(buffer);
        if (!isPlaying) {
            playNextAudio();
        }
    }, function(e) {
        console.log("Error with decoding audio data" + e.err);
    });
};

var currentAudio = null;

function playNextAudio() {
    if (audioQueue.length > 0) {
        const buffer = audioQueue.shift(); // 从队列中取出下一个音频片段
        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        source.start(0);
        isPlaying = true;
        currentAudio = source;
        source.onended = function() {
            isPlaying = false;
            playNextAudio(); // 当一段音频播放完毕后，播放下一段
        };
    }
}

function findURL(text) {
    // 方法1: 调整正则表达式以排除结尾的)
    const urlRegex = /https?:\/\/[^\s)>]+/g;
    const match = text.match(urlRegex);
    if (match) {
        let url = match[0];

        // 方法2: 检查和移除结尾的)
        if (url.endsWith(')')) {
            url = url.slice(0, -1);
        }

        return url;
    }

    return null;
}

// 示例使用
/*const inputText = "Check out this picture: <https://example.com/photo.jpg> It's amazing!";
const foundURL = findURL(inputText);

console.log(foundURL); // 输出: https://example.com/photo.jpg*/

// 复制内容到剪贴板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        console.log('内容已复制到剪贴板');
    }).catch(function(err) {
        console.error('无法复制内容: ', err);
    });
}


// 为所有复制按钮添加事件监听器
document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        let messageContent = this.previousElementSibling.textContent;
        copyToClipboard(messageContent);
    });
});

// 为所有执行按钮添加事件监听器
document.querySelectorAll('.execute-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        let messageContent = this.previousElementSibling.textContent;
        // 这里替换为你的服务器 URL
        fetch('https://your-server.com/execute', {
            method: 'POST',
            body: JSON.stringify({ message: messageContent }),
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(response => {
            if (response.ok) {
                console.log('内容已发送到服务器');
            } else {
                console.error('服务器响应错误');
            }
        }).catch(err => {
            console.error('发送请求失败: ', err);
        });
    });
});
document.querySelectorAll('.save-btn').forEach(btn => {
					// 要保存的字符串
					const stringData = this.previousElementSibling.textContent;
					// dada 表示要转换的字符串数据，type 表示要转换的数据格式
					const blob = new Blob([stringData], {
						type: "text/plain;charset=utf-8"
					})
					// 根据 blob生成 url链接
					const objectURL = URL.createObjectURL(blob)

					// 创建一个 a 标签Tag
					const aTag = document.createElement('a')
					// 设置文件的下载地址
					aTag.href = objectURL
					// 设置保存后的文件名称
					aTag.download = "文本文件.txt"
					// 给 a 标签添加点击事件
					aTag.click()
					// 释放一个之前已经存在的、通过调用 URL.createObjectURL() 创建的 URL 对象。

					// 当你结束使用某个 URL 对象之后，应该通过调用这个方法来让浏览器知道不用在内存中继续保留对这个文件的引用了。
					URL.revokeObjectURL(objectURL)
				}
);

// 为父元素添加事件监听器
document.getElementById('chat-box').addEventListener('click', function(event) {
    // 检查被点击的元素是否是复制按钮
    if (event.target.classList.contains('copy-btn')) {
        let messageContent = event.target.previousElementSibling.textContent;
        copyToClipboard(messageContent);
    }

    // 检查被点击的元素是否是执行按钮
    if (event.target.classList.contains('execute-btn')) {
        let messageContent = event.target.previousElementSibling.textContent;
    exec_script(messageContent);
    }
    if (event.target.classList.contains('save-btn')) {
        let messageContent = event.target.previousElementSibling.textContent;
        save_script(messageContent);
    }
});

// dada 表示要转换的字符串数据，type 表示要转换的数据格式
function save_script(stringData){
    var format = detectFormat(stringData);
    var ext_name = ".txt";
    if (format == 'csv'){
        ext_name = ".csv"
    }
    const blob = new Blob([stringData], {
            type: "text/plain;charset=utf-8"
    })
    // 根据 blob生成 url链接
    const objectURL = URL.createObjectURL(blob)

    // 创建一个 a 标签Tag
    const aTag = document.createElement('a')
    // 设置文件的下载地址
    aTag.href = objectURL
    // 设置保存后的文件名称
    aTag.download = "文本文件" + ext_name
    // 给 a 标签添加点击事件
    aTag.click()
    // 释放一个之前已经存在的、通过调用 URL.createObjectURL() 创建的 URL 对象。

    // 当你结束使用某个 URL 对象之后，应该通过调用这个方法来让浏览器知道不用在内存中继续保留对这个文件的引用了。
    URL.revokeObjectURL(objectURL)
}

function exec_script(messageContent){
    // 这里替换为你的服务器 URL
    let srv_url = `http://${domain}/exec_script`;
    fetch(srv_url, {
        method: 'POST',
        body: messageContent,
        headers: {
            'Content-Type': 'text/plain'
        }
    }).then(response => {
        if (response.ok) {
            console.log('内容已发送到服务器');
        } else {
            console.error('服务器响应错误');
        }
    }).catch(err => {
        console.error('发送请求失败: ', err);
    });
}

//addCodeBlock("hello");

function agent_exec(question){
    let srv_url = AGENT_URL;
    let token = "AppincloudAbcd";
    var httpRequest = new XMLHttpRequest();	//第一步：创建需要的对象
    httpRequest.open('POST', srv_url, true);	//第二步：打开连接
    /***发送json格式文件必须设置请求头 ；如下 - */
    httpRequest.setRequestHeader("Content-type","application/json; charset=utf-8");	// 设置请求头,注：post方式必须设置请求头（在建立连接后设置请求头）
    var obj = { question: question , token: token}
    httpRequest.send(JSON.stringify(obj));//发送请求 将json写入send中
    /**
     * 获取数据后的处理程序
     */
    httpRequest.onreadystatechange = function () {//请求后的回调接口，可将请求成功后要执行的程序写在其中
        if (httpRequest.readyState == 4 && httpRequest.status == 200) {//验证请求是否发送成功
            var json = httpRequest.responseText;//获取到服务端返回的数据
            let jsonObject = JSON.parse(json);
            if (jsonObject.ret){
                addToExisting(jsonObject.answer)
            }
        }
    };
}

document.getElementById('scriptButton').addEventListener('click', function() {
    exec_script(current_codes);
});
const spinnerMap = {};

function addhideBu(text) {
    const chatBox = document.getElementById('chat-box');
    const uniqueId = 'hide_button_' + Math.random().toString(36).substr(2, 9);

    // 创建一个新的 div 元素作为容器
    const hideButtonContainer = document.createElement('div');
    hideButtonContainer.className = 'hide-button-container';
    hideButtonContainer.id = uniqueId; // 设置唯一 ID

    // 创建加载圈元素
    const spinner2 = document.createElement('div');
    spinner2.className = "spinner";
    spinner2.style.display = "inline-block";
    spinner2.style.marginTop = '15px';

    // 创建隐藏按钮的 div 元素
    const toggleDiv = document.createElement('div');
    toggleDiv.className = 'hide_button';
    toggleDiv.textContent = text;
    toggleDiv.setAttribute('data-unique-id', uniqueId); // 设置唯一 ID 属性

    // 将加载圈和按钮添加到主容器中
    hideButtonContainer.appendChild(spinner2);
    hideButtonContainer.appendChild(toggleDiv);

    // 将主容器添加到聊天框中
    chatBox.appendChild(hideButtonContainer);

    // 使用一个唯一的标识符将 spinner 存储在 spinnerMap 中
    const spinnerId = 'spinner_' + uniqueId;
    spinnerMap[spinnerId] = spinner2;

    // 初始化状态，标记链接是否被隐藏
    let linksHidden = false;

    // 在 chatBox 容器上添加事件监听器 (事件委托)
    chatBox.addEventListener('click', function (event) {
        const target = event.target;

        // 检查点击的是否是一个隐藏按钮
        if (target.classList.contains('hide_button')) {
            const uniqueId = target.getAttribute('data-unique-id'); // 获取唯一 ID
            const hideButtonContainer = document.getElementById(uniqueId);

            // 获取当前链接组
            const linkItems = hideButtonContainer.nextElementSibling?.querySelectorAll('.link-container');
            linksHidden = !linksHidden; // 切换状态

            if (!linkItems) return; // 若链接组不存在则退出

            if (linksHidden) {
                linkItems.forEach(item => {
                    item.style.display = 'none'; // 隐藏链接
                });
                target.textContent = "资料链接";
            } else {
                linkItems.forEach(item => {
                    item.style.display = 'block'; // 显示链接
                });
                target.textContent = "隐藏链接";
            }

            // 隐藏对应的 spinner
            if (spinnerMap[spinnerId]) {
                spinnerMap[spinnerId].style.display = 'none';
            }

            // 打印当前状态
            console.log(`按钮 ${uniqueId} 当前状态：`, linksHidden ? "隐藏" : "显示");
        }
    });
}





function addlinkBlock(linkInfo) {
    const chatBox = document.getElementById('chat-box');

    // 创建一个新的 div 容器来存放链接
    const linkGroupContainer = document.createElement('div');

    linkInfo.forEach(link => {
        // 创建外层 div，添加新的 CSS 类
        const outerDiv = document.createElement('div');
        outerDiv.className = 'link-container '; // 使用新增的样式类

        // 创建链接的 a 标签，使用新的链接样式
        const anchor = document.createElement('a');
        anchor.href = link.url; // 设置链接
        anchor.target = '_blank';
        anchor.rel = 'noreferrer';
        anchor.className = 'link-anchor'; // 使用新的样式类

        // 创建显示标题的 div
        const titleDiv = document.createElement('div');

        titleDiv.textContent = link.name; // 设置名称

        // 创建显示 URL 的 div
        const urlDiv = document.createElement('div');
        urlDiv.textContent = link.url; // 设置 URL

        // 将标题和 URL 添加到链接
        anchor.appendChild(titleDiv);
        anchor.appendChild(urlDiv);

        // 将链接添加到外层 div
        outerDiv.appendChild(anchor);

        // 将外层 div 添加到 linkGroupContainer
        linkGroupContainer.appendChild(outerDiv);
    });

    // 将整个链接组添加到 chatBox
    chatBox.appendChild(linkGroupContainer);
    const spinner = chatBox.querySelector('#spinner_gen');
    const spinners = chatBox.querySelectorAll('.spinner');
    spinners.forEach(spinner => {
        spinner.remove();
    });
    Object.keys(spinnerMap).forEach(key => {
        delete spinnerMap[key];
    });
}
function addMarkdownBlock(text) {
    const chatBox = document.getElementById('chat-box'); // 获取聊天框元素
    let toadd = '<div class="chat-message">'; // 创建聊天消息的容器

    // 使用 marked 库将 Markdown 内容转换为 HTML
    let htmlContent = text
    htmlContent = marked.parse(htmlContent);
    htmlContent = htmlContent.replace(/<strong>(.*?)<\/strong>：/g, '<strong>$1：</strong>'); // 把“：”放到 <strong> 内

    // 将转换后的 HTML 添加到聊天消息中
    toadd += htmlContent; // 将解析后的 HTML 内容添加到容器中

    // 添加一个隐藏的 div 来存储原始 Markdown 内容
    toadd += '<div style="visibility: hidden;">' + text + '</div>';


    toadd += '</div>'; // 结束聊天消息容器
    chatBox.insertAdjacentHTML('beforeend', toadd); // 使用 insertAdjacentHTML 添加内容
    updateHideButtonFunctionality();
    chatBox.scrollTop = chatBox.scrollHeight; // 滚动到底部
}

function addGraphDataShowBlock(){
    const chatBox = document.getElementById('chat-box'); // 获取聊天框元素
    const data_show_infoBox = document.getElementById('data_show_infoBox'); // 获取聊天框元素
    if(data_show_infoBox){
        return;
    }else{
        // 创建信息展示框
        const data_show_infoBox = document.createElement('div');
        data_show_infoBox.id = "data_show_infoBox"
        data_show_infoBox.className = 'data_show_infoBox';
        data_show_infoBox.style.display = 'none'; // 初始化时隐藏展示框

        
        // 创建关闭按钮
        const closeButton = document.createElement('span');
        closeButton.id = "data_show_clsbtn"
        closeButton.className = 'close-btn';
        closeButton.innerHTML = '✖';

        // 使用 addEventListener 监听关闭按钮点击事件
        closeButton.addEventListener('click', function() {
            // 从 DOM 中移除图表容器
            data_show_infoBox.remove(); 
        });
        
        // 创建内容区域
        const infoContent = document.createElement('div');
        infoContent.id = "data_show_infoContent"
    
        // 将按钮和内容添加到信息框
        data_show_infoBox.appendChild(closeButton);
        data_show_infoBox.appendChild(infoContent);
        
        // 将信息框添加到页面
        chatBox.appendChild(data_show_infoBox);
    }

}
    


function addGraphBlock(text, suffix="0") {
    const chatBox = document.getElementById('chat-box'); // 获取聊天框元素

    // 如果有传入的后缀，拼接到ID后面
    const uniqueId = `${suffix ? `-${suffix}` : ''}`;

    // 创建一个 div 元素，并为其添加 class 和 id
    const chatMessageDiv = document.createElement('div');
    chatMessageDiv.className = 'graphrag-chat-message'; // 添加类名
    chatMessageDiv.id = `chat-message${uniqueId}`; // 设置唯一的ID

    // 将转换后的 HTML 添加到创建的 div 元素中
    chatMessageDiv.innerHTML = text; // text 可能是预先生成的 HTML 内容

    // 将生成的 div 插入到聊天框元素中
    messageContainer.appendChild(chatMessageDiv);
    
    // 创建展示超链接的div
    // 创建按钮容器
    const dataDisplay = document.createElement('div');
    dataDisplay.id = `data-display${uniqueId}`
    dataDisplay.style.fontSize = "16px"
    chatMessageDiv.appendChild(dataDisplay); // 在聊天消息中追加 data-display


    chatBox.scrollTop = chatBox.scrollHeight; // 滚动到底部
}

function createGraphBtn(suffix = "0") {
    const uniqueId = `${suffix ? `-${suffix}` : ''}`;

    // 创建按钮容器
    const buttonContainer = document.createElement('div');
    buttonContainer.id = `button-container${uniqueId}`
    buttonContainer.className = 'button-container';
    
    // 创建按钮
    const button = document.createElement('button');
    button.id = `chat-massage-btn${uniqueId}`;
    button.className = 'rounded-button';
    button.style.marginTop = '10px';  // 设置上方间距为 10px

    // 创建 SVG 元素
    const svgIcon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svgIcon.setAttribute('viewBox', '0 0 1024 1024');
    svgIcon.setAttribute('class', 'button-icon');

    // 第一个路径
    const path1 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path1.setAttribute('d', 'M341.333333 384a42.666667 42.666667 0 1 1-42.666666 42.666667 42.666667 42.666667 0 0 1 42.666666-42.666667m0-42.666667a85.333333 85.333333 0 1 0 85.333334 85.333334 85.333333 85.333333 0 0 0-85.333334-85.333334zM512 618.666667a21.333333 21.333333 0 1 1-21.333333 21.333333 21.333333 21.333333 0 0 1 21.333333-21.333333m0-42.666667a64 64 0 1 0 64 64 64 64 0 0 0-64-64zM725.333333 405.333333a21.333333 21.333333 0 1 1-21.333333 21.333334 21.333333 21.333333 0 0 1 21.333333-21.333334m0-42.666666a64 64 0 1 0 64 64 64 64 0 0 0-64-64z');
    
    // 第二个路径
    const path2 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path2.setAttribute('d', 'M667.733333 454.186667l-128 128a64 64 0 0 1 30.08 30.08l128-128a64 64 0 0 1-30.08-30.08zM490.666667 579.84l-81.706667-102.186667a83.413333 83.413333 0 0 1-33.28 26.666667l81.706667 101.973333A64 64 0 0 1 490.666667 579.84z');
    
    // 第三个路径
    const path3 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path3.setAttribute('d', 'M896 220.16v583.68L518.4 746.666667h-12.8L128 803.84V220.16L505.6 277.333333h12.8L896 220.16M938.666667 170.666667l-426.666667 64L85.333333 170.666667v682.666666l426.666667-64 426.666667 64V170.666667z');

    // 添加路径到 SVG
    svgIcon.appendChild(path1);
    svgIcon.appendChild(path2);
    svgIcon.appendChild(path3);

    // 将 SVG 添加到按钮
    button.appendChild(svgIcon);

    // 创建按钮文本
    const buttonText = document.createElement('span');
    buttonText.className = 'button-text';
    buttonText.textContent = resources['show_graph'];
    button.appendChild(buttonText);

    // 创建旋转圈元素
    const spinner = document.createElement('div');
    spinner.id = `spinner${uniqueId}`;
    spinner.className = "spinner";
    // spinner.style.display = "inline-block";

    // 将按钮和旋转圈添加到按钮容器中
    buttonContainer.appendChild(button);
    buttonContainer.appendChild(spinner);

    document.getElementById(`chat-message${uniqueId}`).appendChild(buttonContainer);
}

function createGraphBtnListener(suffix) {
    const button = document.getElementById(`chat-massage-btn-${suffix}`)
    button.addEventListener('click',  (event) => {
        const buttonText = button.querySelector(".button-text");
        if (buttonText.textContent === resources['show_graph']) {
            button.disabled = true; // 禁用按钮
            button.classList.add('disabled'); // 添加禁用样式类
            const parentDiv = event.target.closest('.graphrag-chat-message'); // 获取按钮的父级 div
            const parentId = parentDiv.id; // 获取父级 div 的 ID
            const parentContent = parentDiv.innerHTML; // 获取父级 div 的内容

            const match = parentId.match(/-(\d+)$/); // 匹配最后的数字
            if (match) {
                const lastNumber = match[1]; // 提取数字

                const spinner = document.getElementById(`spinner-${lastNumber}`);
                if (spinner) {
                    spinner.style.display = "inline-block"; // 显示加载圈
                } else {
                    console.error(`没有找到 ID 为 spinner-${lastNumber} 的元素`);
                }

                // 删除之前的图谱
                removeGraph();
                // 等待生成图谱
                // show_graph(parentContent, lastNumber.toString());
                show_graph_from_span(lastNumber.toString());
            } else {
                console.error('未能匹配 ID 中的数字');
                spinner.style.display = "none";
            }
        }else{
            removeGraph()
            buttonText.textContent = resources['show_graph']; // 改变按钮文字
        }
    });
}

function removeGraph() {
    // 查找 graphContainer
    const graphContainer = document.getElementById("graphContainer");

    if (graphContainer) {

        // 查找 graphContainer 的父元素
        const parent = graphContainer.parentElement;

        // 从 DOM 中移除图表容器
        graphContainer.remove();

        // 查找同级别的 button-container
        const buttonContainer = parent.querySelector('.button-container'); // 在父元素中查找 button-container


        if (buttonContainer) {
            // 获取 button
            const button = buttonContainer.querySelector('.rounded-button');
            const buttonText = button.querySelector(".button-text");
            if (button) {
                buttonText.textContent = resources['show_graph'];
            }
        }
    }
}

// 使用 Promise 封装 XMLHttpRequest，便于链式调用
function sendRequest(url, data) {
    return new Promise(function(resolve, reject) {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify(data));

        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    resolve(xhr.responseText);  // 成功时返回响应文本
                } else {
                    reject(xhr.statusText);  // 失败时返回错误信息
                }
            }
        };
    });
}

// 合并的函数
async function processGraphELRequest(or_text) {
    const prompt = { text: or_text };

    try {
        // 第一个请求：获得 prompt
        const responseText = await sendRequest(`${window.location.protocol}//${domain}/graphrag/get_prompt`, prompt);
        const promptData = JSON.parse(responseText);

        // 第二个请求：生成答案
        if (! promptData.question){
            return
        }
        const answerResponse = await sendRequest(`${window.location.protocol}//${domain}/generate`, promptData);
        const answer = JSON.parse(answerResponse).answer;

        // 正则表达式提取 JSON 字符串
        const jsonMatch = answer.match(/(\{.*\})/s);
        if (jsonMatch) {
            const jsonString = jsonMatch[1];  // 提取 JSON 字符串
            const idJson = JSON.parse(jsonString);  // 解析 JSON 字符串
            
            const info_josn = { kdb_id: kdb_id , id_json: idJson};

            // 获取entity和relationship的名字
            const answerResponse = await sendRequest(`${window.location.protocol}//${domain}/graphrag/get_el_name`, info_josn);
            const answer = JSON.parse(answerResponse);
            return {name_info: answer};  // 最终返回节点与链接数据
        } else {
            console.error("未找到有效的 JSON 字符串。");
            return null;
        }
    } catch (error) {
        console.error("Error during processing:", error);
        if (error.response) {
            // 打印服务器返回的错误信息
            console.error("Response data:", error.response.data);
            console.error("Response status:", error.response.status);
        }
    }
}


// 合并的函数
async function processGraphRequest(or_text) {
    const prompt = { text: or_text };

    try {
        // 第一个请求：获得 prompt
        const responseText = await sendRequest(`${window.location.protocol}//${domain}/graphrag/get_prompt`, prompt);
        const promptData = JSON.parse(responseText);

        // 第二个请求：生成答案
        const answerResponse = await sendRequest(`${window.location.protocol}//${domain}/generate`, promptData);
        const answer = JSON.parse(answerResponse).answer;

        // 正则表达式提取 JSON 字符串
        const jsonMatch = answer.match(/(\{.*\})/s);
        if (jsonMatch) {
            const jsonString = jsonMatch[1];  // 提取 JSON 字符串
            const idJson = JSON.parse(jsonString);  // 解析 JSON 字符串
            const data = {
                kdb_id: kdb_id,
                id_json: idJson
            };
            // 第三个请求：生成节点与链接
            const nlResponse = await sendRequest(`${window.location.protocol}//${domain}/graphrag/get_nl`, data);
            const nl = JSON.parse(nlResponse);

            return {nl: nl};  // 最终返回节点与链接数据
        } else {
            console.error("未找到有效的 JSON 字符串。");
            return null;
        }
    } catch (error) {
        console.error("Error during processing:", error);
        if (error.response) {
            // 打印服务器返回的错误信息
            console.error("Response data:", error.response.data);
            console.error("Response status:", error.response.status);
        }
    }
}


function createGraphContainer(suffix = "0") {
    const uniqueId = `${suffix ? `-${suffix}` : ''}`;
    // 创建主要的容器
    const graphContainer = document.createElement('div');
    graphContainer.className = 'graph-container';
    graphContainer.id = 'graphContainer';

    // 创建图形显示区域
    const showGraph = document.createElement('div');
    showGraph.className = 'show_graph';
    showGraph.id = 'show_graph';

    // 创建滑块控件区域
    const sliderControls = document.createElement('div');
    sliderControls.className = 'controls';
    sliderControls.id = 'sliderControls';

    const label = document.createElement('label');
    label.setAttribute('for', 'thresholdRange');
    label.textContent = resources['graph_bar'];

    const thresholdRange = document.createElement('input');
    thresholdRange.type = 'range';
    thresholdRange.id = 'thresholdRange';
    thresholdRange.min = 0;
    thresholdRange.max = 100;
    thresholdRange.value = 1;
    thresholdRange.step = 2;
    thresholdRange.style.width = '200px';

    const thresholdValue = document.createElement('span');
    thresholdValue.id = 'thresholdValue';
    thresholdValue.textContent = '1';

    // 将滑块控件添加到控件区域
    sliderControls.appendChild(label);
    sliderControls.appendChild(thresholdRange);
    sliderControls.appendChild(thresholdValue);

    // 创建信息框
    const infoBox = document.createElement('div');
    infoBox.className = 'infoBox';
    infoBox.id = 'infoBox';

    const closeButton = document.createElement('span');
    closeButton.className = 'close-btn';
    closeButton.textContent = '✖';
     // 传递动态生成的 id 给 hideInfo 函数
     closeButton.onclick = function() {
        hideInfo(); // 传递带有后缀的 id
    };
    // closeButton.onclick = hideInfo; // 绑定关闭函数

    const infoContent = document.createElement('div');
    infoContent.id = 'infoContent';

    // 将信息框的内容添加到信息框中
    infoBox.appendChild(closeButton);
    infoBox.appendChild(infoContent);

    // 将所有元素添加到主要容器中
    graphContainer.appendChild(showGraph);
    graphContainer.appendChild(sliderControls);
    graphContainer.appendChild(infoBox);
    // 将容器添加到主内容区域
    document.getElementById(`chat-message${uniqueId}`).appendChild(graphContainer);
}

function show_data_el(text,suffix){

    const span = document.getElementById("span_gen");
    if (span) {
        span.innerText = resources['graphrag_el_text']; // 设置文本内容
    }

    processGraphELRequest(text)
        .then((result) => {
            removeLoadingSpinner()
            const targetDiv = document.getElementById(`chat-message-${suffix.toString()}`);

            // 获取所有子元素
            const children = Array.from(targetDiv.children);

            // 找到 id="data-display-0" 元素
            const dataDisplayDiv = targetDiv.querySelector(`#data-display-${suffix.toString()}`);

            // 对其他元素进行修改（除了 id="data-display-0"）
            children.forEach(child => {
                // 如果子元素不是 id="data-display-0"
                if (child !== dataDisplayDiv) {
                    child.innerHTML = clean_data_graphrag(child.innerHTML)
                }
            });

            // 保持原始的 id="data-display-0" 元素不变
            targetDiv.innerHTML = '';
            // 将修改后的子元素和 id="data-display-0" 保持原样插入
            children.forEach(child => {
                if (child !== dataDisplayDiv) {
                    targetDiv.appendChild(child);
                }
            });
            targetDiv.appendChild(dataDisplayDiv);  // 保证 id="data-display-0" 保持在最后


            // 展示超链接
            const dataDisplay = document.getElementById(`data-display-${suffix.toString()}`);
            if (dataDisplay) {
                displayData(result.name_info, suffix)
                attachEventListeners()
            }
            // createGraphBtnListener()
        })
        .catch((error) => {
            removeLoadingSpinner()
        });
}

function clean_data_graphrag(text){
    // 只删除 [Data: ...] 部分的内容，不记录
    text = text.replace(/\[Data: [^\]]*\]/g, match => {
        return ''; // 删除匹配内容
    });

    // 只删除单独部分的数字（[Sources: ...], [Reports: ...], 等）并删除内容
    text = text.replace(/\[(Sources|Reports|Entities|Relationships|Claims): \(([^\)]+)\)\]/g, (_, key, numbers) => {
        return ''; // 删除匹配内容
    });

    return text
}

function show_data_el_rg(text){
    // 进行删除和修改
    text = text.replace(/\[Data: [^\]]*\]/g, match => {
        // console.log(match)
        // console.log("-----")
        // 处理每个匹配到的 [Data: ...] 部分
        return match.replace(/(Sources|Reports|Entities|Relationships|Claims) \(([^\)]+)\)/g, (_, key, numbers) => {
            // console.log(key)
            // console.log(numbers)
            // 提取数字并转换为 HTML 可点击元素
            const cleanNumbers = numbers.replace(', +more', '').split(',').map(num => num.trim());
            // console.log("提取出来的数字是", cleanNumbers);

            // 为每个数字创建可点击的 HTML 元素
            const clickableNumbers = cleanNumbers.map(num => {
                return `<span class="clickable-number" data-id="${num}" data-type="${key.trim().toLowerCase()}">${num}</span>`;
            }).join(', ');
            // console.log("第一步修改后的数字是",clickableNumbers)
            // 返回修改后的字符串，替换原来的数字
            return `${key} (${clickableNumbers})`;
        });
    });

    // 替换所有格式 [Data: ...], [Sources: ...], [Reports: ...], [Entities: ...], [Relationships: ...], [Claims: ...]
    text = text.replace(
        /(\[(Data|Sources|Reports|Entities|Relationships|Claims):\s*\()([^\)]+)\)/g,
        (_, fullMatch, key, numbers) => {
            console.log(fullMatch)
            console.log(key)
            console.log(numbers)
            // 处理 +more
            const cleanNumbers = numbers.replace(', +more', '').split(',').map(num => num.trim());
            console.log("第二部提取出来的数字是",cleanNumbers)
            // 为每个数字创建可点击的元素
            const clickableNumbers = cleanNumbers.map(num => {
                return `<span class="clickable-number" data-id="${num}" data-type="${key.trim().toLowerCase()}">${num}</span>`;
            }).join(', ');

            return `[${key}: (${clickableNumbers})]`;
        }
    );

    return text
}


function add_el_listener(className){
    // 为可点击数字添加事件
    document.querySelectorAll(className).forEach(element => {
        // 先移除之前可能存在的监听器
        element.removeEventListener('click', element._clickHandler);
        
        // 定义点击事件处理函数
        const clickHandler = () => {
            const id = element.dataset.id
            const type = element.dataset.type
            console.log(`ID: ${element.dataset.id}\nType: ${element.dataset.type}`);
            addGraphDataShowBlock()
            // 发送请求获得节点的信息
             // 判断节点类型
             if (type === 'entity' || type === 'entities') {
                // 在这里执行与 entity 相关的操作
                const url = `${window.location.protocol}//${domain}/graphrag/local_entity`;
                const data = { kdb_id: kdb_id,id : id };

                sendRequest(url, data)
                    .then(responseText => {
                        // 处理 responseText
                        if(responseText){
                            showInfo(resources['entity_info'], JSON.parse(responseText), "data_show_");
                        }
                    })
                    .catch(error => {
                        console.error("Error:", error);
                    });

            } else if (type === 'relationship' || type === 'relationships') {
                // 在这里执行与 relationship 相关的操作
                const url = `${window.location.protocol}//${domain}/graphrag/local_relationship`;
                const data = { kdb_id: kdb_id, id : id };

                sendRequest(url, data)
                    .then(responseText => {
                        // 处理 responseText
                        if(responseText){
                            showInfo(resources['relationship_info'], JSON.parse(responseText), "data_show_");
                        }
                    })
                    .catch(error => {
                        console.error("Error:", error);
                    });

            }
        };
        
        // 将处理函数保存在元素的一个私有属性中，以便以后移除
        element._clickHandler = clickHandler;
        
        // 添加事件监听器
        element.addEventListener('click', clickHandler);
    });
}

function show_graph(text,suffix) {
    const spinner = document.getElementById(`spinner-${suffix}`);
    if (spinner) {
        spinner.style.display = "inline-block"; // 显示加载圈
    }

    processGraphRequest(text)
        .then((result) => {
            // 在这里处理 result，比如更新 UI 或进一步操作

            // 隐藏加载圈
            if (spinner) {
                spinner.style.display = "none"; // 隐藏加载圈
            }

            // 默认展示图谱
            if (result.nl.is_show){
                // 移除按钮
                createGraphContainer(suffix.toString());
                showGraph(result.nl);
                const button = document.getElementById(`chat-massage-btn-${suffix}`)
                const buttonText = button.querySelector(".button-text");
                buttonText.textContent = resources['close_graph']; // 改变按钮文字
                button.disabled = false; // 禁用按钮
                button.classList.remove('disabled'); // 添加禁用样式类
            }else{
                removegraphBtn(suffix.toString())
            }
        })
        .catch((error) => {
            // 在发生错误时，确保按钮和加载圈的状态也能恢复
            if (spinner) {
                spinner.style.display = "none"; // 隐藏加载圈
            }
        });
}


function show_graph_from_span(suffix) {

    const spinner = document.getElementById(`spinner-${suffix}`);
    if (spinner) {
        spinner.style.display = "inline-block"; // 显示加载圈
    }

    // 获取包含数据的容器
    const dataDisplay = document.getElementById(`data-display-${suffix}`);

    // 定义目标结构
    const result = {
        entity: [],
        relationship: []
    };

    // 查询所有带有 `clickable-number` 类的元素
    const clickableNumbers = dataDisplay.querySelectorAll('.clickable-number');

    // 遍历这些元素并组织数据
    clickableNumbers.forEach(span => {
        const id = parseInt(span.getAttribute('data-id'), 10); // 获取并转换 `data-id` 为数字
        const type = span.getAttribute('data-type'); // 获取 `data-type`

        // 根据 `type` 将数据推入对应数组
        if (type === 'entity') {
            result.entity.push({ id });
        } else if (type === 'relationship') {
            result.relationship.push({ id });
        }
    });

    // 查看结果
    const data = {
        kdb_id: kdb_id,
        id_json: result
    };
    // 发送获取请求
    fetch(`${window.location.protocol}//${domain}/graphrag/get_nl`, {
        method: 'POST',
        credentials: 'include', // 发送 cookie
        headers: {
            'Content-Type': 'application/json' // 设置请求体的内容类型为 JSON
        },
        body: JSON.stringify(data) // 将对象转为 JSON 字符串s
    })
    .then(response => response.json())
    .then(result => {
        // 隐藏加载圈
        if (spinner) {
            spinner.style.display = "none"; // 隐藏加载圈
        }
        // 默认展示图谱
        if (result.is_show){
            // 移除按钮
            createGraphContainer(suffix.toString());
            showGraph(result);
            const button = document.getElementById(`chat-massage-btn-${suffix}`)
            const buttonText = button.querySelector(".button-text");
            buttonText.textContent = resources['close_graph']; // 改变按钮文字
            button.disabled = false; // 禁用按钮
            button.classList.remove('disabled'); // 添加禁用样式类
        }else{
            removegraphBtn(suffix.toString())
        }
    })
    .catch((error) => {
        // 在发生错误时，确保按钮和加载圈的状态也能恢复
        if (spinner) {
            spinner.style.display = "none"; // 隐藏加载圈
        }
    });
}

function removegraphBtn(suffix) {
    // 查找 graphContainer
    const buttonContainer = document.getElementById(`button-container-${suffix}`);

    if (buttonContainer) {
        // 从 DOM 中移除图表容器
        buttonContainer.remove(); 
    } else {
        console.error("Button container not found."); // 输出错误信息
    }
}

// 创建可点击的数字，并显示数据
function generateClickableNumbers(items, name, type) {
    if(type === "entity"){
        return items.map(item => {
            const entity_name = name[item.id] || "未知"; // 根据 item.id 获取对应的名字，找不到则显示 "未知"
            return `<span class="clickable-number" data-id="${item.id}" data-type="${type}">${item.id}: ${entity_name}</span>`;
        }).join(", ");
    }else{
        return items.map(item => {
            const rel_source_name = name["source_name"][item.id] || "未知"; // 根据 item.id 获取对应的名字，找不到则显示 "未知"    
            const rel_target_name = name["target_name"][item.id] || "未知";
            return `<span class="clickable-number" data-id="${item.id}" data-type="${type}">${item.id}: ${rel_source_name} --> ${rel_target_name}</span>`;
        }).join(", ");
    }
}

// 将数据插入到页面
function displayData(data,suffix) {
    const dataDisplay = document.getElementById(`data-display-${suffix.toString()}`);
    
    // 检查是否有 entity 或 relationship 的数据
    const hasEntities = data.ef_id.entity && data.ef_id.entity.length > 0;
    const hasRelationships = data.ef_id.relationship && data.ef_id.relationship.length > 0;

    if (!hasEntities && !hasRelationships) {
        // 如果 entity 和 relationship 都为空，隐藏 dataDisplay
        dataDisplay.style.display = 'none';
        return;
    }

    // 如果有 entity 或 relationship，显示 dataDisplay
    dataDisplay.style.display = 'block';
    
    let dataHtml = '<br>'+ `<span style="font-size: 20px; font-weight: bold; color: black;">${resources['el_info_show']} </span>` + '<br>';

    const entities = hasEntities ? `${resources['entity_info']}： (${generateClickableNumbers(data.ef_id.entity, data.entity_name,'entity')})` : '';
    const rel_name = {
        source_name: data.relationship_source_name || resources['unknow'], 
        target_name: data.relationship_target_name || resources['unknow']
    };
    const relationships = hasRelationships ? `${resources['relationship_info']}： (${generateClickableNumbers(data.ef_id.relationship, rel_name,'relationship')})` : '';

    // 拼接不为空的部分
    if (entities) {
        dataHtml += entities + '<br>';
    }
    if (relationships) {
        if (entities) dataHtml += '<br>'; // 如果前面有实体部分，添加分号
        dataHtml += relationships;
    }

    dataDisplay.innerHTML = dataHtml; // 更新显示的内容

    createGraphBtn(suffix.toString())
    createGraphBtnListener(suffix.toString())
}


// 添加点击事件处理器
function attachEventListeners() {
    const numbers = document.querySelectorAll('.clickable-number');
    numbers.forEach(number => {
        number.addEventListener('click', (event) => {
            const id = number.getAttribute('data-id');
            const type = number.getAttribute('data-type'); // 获取类型
            addGraphDataShowBlock()
            // 发送请求获得节点的信息
             // 判断节点类型
             if (type === 'entity') {
                // 在这里执行与 entity 相关的操作
                const url = `${window.location.protocol}//${domain}/graphrag/local_entity`;
                const data = { kdb_id: kdb_id,id : id };

                sendRequest(url, data)
                    .then(responseText => {
                        // 处理 responseText
                        if(responseText){
                            showInfo(resources['entity_info'], JSON.parse(responseText), "data_show_");
                        }
                    })
                    .catch(error => {
                        console.error("Error:", error);
                    });

            } else if (type === 'relationship') {
                // 在这里执行与 relationship 相关的操作
                const url = `${window.location.protocol}//${domain}/graphrag/local_relationship`;
                const data = { kdb_id: kdb_id, id : id };

                sendRequest(url, data)
                    .then(responseText => {
                        // 处理 responseText
                        if(responseText){
                            showInfo(resources['relationship_info'], JSON.parse(responseText), "data_show_");
                        }
                    })
                    .catch(error => {
                        console.error("Error:", error);
                    });

            }
        });
    });
}

//dom???????

function updateHideButtonFunctionality() {
    // 获取所有隐藏按钮
    const hideButtons = document.querySelectorAll('.hide_button');
    hideButtons.forEach(hideButton => {
        // 重新添加事件监听器
        hideButton.onclick = function() {
            const linkItems = hideButton.parentElement.nextElementSibling.querySelectorAll('.link-item'); // 获取当前组的所有链接项
            const isHidden = linkItems[0] && linkItems[0].style.display === 'none'; // 判断当前状态
            linkItems.forEach(item => {
                item.style.display = isHidden ? 'block' : 'none'; // 切换显示状态
            });
            hideButton.textContent = isHidden ? 'searching sites' : '资料链接'; // 根据状态更新按钮文本
        };
    });
}

function set_session_id(sid){
    session_id = sid
}
// 显示消息的函数



function displayMessageFromHistory(jsonObject) {
    console.log("HISTORY ======",jsonObject);
     if (typeof jsonObject.text === 'string') {
        // 替换连续的4个空格为2个空格
        // jsonObject.text = jsonObject.text.replace(/    /g, '  ');
        // jsonObject.text = jsonObject.text.replace(/\n|\\n/g, '<br>')
    }
    // jsonObject.text=processInMarkdowm(jsonObject.text);
    if (jsonObject.text_type == 'code'){
        console.log("lastrole",lastRole);
        if (lastRole === 'user') { // 只有在角色从 You 切换到 AI 时调用
            addMessageWrapperToChatBox();
            addAvatarToChatBox("/static/images/haifeng.jpeg");
            createMessageContainer();
            lastRole='assistant'
            }
        addCodeBlock(jsonObject.text); // 调用 addCodeBlock 函数处理普通代码块
        current_codes += "\n" + jsonObject.text;
        if (jsonObject.text.trim().startsWith('maid') || jsonObject.text.trim().startsWith('ermaid')) {
            console.log("messagecon   :",messageContainer);
            addMaid(jsonObject.text); // 调用 addMaid 函数处理 Mermaid 流程图
    }
    }else if (jsonObject.text_type == 'file'){
         if (!FileContainer) {
            createFileContainer();  // 创建新的文件容器
        }
        addFilesToChatBox(jsonObject.text);
    }else if (jsonObject.text_type === 'link') {
        let url = findURL(jsonObject.text);
        if (url) {
            if (url.toLowerCase().endsWith(".jpg") || url.toLowerCase().endsWith(".jpeg") || url.toLowerCase().endsWith(".png"))
                addImageToChatbox(url);
             else
                addLinkToChatbox(url);
        }
    }
    else if (jsonObject.text_type === 'code_begin') {
        addCodeBlock("");
    } else if (jsonObject.text_type === 'code_continue') {
        addToExisting(jsonObject.text);
    } else if (jsonObject.text_type === 'char') {
        if (jsonObject.text === '\n') {
            createParagraph();
            addToChatBox(jsonObject.text);

        } else {
            addToExisting(jsonObject.text);
        }
    } else if (jsonObject.text_type === 'json') {
        let data_ = JSON.parse(jsonObject.text);
        if (data_.datatype === 'link') {
            addlinkBlock(data_.data);
        }
    } else if (jsonObject.text_type === 'Markdown') {
        const chatBox = document.getElementById('chat-box');
        const text = jsonObject.text;
        const prefix = jsonObject.role + ': ';

        const prefixDiv = document.createElement('div');
        prefixDiv.className = 'chat-message';
        prefixDiv.textContent = prefix;

        chatBox.insertAdjacentElement('beforeend', prefixDiv);

        addMarkdownBlock(text);

    } else if (jsonObject.text_type === 'Graph') {
        addMessageWrapperToChatBox();
        
        addAvatarToChatBox("/static/images/haifeng.jpeg");
        if(kdb_id){
            showGraphLoadingSpinner(resources['graphrag_el_text']);
        }else{
            showGraphLoadingSpinner(resources['graphrag_el_text'],have_kdb=false);
        }
        createMessageContainer(if_graphrag=true);
        let htmlContent = jsonObject.text
        htmlContent = marked.parse(htmlContent);
        htmlContent = htmlContent.replace(/<strong>(.*?)<\/strong>：/g, '<strong>$1：</strong>'); // 把“：”放到 <strong> 内

        // htmlContent = show_data_el_rg(htmlContent)
        // htmlContent = clean_data_graphrag(htmlContent)

        addGraphBlock(htmlContent, grapg_suffix.toString());
        // add_el_listener('.clickable-number')

        //kdb_id不为空才进行el的检索
        if(kdb_id){
            show_data_el(jsonObject.text, grapg_suffix.toString());
        }
        grapg_suffix++;
    } else if (jsonObject.text_type == 'rag_node'){
        add_rag_node(jsonObject.text)
    } else if (jsonObject.text_type === 'status') {
        let textObject
        if (typeof jsonObject.text === 'string') {
        textObject = JSON.parse(jsonObject.text);  // 仅在是字符串时解析
        } else {
            textObject = jsonObject.text;  // 如果已经是对象，则直接使用
        }
        if (textObject.status) {
            switch (textObject.status) {
                case 'searching sites':
                    if (lastRole !== 'assistant') { // 只有在角色从 You 切换到 AI 时调用
                        addMessageWrapperToChatBox();
                        addAvatarToChatBox("/static/images/haifeng.jpeg");
                    }
                    addhideBu(textObject.text);
                    break;
                case 'chat_end':
                    //processInMarkdowm();
                    break;
                default:
                    console.log('未知的 status:', textObject.status);
            }
        }
    } else {
        if (jsonObject.role === 'assistant') {
            if (lastRole !== 'assistant') { // 仅在角色切换时调用
                addMessageWrapperToChatBox();
                addAvatarToChatBox("/static/images/haifeng.jpeg");
                createMessageContainer() ;
                createParagraph();
                FileContainer=null;
            }
            if(currentParagraph === null)
            {
                createParagraph();
            }
            let htmlContent = jsonObject.text

            console.log("进入markdowm前的文本是:",htmlContent)
            htmlContent = processInMarkdowm(htmlContent)
            // htmlContent = marked.parse(htmlContent);
            console.log("markdowm后的文本是:",htmlContent)
            htmlContent = htmlContent.replace(/<strong>(.*?)<\/strong>：/g, '<strong>$1：</strong>'); // 把“：”放到 <strong> 内
            htmlContent= `<p>${htmlContent}</p>`;
            addToChatBox(htmlContent);
            lastRole = 'assistant'; // 更新上次的 role
        } else if (jsonObject.role === 'user') {
            addToChatBoxUser(jsonObject.text, "userMessage");
            currentText = "";
            lastRole = 'user'; // 更新上次的 role
        } else {
            let htmlContent = jsonObject.text
            htmlContent = processInMarkdowm(htmlContent)

            // htmlContent = marked.parse(htmlContent);
            htmlContent = htmlContent.replace(/<strong>(.*?)<\/strong>：/g, '<strong>$1：</strong>'); // 把“：”放到 <strong> 内
            // console.log("add chat box ======",htmlContent);
            htmlContent= `<p>${htmlContent}</p>`;
            addToChatBox(htmlContent);
        }
    }
    
    // 渲染数学公式的函数
    renderMathInElement(document.body, {
        delimiters: [
            {left: "\\(", right: "\\)", display: false},  // 行内公式
            {left: "\\[", right: "\\]", display: true}    // 块级公式
        ]
    });
    updateHideButtonFunctionality();
    push_tts(jsonObject);
}



// 从 history_list 中倒序显示
function displayHistory(historyList) {
    // 倒序遍历 history_list
    //historyList = JSON.parse(str1)
    for (let i = historyList.length - 1; i >= 0; i--) {
        let jsonObject = historyList[i];
        displayMessageFromHistory(jsonObject); // 调用显示函数
    }
}


function addToChatBoxUser(message, type) {
    const chatBox = document.getElementById('chat-box');
    // 设置消息内容
    createFileContainer();
    const messageDiv = document.createElement('div');
    messageDiv.className = type; // 根据类型应用样式
    messageDiv.textContent = message;

    chatBox.appendChild(messageDiv); // 将消息添加到聊天框

    if(type === "userMessage"){
        const elementsWithClass = chatBox.querySelectorAll('.userMessage'); // 获取所有具有指定类名的子元素
        const previousElement = messageDiv.previousElementSibling;
        // 如果上方有元素，则设置 margin-top
        if (elementsWithClass.length !== 1 && previousElement && !previousElement.hasChildNodes()) {
            console.log("userMessage的上元素是",previousElement)
            messageDiv.style.marginTop = '50px'; // 可以根据需要调整这个值
        }
    }
    
    chatBox.scrollTop = chatBox.scrollHeight; // 滚动到最新消息
    
}
function addAvatarToChatBox(avatarSrc, if_graphrag=false) {
    if (!currentMessageWrapper) {
        console.error('请先创建消息外部容器'); // 如果外部容器不存在，输出错误
        return;
    }

    const avatarImg = document.createElement('img');
    avatarImg.src = avatarSrc; // 头像图片路径
    avatarImg.alt = 'Avatar';
    avatarImg.className = 'avatar'; // 使用 CSS 类名
    if(if_graphrag){

    }
    currentMessageWrapper.appendChild(avatarImg); // 将头像添加到当前消息外部容器
    currentMessageWrapper.scrollTop = currentMessageWrapper.scrollHeight; // 滚动到最新消息
}
function createMessageContainer(if_graphrag=false, if_faq=false) {
    const mescontainer = document.createElement('div');
    mescontainer.className = 'message-container';
    if (!currentMessageWrapper) {
        console.error('请先创建消息外部容器'); // 如果外部容器不F存在，输出错误
        return;
    }
    if(if_graphrag){
        // 假设 currentMessageWrapper 是父容器 div 元素
        const loadingMessageContainer = currentMessageWrapper.querySelector('#graph-loading-message-container');
        loadingMessageContainer.appendChild(mescontainer); // 添加到当前消息外部容器
    }else{
        if(if_faq){
            // 创建旋转圈元素
            const spinner = document.createElement('div');
            spinner.id = 'rag_spinner_gen';
            spinner.className = "spinner-answer";
            spinner.style.display = "inline-block";
            currentMessageWrapper.appendChild(spinner);
        }
        currentMessageWrapper.appendChild(mescontainer); // 添加到当前消息外部容器
    }
    messageContainer=mescontainer;// 更新全局变量
    const chatBox = document.getElementById('chat-box'); // 获取聊天框元素
    // 滚动到最新消息   
    chatBox.scrollTop = chatBox.scrollHeight;
}


function createFileContainer() {
    // 创建新的 div 容器
    FileContainer = document.createElement('div');
    FileContainer.className = 'file-container';  // 可以根据需要添加样式类名
    document.getElementById('chat-box').appendChild(FileContainer);  // 将容器添加到 chat-box 或其他目标容器中
}

function addMessageWrapperToChatBox() {
    const chatBox = document.getElementById('chat-box'); // 获取聊天框元素

    // 创建外部容器
    const messageWrapper = document.createElement('div');
    messageWrapper.className = 'message-wrapper'; // 设置类名
    // 将外部容器添加到聊天框
    chatBox.appendChild(messageWrapper);
    chatBox.scrollTop = chatBox.scrollHeight; // 滚动到最新消息
    currentMessageWrapper = messageWrapper; // 更新全局变量
}

function createParagraph() {
    const Paragraph = document.createElement('p'); // 创建新的 <p> 元素
    Paragraph.className = 'chat-message';

    messageContainer.appendChild(Paragraph); // 将 <p> 元素添加到 messageContainer 中
    currentParagraph = Paragraph; // 更新全局的 currentParagraph
    currentText = "";
}

async function fetchImage(image_name, doc_id) {
    // 获取 URL 查询参数中的 kdb_id
    const urlParams = new URLSearchParams(window.location.search);
    const kdbId = urlParams.get('kdb_id'); // 获取 'kdb_id' 参数
    const baseURL = window.location.origin; // 网站基础路径
    console.log("baseURL",baseURL);
    if (!kdbId) {
        console.error("kdb_id is missing from the URL.");
        return;
    }

    // 构建图片获取的 API 请求 URL
    const apiUrl = `${baseURL}/kdb/get_image?image_name=${image_name}&doc_id=${doc_id}&kdb_id=${kdbId}&session_id=${session_id}`;
    try {
        // 获取显示图片的容器
        const imageContainer = document.getElementById('chat-box');

        // 创建并展示图片
        const imgElement = document.createElement('img');
        imgElement.src = apiUrl;
        imgElement.alt = image_name;
        imgElement.className = 'chat-image';
        //上面不生效？
         imgElement.style.height = '300px';   // 设置固定高度为 300px
        imgElement.style.width = 'auto';
        imgElement.addEventListener('click', () => {
            showModal(imgElement.src);
        });
        imageContainer.appendChild(imgElement);
        imageContainer.appendChild(document.createElement('br'))
    } catch (error) {
        console.error('Error fetching image:', error);
    }
}
let previousText = "";

function extractImageInfo(text) {
    text = text.replace(/!\[\]\(([^)]+)\)/g, (match, capturedGroup, offset, fullText) => {
        // 从匹配的链接中提取文件名
        let imageName = capturedGroup.split('/').pop(); // 获取文件名部分
        // 基于原始文件名生成新链接
        const doc_id = imageName.split('_')[1];
        
        // 如果 doc_id 无效，返回空字符串
        if (isNaN(doc_id)) {
            return "";
        }

        const kdbId = new URLSearchParams(window.location.search).get('kdb_id') ?? '';
        const apiUrl = `${window.location.origin}/kdb/get_image?image_name=${imageName}&doc_id=${doc_id}&kdb_id=${kdbId}&session_id=${session_id}&resize=True`;

        // 使用 XMLHttpRequest 进行同步 GET 请求
        const xhr = new XMLHttpRequest();
        xhr.open('GET', apiUrl, false);  // false 表示同步请求
        try {
            xhr.send();

            if (xhr.status >= 200 && xhr.status < 300) {
                // 如果响应成功，返回图片标签
                return `<br>![](${apiUrl})<br>`;
            } else {
                // 如果响应失败，返回空字符串
                console.log(`API URL无效: ${apiUrl}`);
                return "";
            }
        } catch (error) {
            // 请求错误时，返回空字符串
            console.log(`请求出错: ${error}`);
            return "";
        }
    });
    return text;
}


function encodeMathInMarkdown(markdownContent) {
    // 正则表达式，用于匹配块级公式（\[\]）和行内公式（\(\)）
    const formulaRegex = /\\\[(.*?)\\\]|\\\((.*?)\\\)/gs;  // 这里添加了 `s` 修饰符，允许匹配多行内容

    let formulaPlaceholders = [];
    let index = 0;

    // 1. 使用占位符替换公式部分
    markdownContent = markdownContent.replace(formulaRegex, (match, blockFormula, inlineFormula) => {
        let formula = blockFormula || inlineFormula;  // 获取公式内容
        formulaPlaceholders.push(formula);

        // 生成占位符，并递增 index
        const placeholder = `$$FORMULA_${index++}$$`;  // 每次生成唯一的占位符
        return placeholder;  // 返回占位符
    });

    // 2. 返回编码后的 Markdown 内容和公式占位符列表
    return { encodedContent: markdownContent, formulaPlaceholders };
}

function decodeMathFromMarkdown(encodedContent, formulaPlaceholders) {
    formulaPlaceholders.forEach((formula, i) => {
        const placeholder = `$$FORMULA_${i}$$`;

        // 判断公式是否为块级公式，块级公式通过换行符或其他特征来识别
        const isBlockFormula = formula.includes('\\');  // 如果公式包含 `\\`，则认为是块级公式

        // 根据是否为块级公式决定如何渲染
        const mathHTML = isBlockFormula
            ? `\\[ ${formula} \\]`  // 块级公式：恢复为 \[ 公式内容 \]
            : `\\( ${formula} \\)`;  // 行内公式：恢复为 \( 公式内容 \)
        
        // 替换占位符为实际的公式
        encodedContent = encodedContent.replace(placeholder, mathHTML);
    });

    // 3. 返回最终的 HTML 内容
    return encodedContent;
}

function processInMarkdowm(text) {
    text = extractImageInfo(text)
    // 1. 调用编码函数，将公式替换为占位符
    const { encodedContent, formulaPlaceholders } = encodeMathInMarkdown(text);
    // 2. 使用 marked 解析编码后的 Markdown 内容
    const htmlContent = marked.parse(encodedContent, { renderer: renderer });
    // 3. 调用解码函数，将占位符还原为实际的数学公式
    //console.log("markdowm后的为本是",htmlContent)
    const finalContent = decodeMathFromMarkdown(htmlContent, formulaPlaceholders);

    return finalContent
}

function extractImageInfoAndShow(text) {
    console.log("Extracting:", text);

    // 检查是否为字符串
    if (typeof text !== "string") {
        console.log("Input is not a string. Returning without processing.");
        return text; // 如果不是字符串，直接返回原始输入
    }

    // 使用正则表达式分块处理，保留完整的 <img> 标签
    const parts = text.split(/(<img\s+[^>]*>)/); // 分割文本，将 <img> 标签单独分开

    let updatedText = parts
        .map(part => {
            if (part.startsWith("<img")) {
                // 保留原有的 <img> 标签
                return part;
            }

            // 对非 <img> 部分的文本进行图片名称替换
            const imagePattern = /(?:\*?\s*[^a-zA-Z0-9]*\s*image_name\s*[:：]?\s*[^a-zA-Z0-9]*\s*)?(doc_\d+_page_\d+_image_([\w\u4e00-\u9fa5]+?)\.\w+)/g;

            return part.replace(imagePattern, (match, imageName) => {
                // 构建图片的 API URL，imageName 只包含文件名
                const apiUrl = `${window.location.origin}/kdb/get_image?image_name=${imageName}&doc_id=${imageName.split('_')[1]}&kdb_id=${new URLSearchParams(window.location.search).get('kdb_id')}&session_id=${session_id}`;

                // 创建 `<img>` 标签
                const imgTag = `<img src="${apiUrl}" alt="${imageName}" class="chat-image" style="height: 300px; width: auto;" onclick="showModal('${apiUrl}')"/>`;
                console.log("图片的转换",imgTag)
                // if(){}
                // 返回替换后的内容，确保前后都有 `<br>`
                return `<br>${imgTag}<br>`;
            });
        })
        .join(""); // 将分割后的部分重新拼接为完整文本

    updatedText = updatedText.replace(/[\s,，]*&lt;br&gt;/g, '&lt;br&gt;');
    console.log("updatedText:", updatedText);
    return updatedText;
}


function extractImageInfoAndShow_new(text) {
    console.log("Extracting:", text);

    // 检查是否为字符串
    if (typeof text !== "string") {
        console.log("Input is not a string. Returning without processing.");
        return text; // 如果不是字符串，直接返回原始输入
    }

    // 使用正则表达式分块处理，保留完整的 <img> 标签
    const parts = text.split(/(<img\s+[^>]*>)/); // 分割文本，将 <img> 标签单独分开
    console.log("分割后的 parts:", parts);

    let updatedText = parts
        .map(part => {
            if (part.startsWith("<img")) {
                // 保留原有的 <img> 标签
                return part;
            }

            // 处理包含 "image_name:" 的部分
            const part_s = part.split(/(image_name:[^\s]+)/g);
            console.log("分割后的 part_s:", part_s);

            // 处理每一部分，替换 image_name 为 <img> 标签
            return part_s
                .map(innerPart => {
                    if (innerPart.startsWith("image_name:")) {
                        // 提取 image_name 后的图片名称列表
                        const imageNames = innerPart.replace(/^image_name:/, "").trim().split(',');

                        // 生成多个 <img> 标签
                        return imageNames
                            .map(imageName => {
                                const apiUrl = `${window.location.origin}/kdb/get_image?image_name=${imageName}&doc_id=${imageName.split('_')[1]}&kdb_id=${new URLSearchParams(window.location.search).get('kdb_id')}&session_id=${session_id}`;

                                // 创建 `<img>` 标签
                                const imgTag = `<img src="${apiUrl}" alt="${imageName}" class="chat-image" style="height: 300px; width: auto;" onclick="showModal('${apiUrl}')"/>`;
                                console.log("图片的展示",imgTag)
                                // 返回 `<img>` 标签并包裹在 `<br>` 中
                                return `<br>${imgTag}<br>`;
                            })
                            .join(""); // 将所有的 <img> 标签合并为一个字符串
                    }
                    // 如果不是 image_name 部分，直接返回
                    return innerPart;
                })
                .join(""); // 将分割后的部分重新拼接为完整文本
        })
        .join(""); // 将所有处理过的部分重新拼接为完整文本

    // 清理多余的换行符，确保没有多余的空白字符
    updatedText = updatedText.replace(/[\s,，]*<br>/g, '<br>');
    console.log("updatedText:", updatedText);
    return updatedText;
}


// 展示模态框的函数
function showModal(imageUrl) {
    console.log("图片被点击了，显示模态框：", imageUrl);

    // 创建模态框元素
    const modal = document.createElement('div');
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100%'; // 让模态框覆盖整个页面
    modal.style.height = '100%'; // 让模态框覆盖整个页面
    modal.style.backgroundColor = 'rgba(0, 0, 0, 0.7)'; // 设置背景色为半透明黑色
    modal.style.display = 'flex';
    modal.style.justifyContent = 'center'; // 水平居中
    modal.style.alignItems = 'center'; // 垂直居中
    modal.style.zIndex = '1000'; // 确保模态框在最前面
    modal.style.cursor = 'pointer'; // 设置鼠标样式为指针，表明可以点击关闭

    // 创建图片元素
    const img = document.createElement('img');
    img.src = imageUrl;
    img.style.maxWidth = '90%'; // 限制图片的最大宽度为90%
    img.style.maxHeight = '90%'; // 限制图片的最大高度为90%
    img.style.objectFit = 'contain'; // 保持图片的比例

    // 将图片添加到模态框
    modal.appendChild(img);

    // 将模态框添加到页面
    document.body.appendChild(modal);

    // 点击模态框外部关闭
    modal.addEventListener('click', function () {
        document.body.removeChild(modal);
    });

    // 防止点击图片时关闭模态框
    img.addEventListener('click', function (event) {
        event.stopPropagation(); // 阻止点击事件冒泡，避免触发模态框关闭事件
    });
}


function addMaid(text) {
    // 创建一个新的 div 元素
    text = text.replace(/^ermaid\s*/, '').trim();
    text = text.replace(/^maid\s*/, '').trim();
    const div = document.createElement('div');
    div.className = 'mermaid'; // Mermaid 的特殊类名，用于渲染流程图
    div.innerHTML = text; // 将流程图内容放入 div 中
    // 将创建的 div 添加到 messageContainer 中
    messageContainer.appendChild(div);
    // 初始化 Mermaid
    mermaid.initialize({ startOnLoad: true });
    // 渲染所有 Mermaid 图表
    mermaid.contentLoaded();
}

function RemoveAndShow(){
    new_text=currentText
    console.log('new_text.new_text :',new_text)
    // 更新聊天框
    let htmlContent = marked.parse(new_text);
    htmlContent = htmlContent.replace(/<strong>(.*?)<\/strong>：/g, '<strong>$1：</strong>'); // 把“：”放到 <strong> 内
    renewChatBox(htmlContent);
    add_el_listener('.clickable-number')
}

function addFilesToChatBox(fileList) {
    const chatBox = document.getElementById('chat-box');
    const fileDivArea = document.createElement('div');
    fileDivArea.className = "chat-fileshowdiv"; // 根据类型应用样式
    // 遍历文件列表
    fileList.forEach(file => {
        // 创建外层 div
        const fileDiv = document.createElement('div');
        fileDiv.className = "file-display"; // 根据类型应用样式
        fileDiv.style.display = 'flex';
        fileDiv.style.marginBottom = '0px'; // 消息底部留间距
        fileDiv.style.width = 'auto'; // 自适应宽度
        fileDiv.style.padding = '13px 13px'; // 自适应宽度
        fileDiv.style.flexShrink = '0';

        // 创建文件图标
        const fileIcon = document.createElement('img');
        fileIcon.src = '/static/images/file.png'; // 替换为文件图标路径
        fileIcon.alt = 'file icon';
        fileIcon.className = 'file-icon';
        fileIcon.style.display = 'block';

        // 创建内容区域 div
        const fileContent = document.createElement('div');
        fileContent.className = 'file-content';
        console.log("文件是",file)
        // 创建文件名和文件类型 div
        const fileNameDiv = document.createElement('div');
        fileNameDiv.className = 'file-name';
        fileNameDiv.textContent = getTruncatedFileName(file.filename)

        const fileTypeDiv = document.createElement('div');
        fileTypeDiv.className = 'file-type';
        fileTypeDiv.id = file.type;
        fileTypeDiv.textContent = `${mimeTypeMap[file.filetype]}, ${formatSize(file.filesize)}` || '未知类型';
        fileTypeDiv.style.display = 'block';

        // 将子元素组合到父元素
        fileContent.appendChild(fileNameDiv);
        fileContent.appendChild(fileTypeDiv);
        fileDiv.appendChild(fileIcon);
        fileDiv.appendChild(fileContent);

        // 添加到容器中
        fileDivArea.appendChild(fileDiv);
    }); 

    const previousElement = FileContainer.previousElementSibling;
    
    // 如果上方有元素，则设置 margin-top
    if (previousElement) {
        FileContainer.style.marginTop = '50px'; // 可以根据需要调整这个值
    }

    FileContainer.appendChild(fileDivArea);
    // 滚动到最新消息
    chatBox.scrollTop = chatBox.scrollHeight;
}



let upload_file = []
let finish_file = []
let ng_file = []
let allowedExtensions = []
const maxSize = 30 * 1024 * 1024; // 30MB
let seenFiles = new Set(); // 用来追踪已经遇到的文件（通过文件名和大小判断）
const fileContainer = document.getElementById('filediv'); // 获取目标容器 div

function get_history_file(){
    // 使用fetch API提交数据到服务器
    fetch(`${window.location.protocol}//${window.location.host}/kdb/get_session_file`, {
        method: 'POST',
        credentials: 'include', // 发送 cookie
        headers: {
            'Content-Type': 'application/json' // 设置请求体的内容类型为 JSON
        },
        body: JSON.stringify({session_id: session_id}) // 将对象转为 JSON 字符串s
    })
    .then(response => response.json())
    .then(data => {
        // 3. 将文件名添加到 Set 中
        data.forEach(fileName => {
            seenFiles.add(fileName);  // Set 会自动去重
        });
    })
    .catch((error) => {
        console.log("error")
    });
}

get_history_file()

function get_permissions(){
    // 使用fetch API提交数据到服务器
    fetch(`${window.location.protocol}//${window.location.host}/kdb/upload_get_allowedExtensions`, {
        method: 'POST',
        credentials: 'include', // 发送 cookie
        headers: {
            'Content-Type': 'application/json' // 设置请求体的内容类型为 JSON
        }
    })
    .then(response => response.json())
    .then(data => {
        allowedExtensions = data.allowedExtensions
    })
    .catch((error) => {
        console.log("error")
    });
}

get_permissions()

function deleteFile(fileId, file_name, session_id) {
    fetch(`/kdb/deleteFile?file_id=${fileId}&file_name=${file_name}&session_id=${session_id}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(result => {
        const fileDiv = document.querySelector(`[data-file-id="${fileId}"]`);
        if (fileDiv) {
            // 从 DOM 中移除对应的 div
            fileContainer.removeChild(fileDiv);
        }

        if (!result.success) {
            showPopup(`${resources.file}${file_name}${resources.delete_low}${resources.fail}！`)
        }
    })
    .catch(error => {
        const fileDiv = document.querySelector(`[data-file-id="${fileId}"]`);
        if (fileDiv) {
            // 从 DOM 中移除对应的 div
            fileContainer.removeChild(fileDiv);
        }
        
        showPopup(resources.delete_file_mes);
        return false;
    });
}

async function displayUploadedFile(files) {
    // 线上传文件
    let formData = new FormData();
  
    files.forEach(file => {
        const fileId = `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        // 创建外层 div
        const fileDiv = document.createElement('div');
        fileDiv.className = 'file-display';
        fileDiv.setAttribute('contenteditable', 'false');
        fileDiv.setAttribute('data-file-id', fileId);

        formData.append('files', file);
        formData.append('fileIds', fileId);

        // 创建删除按钮
        const deleteImg = document.createElement('img');
        deleteImg.src = '/static/images/delete2.png';  // 设置图片路径
        deleteImg.alt = 'Delete'; // alt 属性
        deleteImg.className = 'uploadfiledel';  // 为图片添加类名
        deleteImg.style.display = "none";
        deleteImg.addEventListener('click',  (event) => {
            event.preventDefault();
            deleteFile(fileId, file.name, session_id) // 使用 then 处理删除文件
            seenFiles.delete(file.name);
        });

        // 创建 img 元素，假设默认图片为文件图标
        const fileIcon = document.createElement('img');
        fileIcon.src = '/static/images/file.png'; // 替换为你的文件图标路径
        fileIcon.alt = 'file icon';
        fileIcon.className = 'file-icon';
        fileIcon.style.display = "none"

        const overlay = document.createElement('div');
        overlay.className = 'file-overlay';

        // 创建内容区域 div
        const fileContent = document.createElement('div');
        fileContent.className = 'file-content';

        // 创建文件名和文件类型 div
        const fileNameDiv = document.createElement('div');
        fileNameDiv.className = 'file-name';
        fileNameDiv.id = file.name
        fileNameDiv.textContent = getTruncatedFileName(file.name)

        const fileTypeDiv = document.createElement('div');
        fileTypeDiv.className = 'file-type';
        fileTypeDiv.id = file.type;
        fileTypeDiv.dataset.size = file.size; // 设置 data-size 属性
        fileTypeDiv.textContent = `${mimeTypeMap[file.type]}, ${formatSize(file.size)}` || '未知类型';
        
        const fileProgressDiv = document.createElement('div');
        fileProgressDiv.className = 'file-prg';
        // 上传中 -》 分析中 -》 TXT， 大小
        fileProgressDiv.textContent = "上传中";

        // 将子元素组合到父元素
        fileContent.appendChild(fileNameDiv);
        fileContent.appendChild(fileTypeDiv);
        fileContent.appendChild(fileProgressDiv);

        fileDiv.appendChild(overlay); // 添加覆盖层
        fileDiv.appendChild(fileIcon);
        fileDiv.appendChild(fileContent);
        fileDiv.appendChild(deleteImg);
        // 添加到目标容器 div 中
        fileContainer.appendChild(fileDiv);
    });

    let upload_id = session_id
    formData.append('session_id', upload_id);  // 将 kdb_id 添加到 FormData

    // 发送上传和分析请求
    startAnalyzeFiles(formData, upload_id)
}

async function startAnalyzeFiles(formData, session_id) {
    setTimeout(() => uploadProgress(session_id), 1000);  // 延迟一秒
    const response = await fetch('/kdb/addNewUploadFile', {
        method: 'POST',
        body: formData
    });
}

async function uploadProgress(session_id) {
    try {
        const requestBody = { session_id: session_id };  // 查询进度的请求体
        const response = await fetch('/kdb/input_upload_check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();
        
        if (JSON.stringify(upload_file) !== JSON.stringify(data.saved_files)){
            let difference = data.saved_files.filter(item => !upload_file.includes(item));
            // 修改内容
            difference.forEach(fileId => {
                const fileDiv = document.querySelector(`[data-file-id="${fileId}"]`);
                // 获取其中的 fileTypeDiv
                const filecontent = fileDiv.querySelector('.file-content');
                const filepgr = filecontent.querySelector('.file-prg');
                // 修改 textContent
                filepgr.textContent = '分析中'; // 设置新的文本内容
            });

            upload_file = data.saved_files
        }

        // 根据名字展示图表
        if (JSON.stringify(finish_file) !== JSON.stringify(data.finish_file)){
            let difference = data.finish_file.filter(item => !finish_file.includes(item));
            // 修改内容
            difference.forEach(fileId => {
                const fileDiv = document.querySelector(`[data-file-id="${fileId}"]`);
                // 获取其中的 fileTypeDiv
                const filecontent = fileDiv.querySelector('.file-content');
                const filepgr = filecontent.querySelector('.file-prg');
                const filetype = filecontent.querySelector('.file-type');

                const fileimg = fileDiv.querySelector('.file-icon');
                const fileoverly = fileDiv.querySelector('.file-overlay');
                const deleteimg = fileDiv.querySelector('.uploadfiledel');
                fileoverly.style.display = "none";
                fileimg.style.display = "block";
                // 修改 textContent
                filepgr.style.display = "none";
                filetype.style.display = "block";
                deleteimg.style.display = "block";
            });
            
            finish_file = data.finish_file
        }

        // 根据名字展示图表
        if (JSON.stringify(ng_file) !== JSON.stringify(data.ng_file)){
            let difference = data.ng_file.filter(item => !ng_file.includes(item));
            difference.forEach(fileId => {
                const fileDiv = document.querySelector(`[data-file-id="${fileId}"]`);
                // 查找 class="file-content" 下的 class="file-name" 的 div 元素
                const fileNameDiv = fileDiv.querySelector(".file-content .file-name");

                // 获取 file-name div 的 id 属性值
                const fileNameDivId = fileNameDiv ? fileNameDiv.id : null;
                if (fileDiv) {
                    fileDiv.remove(); // 删除元素
                    seenFiles.delete(fileNameDivId);
                }
            })
            ng_file = data.ng_file
        }

        if (!data.no_task) {
            setTimeout(() => uploadProgress(session_id), 1000);  // 每秒查询一次
        }
    } catch (error) {
        console.log("分析错误:",error)
    }
}

document.getElementById('fileInput').addEventListener('change', function(event) {
    const fileInput = event.target; // 当前触发事件的 input
    const files = fileInput.files; // 获取文件列表

    // 检查是否选择了文件
    if (!files.length) {
        return;
    }

    // 使用 Array.from() 创建一个可操作的数组
    const validFiles = Array.from(files).filter(file => {
        const fileSizeValid = file.size > 0 && file.size <= maxSize; // 检查文件大小
        const fileExtension = file.name.split('.').pop().toLowerCase(); // 提取文件后缀名
        const extensionValid = allowedExtensions.includes(fileExtension); // 检查后缀名是否有效

        if (!fileSizeValid) {
            showPopup(resources.file_size_zero)
        }
        if (!extensionValid) {
            showPopup(resources.file_type_mes)
        }

        return fileSizeValid && extensionValid; // 仅保留大小和后缀名都合法的文件
    });

    // 去除重复文件，只保留首次出现的文件
    const uniqueFiles = [];
    validFiles.forEach(file => {
        const fileKey = `${file.name}`; // 使用文件的名字和大小作为唯一标识
        if (!seenFiles.has(fileKey)) {
            uniqueFiles.push(file); // 如果文件未出现过，则添加到 uniqueFiles 数组中
            seenFiles.add(fileKey); // 将文件标记为已出现
        } else {
            showPopup(`${resources.file} ${file.name} ${resources.file_duplicate}`)
        }
    });

    if (uniqueFiles.length === 0) {
        fileInput.value = ''; // 清空文件选择框
        return;
    }    
    // 重置文件输入框，允许重新选择相同的文件
    event.target.value = '';  
    displayUploadedFile(uniqueFiles); // 调用显示函数
});


async function checkToken() {
    try {
        const response = await fetch('/check-token', {
            method: 'GET',
            credentials: 'include', // 确保发送 Cookies
        });

        if (response.ok) {
            const data = await response.json();
            console.log("Token is valid:", data.message);
        } else {
            console.warn("Token has expired or is invalid.");
            // 在这里处理 Token 过期的逻辑，例如跳转到登录页
            window.location.href = '/login';
        }
    } catch (error) {
        console.error("Error checking token:", error);
    }
}

// 显示弹窗函数
function showPopup(message) {
    const popup = document.getElementById('popup');
    const popupMessage = document.getElementById('popup-message');
    popupMessage.textContent = message;
    popup.style.opacity = '1'; // 显示弹窗
    popup.style.display = 'flex';
    
    // 5 秒后自动隐藏弹窗
    setTimeout(() => {
        popup.style.opacity = '0';
        setTimeout(() => popup.style.display = 'none', 200); // 等待动画结束后隐藏
    }, 3000);
}

// 关闭弹窗函数
function closePopup() {
    const popup = document.getElementById('popup');
    popup.style.opacity = '0';
    setTimeout(() => popup.style.display = 'none', 200); // 等待动画结束后隐藏
}
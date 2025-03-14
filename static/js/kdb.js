// 绑定点击事件以显示图表
show_graph_btn.addEventListener('click', function() { 
    graphContainer = document.getElementById('graphContainer')
    const buttonText = show_graph_btn.querySelector(".button-text");
    const show_graph_content = resources['show_graph']
    const close_graph_content = resources['close_graph']
    if (buttonText.textContent === show_graph_content) {
        if(!isChartVisible){
            const requestBody = { kdb_id: kdb_id }; // 创建一个包含 kdb_id 的对象
            // 展示图谱
            fetch(srv_url+`/graphrag/local_data`, {
                method: 'POST',
                credentials: 'include', // 发送 cookie
                headers: {
                    'Content-Type': 'application/json' // 设置请求体的内容类型为 JSON
                },
                body: JSON.stringify(requestBody) // 将对象转为 JSON 字符串
            })
            .then(response => response.json())
            .then(datas => {
                if (datas.is_show){
                    // 显示图表和信息框的容器
                    graphContainer.style.display = 'flex'; // 设置为 flex 以便并排显示
                    showGraph(datas); // 调用绘制图表的函数
                    buttonText.textContent = close_graph_content; // 改变按钮文字
                    isChartVisible = true
                }else{
                    showAlert(resources["show_graph_message"]+"！")
                }
            })
            .catch(error => console.error('Error:', error));
        }else{
            graphContainer.style.display = 'flex'; // 设置为 flex 以便并排显示
            buttonText.textContent = close_graph_content; // 改变按钮文字
        }
    } else {
        // 关闭图谱
        graphContainer.style.display = 'none';         // 隐藏图表
        buttonText.textContent = show_graph_content; // 改变按钮文字
    }

});

rebuild_graph_btn.addEventListener('click', function() { 
    //检查是否有新增文件
    check_start();
});

// 当点击“是”按钮时的操作
graphrag_yes_btn.addEventListener('click', async function() {
    confirmationModal.style.display = 'none';
    startRebuiltGraph()
    showAlert(resources["is_building_graph"]);
});

// 当点击“否”按钮时的操作
graphrag_no_btn.addEventListener('click', function() {
    confirmationModal.style.display = 'none';
    showAlert(resources["upload_new_file"],isError=true);
});

dropArea.addEventListener('click', () => {
    if (submitBtn.disabled) {
        showAlert(resources["analyzing_file"]+"...");
    } else {
        fileInput.click();
    }
});

fileInput.addEventListener('change', handleFiles, false);

dropArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    if (!submitBtn.disabled) {
        dropArea.classList.add('active');
    } else {
        showAlert(resources["analyzing_file"]+"...");
    }
});

dropArea.addEventListener('dragleave', (e) => {
    e.preventDefault();
    if (!submitBtn.disabled) dropArea.classList.remove('active');
});

dropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    if (submitBtn.disabled) {
        showAlert(resources["analyzing_file"]+"...");
    } else {
        dropArea.classList.remove('active');
        let dt = e.dataTransfer;
        let files = dt.files;
        fileInput.files = files;
        handleFiles();
    }
});

uploadBtn.addEventListener('click', function() {
    if (submitBtn.disabled) {
        showAlert(resources["analyzing_file"]+"...");
    } else {
        fileInput.click();
    }
});

uploadForm.addEventListener('submit', function(event) {
    event.preventDefault();
    let formData = new FormData(uploadForm);
    // 获取文件输入的字段
    let fileInput = uploadForm.querySelector('input[type="file"]');

    // 判断文件输入是否有文件
    if (!fileInput.files.length) {
        showAlert(resources["please_upload_file"] + "!" ,true)
        return;  // 如果没有文件，退出
    }
    // 判断是否是符合上传文件的格式
    formData.append('kdb_id', kdb_id);  // 将 kdb_id 添加到 FormData
    submitBtn.classList.add("disabled")
    submitBtn.disabled = true;
    const buttonText = submitBtn.querySelector(".button-text");
    buttonText.textContent = resources["uploading"]
    upload_spinner.style.display = "inline-block";
    reanalyze_btn.classList.add("disabled")
    reanalyze_btn.disabled = true;
    choice_file_btn.classList.add("disabled")
    choice_file_btn.disabled = true;
    // 禁止点击移除文件的按钮
    document.querySelectorAll('.file-delete-btn').forEach(button => {
        button.classList.add("disabled")
        button.disabled = true; // 禁用按钮
    });

    rebuildBtn.classList.add("disabled")
    rebuildBtn.disabled = true;
    showAlert(resources["upload_mes"]+"!",false,false,"uploading_mes");
    // 调用上传文件的函数
    uploadFiles(formData);
});


rebuildBtn.addEventListener('click', async function() {
    await rebuildKnowledgeBase();
});

fileInput.addEventListener('change', handleFiles, false);

function getUniqueFileName(fileName, existingFiles) {
    // 分离文件名和扩展名
    const namePattern = /(.*?)(\((\d+)\))?(\.[^.]+)?$/;
    const match = fileName.match(namePattern);

    let baseName = match[1]; // 文件名的主体部分
    let number = match[3] ? parseInt(match[3], 10) : 0; // 括号中的数字
    let extension = match[4] || ""; // 文件扩展名

    let newFileName = fileName;
    while (existingFiles.includes(newFileName)) {
        number += 1;
        newFileName = `${baseName}(${number})${extension}`;
    }
    return newFileName;
}

// 处理上传的文件
function handleFiles() {
    if (submitBtn.disabled) {
        showAlert(resources["analyzing_file"]+"...");
        return; // 如果按钮被禁用，直接返回
    }
    let files = fileInput.files;

    const validFiles = [];  // 用于存储符合要求的文件

    // 获取当前上传的文件
    const currentFiles = Array.from(files);

    // 遍历当前上传的文件，筛选符合要求的文件
    for (let i = 0, len = currentFiles.length; i < len; i++) {
        let file = currentFiles[i];
        let fileName = file.name;
        let fileExtension = fileName.split('.').pop().toLowerCase();


        // 检查文件大小是否为 0
        if (file.size === 0) {
            showAlert(resources["file"] + ":" + fileName + " " + resources["upload_file_size_0"], true);
            continue; // 跳过大小为 0 的文件
        }

        // 检查是否云端已经有该文件
        if (exitst_file_upload.includes(fileName)) {
            showAlert(resources["ex_file"],true)
            let uniqueFileName = getUniqueFileName(fileName, exitst_file_upload);
            console.log("重复后新的文件名：",uniqueFileName)

            const renamedFile = new File([file], uniqueFileName, {
                type: file.type,
                lastModified: file.lastModified,
            });
    
            validFiles.push(renamedFile); // 添加到有效文件数组
            exitst_file_upload.push(uniqueFileName); // 更新文件名记录
            continue;
        }

        if (allowedExtensions.includes(fileExtension)) {
            validFiles.push(file);  // 符合条件的文件添加到 validFiles 数组
        } else {
            showAlert(resources["file"] +":"+ fileName +" "+ resources["type_to_allow"] +":" + allowedExtensions.join(', '),true)
        }

    }

    // 将新的有效文件添加到已上传的文件列表中
    uploadedFiles = [...uploadedFiles, ...validFiles];

    // 更新 fileInput.files 为所有上传的文件
    let dataTransfer = new DataTransfer();
    uploadedFiles.forEach(file => {
        dataTransfer.items.add(file); // 将文件添加到新的 FileList
    });
    fileInput.files = dataTransfer.files; // 更新 fileInput.files

    // 更新文件展示
    displayUploadingFiles();
}

// 显示所有上传的文件，并为每个文件添加删除按钮
function displayUploadingFiles() {
    uploadingFilesList.innerHTML = '';  // 清空当前显示的文件列表

    // 遍历上传的所有文件并显示
    uploadedFiles.forEach((file, index) => {
        let li = document.createElement('li');
        li.innerText = file.name;

        // 创建删除按钮
        let deleteButton = document.createElement('button');
        deleteButton.innerText = resources["remove"];
        deleteButton.className = 'file-delete-btn';  // 可加样式

        // 添加删除按钮点击事件
        deleteButton.addEventListener('click', function() {
            removeFile(index);
        });

        // 将删除按钮添加到列表项中
        li.appendChild(deleteButton);
        uploadingFilesList.appendChild(li);
    });
}

// 从上传文件列表中删除文件
function removeFile(index) {
    const fileName = uploadedFiles[index].name; // 获取文件名
    const index_ex = exitst_file_upload.indexOf(fileName); // 查找文件名的索引
    if (index_ex !== -1) {
        exitst_file_upload.splice(index_ex, 1); // 移除该文件名
    }
    // 删除指定索引的文件
    uploadedFiles.splice(index, 1);

    // 更新 fileInput.files 为新的文件列表
    let dataTransfer = new DataTransfer();
    uploadedFiles.forEach(file => {
        dataTransfer.items.add(file); // 将剩余文件加入新的 FileList
        
    });
    fileInput.files = dataTransfer.files; // 更新 fileInput.files
    // 更新文件展示
    displayUploadingFiles();
}


async function startAnalyzeFiles(kdb_id, prompt_name, if_use_muilt, file_names) {
    setTimeout(() => uploadProgress(kdb_id), 1000);  // 延迟一秒

    const requestBody = {
        kdb_id: kdb_id , prompt_name: prompt_name, if_use_muilt: if_use_muilt, file_names: file_names
    }

    const response = await fetch(srv_url+'/kdb/analyze_files', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    });
}

function uploadFiles(formData) {
    fetch(srv_url+'/kdb/upload_files', {
        method: 'POST',
        body: formData,
        credentials: 'include' // 确保发送 cookie
    })
    .then(response => response.json())
    .then(data => {
        display_showAlert("uploading_mes")
        if(data.file_names){
            analyzing_files = data.file_names
        }
        refreshFileList();
        if(data.no_upload){
            showAlert(data.message,true); // Update status to "Upload successful"
        }else{
            showAlert(data.message); // Update status to "Upload successful"
            const buttonText = submitBtn.querySelector(".button-text");
            buttonText.textContent = resources["analyzing"]
            // 开始分析文件
            startAnalyzeFiles(kdb_id, prompt_name, if_use_muilt, data.file_names)      
        }
    })
    .catch(error => {
        console.error('Error:', error);
        submitBtn.className.remove("disabled")
        const buttonText = submitBtn.querySelector(".button-text");
        buttonText.textContent = resources["analyzed"]
        submitBtn.disabled = false; // Enable the upload button
        upload_spinner.style.display = "none";
        fileInput.value = ''; // Clear the file input
        uploadingFilesList.innerHTML = ''; // Clear the uploading files list
    });
}



function refreshFileList() {
    const requestBody = { kdb_id: kdb_id }; // 创建一个包含 kdb_id 的对象

    fetch(`${srv_url}/kdb/files`, {
        method: 'POST',
        credentials: 'include', // 发送 cookie
        headers: {
            'Content-Type': 'application/json' // 设置请求体的内容类型为 JSON
        },
        body: JSON.stringify(requestBody) // 将对象转为 JSON 字符串
    })
    .then(response => response.json())
    .then(files => {
        existingFilesList.innerHTML = '';
        exitst_file_upload = files
        files.forEach(file => {
            let li = document.createElement('li');
            li.id = file
            li.className = "file-li"
            // 创建一个显示文件名的 <span> 元素
            let fileName = document.createElement('span');
            fileName.innerText = file;
            // 只为文件名添加悬停手势
            fileName.style.cursor = 'pointer';  // 设置鼠标悬停时为指针形状
    
            // 为文件名添加点击事件
            fileName.addEventListener('click', function(event) {
                event.stopPropagation();  // 阻止事件冒泡，防止触发 li 的点击事件
                downloadFile(kdb_id, file, true);  // 调用下载函数
            });
        
            li.appendChild(fileName);  // 将文件名添加到 <li> 中

            if (is_from_share !== "True"){
                // 创建图片元素
                let img = document.createElement('img');
                img.src = '/static/images/finish_an.png';
                img.alt = 'Completed Item';
                img.className = 'finish-analyze-img';

                if (Array.isArray(finish_file) && finish_file.length > 0){
                    if(finish_file.includes(file)){
                        img.style.display = "flex";
                    }
                }   

                li.appendChild(img);

                let deleteBtn = document.createElement('button');
                deleteBtn.className = 'delete-btn'
                deleteBtn.innerText = resources["delete"];
                deleteBtn.onclick = function(event) { 
                    event.stopPropagation();  // 阻止事件冒泡
                    deleteFile(kdb_id, file); 
                };

                if (Array.isArray(analyzing_files) && analyzing_files.length > 0){
                    if(analyzing_files.includes(file)){
                        deleteBtn.classList.add("disabled")
                        deleteBtn.disabled = true;
                    }
                }   
                
                li.appendChild(deleteBtn);
            }

            existingFilesList.appendChild(li);
        });
    })
    .catch(error => console.error('Error:', error));
}



function refreshResFileList() {
    const requestBody = { kdb_id: kdb_id, path_dir: now_dir}; // 创建一个包含 kdb_id 的对象

    fetch(`${srv_url}/kdb/res_files`, {
        method: 'POST',
        credentials: 'include', // 发送 cookie
        headers: {
            'Content-Type': 'application/json' // 设置请求体的内容类型为 JSON
        },
        body: JSON.stringify(requestBody) // 将对象转为 JSON 字符串
    })
    .then(response => response.json())
    .then(files => {
        const keys = Object.keys(files);
        const filteredKeys = keys.filter(key => key === "" || !key.includes('/'));
        analyzed_files.innerHTML = '';
        for (const key of filteredKeys) {
            if(key === ""){
                if (now_dir.length) {
                    // 添加返回按钮
                    let backBtn = document.createElement('button');
                    backBtn.className = 'delete-btn'
                    backBtn.innerText = resources["return"];
                    backBtn.onclick = function(event) { 
                        event.stopPropagation();  // 阻止事件冒泡
                        now_dir.pop();
                        refreshResFileList()
                        
                    };                    
                    analyzed_files.appendChild(backBtn);
                }
                files[key].forEach(file => {
                    let li = document.createElement('li');
                    li.id = file
                    li.className = "file-li"
                    // 创建一个显示文件名的 <span> 元素
                    let fileName = document.createElement('span');
                    fileName.innerText = file;
                    // 只为文件名添加悬停手势
                    fileName.style.cursor = 'pointer';  // 设置鼠标悬停时为指针形状
            
                    // 为文件名添加点击事件
                    fileName.addEventListener('click', function(event) {
                        event.stopPropagation();  // 阻止事件冒泡，防止触发 li 的点击事件
                        downloadFile(kdb_id, file, false);  // 调用下载函数
                    });
                
                    li.appendChild(fileName);  // 将文件名添加到 <li> 中

                    let showBtn = document.createElement('button');
                    showBtn.className = 'delete-btn'
                    showBtn.innerText = resources["show"];
                    showBtn.onclick = function(event) { 
                        event.stopPropagation();  // 阻止事件冒泡
                        showResFile(kdb_id, file);
                        
                    };                    
                    li.appendChild(showBtn);
                    analyzed_files.appendChild(li);
                });
            }else{
                let li = document.createElement('li');
                li.id = key
                li.className = "file-li"
                // 创建一个显示文件名的 <span> 元素
                let fileName = document.createElement('span');
                fileName.innerText = key;
                // 只为文件名添加悬停手势        
                li.appendChild(fileName);  // 将文件名添加到 <li> 中

                let showBtn = document.createElement('button');
                showBtn.className = 'delete-btn'
                showBtn.innerText = resources["enter"];
                showBtn.onclick = function(event) { 
                    event.stopPropagation();  // 阻止事件冒泡
                    now_dir.push(key)
                    refreshResFileList()
                };                    
                li.appendChild(showBtn);
                analyzed_files.appendChild(li);
            }
        }
    })
    .catch(error => console.error('Error:', error));
}




function downloadFile(kdb_id, fileName, if_from_upload) {
    // 创建请求体数据
    const requestData = {
        kdb_id: kdb_id,
        path_dir: now_dir,
        filename: fileName,
        if_from_upload: if_from_upload
    };

    fetch(srv_url+"/kdb/download", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        // 将文件内容转为 Blob 对象
        return response.blob();
    })
    .then(blob => {
        // 创建一个 URL 对象，用于链接到下载的 Blob
        const url = window.URL.createObjectURL(blob);
        
        // 创建一个隐藏的 <a> 标签
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;  // 设置下载时的文件名
        document.body.appendChild(a); // 必须先添加到 DOM 才能触发下载
        
        // 模拟点击事件，触发下载
        a.click();
        
        // 下载完成后，清除创建的 URL 对象
        window.URL.revokeObjectURL(url);
        
        // 移除临时创建的 <a> 标签
        document.body.removeChild(a);
    })
    .catch(error => {
        console.error(resources["error"], error);
    });
}

function deleteFile(kdbId,fileName) {
    fetch(`${srv_url}/kdb/files/${kdbId}/${fileName}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        refreshFileList();
        refreshResFileList();
        showAlert(data.message)
        // 判断是否禁用rag按钮
        if(!data.rag_search){
            const RagButton = document.getElementById('rag_qa_btn');
            RagButton.classList.add("disabled");
            RagButton.disabled = true;

            rebuildBtn.classList.add("disabled");
            rebuildBtn.disabled = true;
            
            rebuild_graph_btn.classList.add("disabled");
            rebuild_graph_btn.disabled = true;
        }
    })
    .catch(error => {
        showAlert(data.message,true)
        console.error(resources["error"], data.message)
    });
}

function showResFile(kdbId,fileName){
    const requestData = {
        kdb_id: kdbId,
        path_dir: now_dir,
        filename: fileName
    };
    fetch(`${srv_url}/kdb/showResFile`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(file_content => {
        // 显示文件内容到模态窗口
        fileContentElement.textContent = file_content;

        // 显示模态窗口
        modalOverlay.style.display = 'flex';
    })
    .catch(error => {
        showAlert(data.message,true)
        console.error(resources["error"], data.message)
    });
}

// 点击关闭按钮时，隐藏模态窗口
closeButton.addEventListener('click', () => {
    modalOverlay.style.display = 'none';
  });

async function rebuildKnowledgeBase() {
    // 显示加载圈和禁用按钮
    spinner.style.display = "inline-block";
    rebuildBtn.disabled = true;
    rebuildBtn.classList.add('disabled-button'); // 添加禁用样式类

    const requestBody = { kdb_id: kdb_id }; // 创建一个包含 kdb_id 的对象

    fetch(srv_url+'/kdb/build', {
        method: 'POST',
        credentials: 'include', // 发送 cookie
        headers: {
            'Content-Type': 'application/json' // 设置请求体的内容类型为 JSON
        },
        body: JSON.stringify(requestBody) // 将对象转为 JSON 字符串s
    })
    .then(response => response.json())
    .then(data => {
        if(data.build){
            showAlert(data.message);
        }else{
            showAlert(data.message,true);
        }
        // 隐藏加载圈并重新启用按钮
        spinner.style.display = "none";
        rebuildBtn.disabled = false;
        rebuildBtn.classList.remove('disabled-button'); // 移除禁用样式类
    })
    .catch(error => console.error(resources["error"], error))
}


function display_showAlert(id) {
    const alertDiv_old = document.getElementById(id);
    if(alertDiv_old){
        alertDiv_old.remove();
    }
}

function showAlert(message, isError = false, timeout=true, show_id="alert_show_area") {
    const main_content = document.getElementById("main_content");
    let alertDiv = document.createElement('div');
    alertDiv.className = 'alert';
    alertDiv.id = show_id
    if (isError) {
        alertDiv.style.backgroundColor = '#f8df01'; // Red for errors
    }
    alertDiv.innerText = message;
    main_content.prepend(alertDiv);
    
    if(timeout){
        // 自动移除提示信息
        setTimeout(function() {
            alertDiv.remove();
        }, 3000);
    }
}

// 当页面加载完成时，刷新文件列表
window.onload = function () {
    refreshFileList();
    refreshResFileList();
};


function check_start(){
    const requestBody = { kdb_id: kdb_id }; // 创建一个包含 kdb_id 的对象
    fetch(srv_url+`/graphrag/check_res_file`, {
        method: 'POST',
        credentials: 'include', // 发送 cookie
        headers: {
            'Content-Type': 'application/json' // 设置请求体的内容类型为 JSON
        },
        body: JSON.stringify(requestBody) // 将对象转为 JSON 字符串s
    })
    .then(response => response.json())
    .then(data => {
        // 检查是可以下载
        if (data.error) {
            showAlert(resources["please_upload_file"]+"！",true)
        }else{
            if (data.start) {
                startRebuiltGraph()
            } else {
                confirmationModal.style.display = 'flex';
            }
        }
    })
    .catch(error => console.error(resources["error"], error))
}

async function startRebuiltGraph() {
    rebuild_graph_btn.classList.add('disabled'); // 添加禁用样式类
    rebuild_graph_btn.disabled = true
    const requestBody = { kdb_id: kdb_id }; // 创建一个包含 kdb_id 的对象

    const response = await fetch(srv_url+'/graphrag/start_rebuiltGraph', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    });

    const data = await response.json();

    // 检查是否存在 session_id
    if (!data.session_id) {
        // 如果没有 session_id，弹窗显示 message 内容
        showAlert(data.message,true);
    } else {
        // 存在 session_id，继续执行后续逻辑
        const sessionId = data.session_id;

        // 使用 { once: true } 确保事件只执行一次
        stopBtn.addEventListener('click', function() {
            stopDownload(sessionId);
        }, { once: true });
        stopBtn.style.display = 'inline'; // 显示停止按钮
        updateProgress(sessionId);
    }
}

async function updateProgress(sessionId) {
    progressBarShow.style.display = 'flex'
    progressBarText.style.display = 'block'
    graph_spinner.style.display = "inline-block";     // 显示加载圈和禁用按钮
    progressBarContainer.style.display = 'block';  // 显示进度条
    const requestBody = { kdb_id: kdb_id, session_id: sessionId }; // 创建一个包含 kdb_id 的对象
    const response = await fetch(srv_url+'/graphrag/progress', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    });

    const data = await response.json();
    if (!data.no_task){
        if (data.progress !== null) {
            progressBar.style.width = `${data.progress}%`;
            
            // 判断 data.progress 的类型
            if (typeof data.progress === 'number') { // 如果是 float
                progressBar.textContent = `${data.progress}%`; // 更新进度信息
                // 如果进度达到或超过100%，则停止更新
                if (data.progress >= 100) {
                    progressBarContainer.style.display = 'none';  // 隐藏进度条
                    stopBtn.style.display = 'none'; // 隐藏停止按钮
                    // 移除重建按钮禁用样式
                    rebuild_graph_btn.classList.remove('disabled'); // 移除禁用样式类
                    rebuild_graph_btn.disabled = false;
                    
                    progressBar.style.width = '0%'; // 重置进度条
                    progressBar.textContent = '0%'; // 重置文本内容

                    // 判断是否展示按钮为禁用
                    if (show_graph_btn.disabled) {
                        show_graph_btn.classList.remove('disabled'); // 添加禁用样式类
                        show_graph_btn.disabled = false;
                    }

                    const GraphRagButton = document.getElementById('grapgrag_qa_btn');
                    // 判断是否展示按钮为禁用
                    if (GraphRagButton.disabled) {
                        GraphRagButton.classList.remove('disabled'); // 添加禁用样式类
                        GraphRagButton.disabled = false;
                    }

                    //判断是否为第一次建立图谱
                    const buttonText = rebuild_graph_btn.querySelector('.button-text');

                    if (buttonText.textContent === resources["built_graphrag"]) {
                        buttonText.textContent = resources["rebuilt_graphrag"];
                    }

                    showAlert(resources["complete_build_graph"] +"!");
                    graph_spinner.style.display = "none";
                    progressBarText.style.display = "none";
                    progressBarShow.style.display = "none";
                    return; 
                }
            } else if (typeof data.progress === 'string') { // 如果是 str
                progressBarContainer.style.display = 'none';  // 隐藏进度条
                stopBtn.style.display = 'none'; // 隐藏停止按钮
                stopBtn.classList.remove("disabled")
                stopBtn.disabled = false

                progressBar.style.width = '0%'; // 重置进度条
                progressBar.textContent = '0%'; // 重置文本内容

                // 移除重建按钮禁用样式
                rebuild_graph_btn.classList.remove('disabled'); // 移除禁用样式类
                rebuild_graph_btn.disabled = false;

                progressBarText.style.display = "none";
                progressBarShow.style.display = "none";
                
                // 隐藏加载圈并移除禁用样式类
                graph_spinner.style.display = "none";

                // 判断是否可以点击graphrag_search
                const if_graphrag_search = graphrag_search_check(kdb_id)

                if(if_graphrag_search){
                    const GraphRagButton = document.getElementById('grapgrag_qa_btn');
                    GraphRagButton.classList.add("disabled")
                    GraphRagButton.disabled = true;
                }
                
                //判断是否为第一次建立图谱
                const buttonText = rebuild_graph_btn.querySelector('.button-text');

                if (buttonText.textContent === resources["built_graphrag"]) {
                    buttonText.textContent = resources["rebuilt_graphrag"];
                }

                showAlert(resources["stop_build_graph"]+"!");
                return; 
            }

            // 每秒钟更新一次进度
            setTimeout(() => updateProgress(sessionId), 1000);

        }
    }
}


function graphrag_search_check(graphrag_check_kdb){
    const requestBody = { kdb_id: graphrag_check_kdb}; // 创建一个包含 kdb_id 的对象
    fetch(srv_url+`/graphrag/stop_rebuiltGraph`, {
        method: 'POST',
        credentials: 'include', // 发送 cookie
        headers: {
            'Content-Type': 'application/json' // 设置请求体的内容类型为 JSON
        },
        body: JSON.stringify(requestBody) // 将对象转为 JSON 字符串s
    })
    .then(response => response.json())
    .then(data => {
        return data.graphrag_search
    })
    .catch(error => console.error(resources["error"], error))
}


function stopDownload(session_id) {
    const requestBody = { kdb_id: kdb_id, session_id: session_id }; // 创建一个包含 kdb_id 的对象
    fetch(srv_url+`/graphrag/stop_rebuiltGraph`, {
        method: 'POST',
        credentials: 'include', // 发送 cookie
        headers: {
            'Content-Type': 'application/json' // 设置请求体的内容类型为 JSON
        },
        body: JSON.stringify(requestBody) // 将对象转为 JSON 字符串s
    })
    .then(response => response.json())
    .then(data => {
        stopBtn.classList.add("disabled")
        stopBtn.disabled = true;
        showAlert(data.message);
    })
    .catch(error => console.error('Error:', error))
}

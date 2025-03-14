const mimeTypeMap = {
    // 文本文件类型
    "text/plain": "TXT",
    "text/markdown": "MD",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "XLSX",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "application/msword": "DOC",
    "application/pdf": "PDF",

    // 音频文件类型
    "audio/mpeg": "MP3",
    "audio/wav": "WAV",
    "audio/x-m4a": "M4A",
    "audio/flac": "FLAC",
    "audio/aac": "AAC",
    "audio/ogg": "OGG",
    "audio/opus": "OPUS",
    "audio/x-ms-wma": "WMA",

    // 演示文件类型
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PPTX",
    "application/vnd.ms-powerpoint": "PPT",

    // 图像文件类型
    "image/jpeg": "JPG",
    "image/png": "PNG",
    "image/webp": "WEBP",
    "image/x-canon-raw": "RAW",
};


function formatSize(size) {
    if (size < 1024) {
        return size + ' Bytes';
    } else if (size < 1024 * 1024) {
        return (size / 1024).toFixed(2) + ' KB';
    } else {
        return (size / (1024 * 1024)).toFixed(2) + ' MB';
    }
}


function getTruncatedFileName(fileName, maxWidth=120, maxIterations=50) {
    const ctx = document.createElement('canvas').getContext('2d'); // 创建一个 Canvas 用于测量文本宽度
    const dummyDiv = document.createElement('div'); // 用于获取字体样式
    dummyDiv.style.font = window.getComputedStyle(document.body).font; // 获取当前页面字体样式
    
    ctx.font = dummyDiv.style.font; // 使用文档的字体样式

    let file_name = fileName.substring(0, fileName.lastIndexOf('.')); // 去掉文件扩展名
    let truncatedName = file_name; // 初始文件名
    let ellipsis = '...';

    // 如果文件名超出容器宽度，截断并加上省略号
    if (ctx.measureText(file_name).width > maxWidth) {
        // 逐步去掉字符并检查宽度
        while (ctx.measureText(truncatedName + ellipsis).width > maxWidth && maxIterations > 0) {
            truncatedName = truncatedName.slice(0, -2); // 每次减少两个字符
            maxIterations--;
        }
        return truncatedName + ellipsis; // 添加省略号并返回结果
    } else {
        return file_name; // 文件名未超出宽度，返回完整文件名
    }
}

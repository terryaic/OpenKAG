// 获取输入框和按钮的引用
const sendButton = document.getElementById('sendButton');
const userInput = document.getElementById('userInput');
userInput.addEventListener('paste', function(e) {
    e.preventDefault();
    
    // 获取粘贴的 HTML 内容
    let html = e.clipboardData.getData('text/html');            
    // 如果粘贴内容是 HTML（并且不为空），清除 HTML 标签
    if (html) {
        let tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        // 获取纯文本
        let plainText = tempDiv.textContent || tempDiv.innerText;                
        // 保留换行符：将 HTML 中的 <br> 标签转换为换行符
        plainText = plainText.replace(/<br\s*\/?>/gi, '\n');  // 将 <br> 标签替换为换行符
        plainText = plainText.replace(/\r?\n/g, '\n');  // 确保所有换行符统一为 \n                
        // 插入纯文本，保持换行
        document.execCommand('insertText', false, plainText);
    } else {
        // 如果没有 HTML 内容（只有文本），直接粘贴
        let text = e.clipboardData.getData('text/plain');
        
        // 保留换行符
        text = text.replace(/\r?\n/g, '\n');  // 换行符统一为 \n

        console.log("输入的文本是",text)
        
        // 插入文本，保持换行
        document.execCommand('insertText', false, text);
    }
});

// 添加键盘事件监听器
userInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && event.shiftKey) {
        if (userInput.innerText.trim() === '') {
            // 如果没有内容，不插入 <br>
            event.preventDefault();
            return;
        }
        // 获取光标的位置
        const selection = window.getSelection();
        const range = selection.getRangeAt(0);
        const br = document.createElement('br');

        // 插入 <br> 换行符
        range.deleteContents();  // 删除当前选中的内容（如果有的话）
        range.insertNode(br);     // 插入 <br> 标签

        // 重新设置光标位置
        range.setStartAfter(br);
        range.setEndAfter(br);
        selection.removeAllRanges();
        selection.addRange(range);
    }
    else if (event.key === 'Enter' && !sendButton.disabled) {
        // 触发按钮点击的逻辑
        event.preventDefault();
        sendButton.click();
    }
});
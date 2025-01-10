
var domain = window.location.host;
//let srv_url = `http://${domain}/change_scene`;
//let ovserver = "omniverse://localhost"
let srv_url = `http://${domain}/change_scene`;
let ovserver = "omniverse://ovserver2.appincloud.cn"
function sendRequest(url) {
    if (url.startsWith("omniverse:") || url.startsWith("http")){
        //nothing
    }else{
        url = ovserver + url
    }
    const formData = new FormData();
    formData.append('url', url);
    // 使用 fetch API 发送异步请求
    fetch(srv_url, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        // 处理服务器响应的数据
    })
    .catch(error => {
        console.error('请求错误:', error);
    });
}
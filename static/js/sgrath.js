function showGraph(datas) {
    var nodes = datas.nodes;
    var links = datas.links;
    var unique_types = datas.unique_types;
    var symbolSize_inf = datas.symbolSize;

    // 获取滑块和显示值的元素
    var sliderControls = document.getElementById('sliderControls');
    var slider = document.getElementById('thresholdRange');
    var thresholdValue = document.getElementById('thresholdValue');

    // 更新显示的阈值
    thresholdValue.innerText = symbolSize_inf.init_show_size;
    // 设置滑块的最小值、最大值和当前值
    slider.min = symbolSize_inf.min_size;
    slider.max = symbolSize_inf.max_size;
    slider.value = symbolSize_inf.init_show_size;

    var myChart = echarts.init(document.getElementById('show_graph'));

    var categories = [];
    for (var i = 0; i < unique_types.length; i++) {
        categories[i] = {
            name: unique_types[i]
        };
    }

    // 初始阈值
    var threshold = symbolSize_inf.init_show_size;

    // 初始化时，过滤符合条件的节点
    function getFilteredNodesAndLinks(threshold) {
        var filteredNodes = nodes.filter(function (node) {
            return node.symbolSize >= threshold;
        });

        var filteredLinks = links.filter(function (link) {
            return filteredNodes.some(function (node) { return node.name === link.source; }) &&
                filteredNodes.some(function (node) { return node.name === link.target; });
        });

        return { filteredNodes, filteredLinks };
    }

    var { filteredNodes, filteredLinks } = getFilteredNodesAndLinks(threshold);


    var option = {
        title: {
            text: resources['graph_name']
        },
        tooltip: {
            formatter: function (x) {
                var description = x.data.des || '无描述';
                return '<div style="max-width: 300px; white-space: normal; word-wrap: break-word;">' + description + '</div>';
            }
        },
        toolbox: {
            show: true,
            feature: {
                mark: { show: true },
                restore: { 
                    show: true,
                    title: resources["restore"]
                },
                saveAsImage: { 
                    show: true,
                    title: resources["save_image"]
                }
            }
        },
        legend: [{
            data: categories.map(function (a) {
                return a.name;
            })
        }],
        series: [{
            type: 'graph',
            layout: 'force', // 可以尝试 'circular' 来避免重叠
            symbolSize: 40,
            roam: true,
            edgeSymbol: ['circle', 'arrow'],
            edgeSymbolSize: [2, 10],
            force: {
                repulsion: 5000, // 增加排斥力
                edgeLength: [50, 100],
                layoutAnimation: true, // 开启动画
                iterations: 300 // 增加迭代次数
            },
            draggable: true,
            lineStyle: {
                normal: {
                    width: 4,
                    color: '#4b565b',
                    type: 'solid'
                }
            },
            edgeLabel: {
                normal: {
                    show: true,
                    formatter: function (x) {
                        return x.data.name;
                    }
                }
            },
            label: {
                normal: {
                    show: true,
                    textStyle: {},
                    position: 'inside'
                }
            },
            data: filteredNodes,
            links: filteredLinks,
            categories: categories,
        }]
    };
    
    myChart.setOption(option);
    // 显示信息框
    sliderControls.style.display = 'flex';  // 显示滑块

    // 监听滑块控件的值变化
    var rangeInput = document.getElementById('thresholdRange');
    var thresholdValueLabel = document.getElementById('thresholdValue');

    rangeInput.addEventListener('input', function() {
        // 获取当前滑块值作为阈值
        threshold = parseInt(rangeInput.value);
        thresholdValueLabel.innerText = threshold;

        // 根据新阈值过滤节点和边
        var { filteredNodes, filteredLinks } = getFilteredNodesAndLinks(threshold);

        // 动态更新图表
        myChart.setOption({
            series: [{
                data: filteredNodes,
                links: filteredLinks
            }]
        });
    });

     // 点击节点事件处理
     myChart.on('click', function (params) {
        if (params.dataType === 'node') { // 确保点击的是节点
            // 更新信息区域内容
            showInfo(datas.entity_title,params.data.info, "");
        } 
        else if (params.dataType === 'edge') { // 检查是否点击了边
            showInfo(datas.relationship_title,params.data.info, ""); // 显示链接信息
        } 
    });
}


// 显示链接信息的函数
function showInfo(search_title, link, prefix="") {
    // 获取展示信息的区域，比如一个指定的 <div> 容器
    var infoBox = document.getElementById(`${prefix}infoBox`);
    var infoContent = document.getElementById(`${prefix}infoContent`);

    // 清空之前的内容
    infoContent.innerHTML = '';

    // 创建标题
    var title = document.createElement('h3');
    title.innerText = search_title;
    infoContent.appendChild(title);

    // 创建表格
    var table = document.createElement('table');
    table.style.width = '100%'; // 设置表格宽度为100%
    table.style.borderCollapse = 'collapse'; // 合并边框
    table.style.tableLayout = 'auto'; // 让列宽自动根据内容调整

    // 遍历字典中的键值对
    for (var key in link) {
        if (link.hasOwnProperty(key)) { // 确保是字典的自有属性
            // 创建一行 <tr>
            var row = document.createElement('tr');

            // 创建 <td> 单元格，显示键（key）
            var keyCell = document.createElement('td');
            keyCell.innerText = key;
            keyCell.style.border = '1px solid #ddd'; // 添加边框
            keyCell.style.padding = '8px'; // 添加内边距
            keyCell.style.fontWeight = 'bold'; // 键加粗
            keyCell.style.whiteSpace = 'nowrap'; // 防止内容折行

            // 创建 <td> 单元格，显示值（value）
            var valueCell = document.createElement('td');
            valueCell.innerText = link[key];
            valueCell.style.border = '1px solid #ddd'; // 添加边框
            valueCell.style.padding = '8px'; // 添加内边距

            // 将单元格添加到行
            row.appendChild(keyCell);
            row.appendChild(valueCell);

            // 将行添加到表格
            table.appendChild(row);
        }
    }

    // 将表格添加到 infoContent 中
    infoContent.appendChild(table);

    // 显示信息框
    infoBox.style.display = 'block'; // 显示信息框
}
    

function hideInfo() {
    var infoBox = document.getElementById('infoBox');
    infoBox.style.display = 'none'; // 隐藏信息框
}

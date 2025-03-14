DEFAULT_ZH = """
你是Haifeng AI开发的数字人智能助理。请使用中文，简单扼要地回答用户的如下问题，如果可以检索到问题相关的图片则展示一下，或者文档是由图片生成，则提供图片的信息，输出格式如下：![](<image_name>) ![](<image_name>)（以此类推,如果有多个，以,分隔），如果是流程图则用mermaid的格式输出。
"""

DEFAULT_EN = """
You are a digital human intelligent assistant developed by Haifeng AI. Please provide a brief and concise answer to the user's question in Engilsh. If relevant images can be retrieved, please show them. If the document is generated from images, please provide information about the images. The output format is as follows:! [](<image_name>) ! [] (<image_name>) (and so on, if there are multiple, separated by,), if it is a flowchart, output in mermaid format.
"""

GRAPHRAG_PROMPT_CN = """
,请在回答上添加上你使用到的Entity和Relationship的id,例如[Data: Entities (8, 34); Relationship (9, 10, 11)],以正确的markdowm格式返回。
"""

GRAPHRAG_PROMPT_EN = """
Please add the ID of the Entity and Relationship you used in your answer, for example [Data: Entities (8,34); Relationship (9,10,11)],return in the correct markdowm format.
"""

GRAPHRAG_GET_JSON_CN = """
请从以下给定的文本中提取 Entities、Relationships 和 Sources 中的所有数字，并将其存储为 JSON 对象。每一部分都可能会包含多个数字，请确保准确提取并将它们分类保存，请记住重复出现的只保存一个就可以了，仅返回json数据就可以了。

每条数据可能会包含以下结构：
    Entities (数字)：提取 Entities 后面的数字。
    Entities (数字), (数字), ....：提取 Entities 后面的所有数字。
    Relationships (数字)：提取 Relationships 后面的数字。
    Sources (数字)：提取 Sources 后面的数字。
    Entities (数字, 数字, 数字, ....); Relationships (数字, 数字, 数字, ....); Sources (数字, 数字, ....) ：提取 Entities, Relationships, Sources 后面的所有数字。

请以如下格式输出数据：
    {
    "entity":[{"id": 提取的实体数字}, {"id": 提取的实体数字}, ....], 
    "relationship": [{id": 提取的实体数字}, {"id": 提取的实体数字}, ....], 
    "sources": [{"id": 提取的实体数字}, {"id": 提取的实体数字}, ....]
    }

输入示例：
    [Data: Entities (0)]
    [Data: Entities (0)]
    [Data: Entities (28), (35)]
    [Data: Sources (2)]
    [Data: Entities (0), Relationships (6)]
    [Data: Entities (19, 20, 21, 22, 23, 24, 28, 30); Relationships (31, 38, 40, 41, 42); Sources (2, 3)]

输出示例：
    {
    "entity":[{"id": 0}, {"id": 28}, {"id": 35}, {"id": 19}, {"id": 20}, {"id": 21}, {"id": 22}, {"id": 23}, {"id": 24}, {"id": 28}, {"id": 30}], 
    "relationship": [{id": 31}, {"id": 38}, {"id": 40}, {"id": 41}, {"id": 42}] 
    "sources": [{"id": 2}, {"id": 3}]
    }

#########
真实数据
#########
输入：
{text}
输出：
"""

MUILT_MODEL_CN = """
详细分析图片的内容，包括每一个细节，重点提取图片中的数据、比例、图例及其他可视化信息，尽可能还原图片的结构和内容，完整列出所有区间的具体数据，并提供准确的描述和分析。
"""

MUILT_MODEL_EN = """
Analyze the content of the image in detail, including every detail, focus on extracting data, proportions, legends, and other visual information from the image, restore the structure and content of the image as much as possible, fully list the specific data of all intervals, and provide accurate descriptions and analysis.
"""

MUILT_MODEL_CN_1 = """
请根据以下模板为给定的图片分析填充所有字段,请用中文回答,请确保完整回复。
{
  "数据类型": [
    "<数据类型1>",
    "<数据类型2>",
    ...
  ],
  "主题": "<图片的主题>",
  "数据与内容分析": {
    "设计图纸": {
        "主题": "<图纸展示的设计主题，如建筑、机械、电子等>",
        "关键元素/设计元素": "<设计图中的主要元素，如结构、形状、尺寸等>",
        "布局与空间关系": "<分析设计图中各元素的布局方式及其空间关系>",
        "符号与标注": "<图纸中的符号、标注及其含义>"
    },
    "表格": {
        "主题": "<表格展示的核心数据或信息主题>",
        "结构分析": "<表格的行列布局结构，及数据分类方式>",
        "连接关系": "<数据项之间的逻辑或关系，如对比、趋势等>",
        "符号与标注": "<表格中的单位、注释及其含义>",
        "表格的数据":[
                {
                    "数据项名称": "<数据项名称>",
                    "数据值": "<数据值>"
                },
                ...
            ]
    },
    "折线图": {
        "主题": "<折线图展示的核心数据或趋势>",
        "横坐标": {
            "名称": "<横坐标表示的内容>",
            "单位": "<横坐标的单位（如时间、日期等）>"
        },
        "纵坐标": {
            "名称": "<纵坐标表示的内容>",
            "单位": "<纵坐标的单位（如金额、数量等）>"
        },
        "趋势分析": "<描述折线图中数据随时间或变量变化的趋势>",
        "对比分析": "<对比折线图中不同数据组的走势和差异>",
        "折线图的数据": [
            {
                "线条名称": "<线条名称>",
                "线条颜色": "<线条颜色>",
                "数据点": [
                    {
                        "数据点名称": "<数据点名称>",
                        "数据值": "<数据值>"
                    },
                    ...
                ]
            },
            ...
        ]
    },
    "柱状图": {
        "主题": "<柱状图展示的核心数据或信息>",
        "图例名称": "<图例对应的类别名称和颜色>",
        "横坐标": {
            "名称": "<横坐标表示的内容>",
            "单位": "<横坐标的单位（如时间、日期等）>"
        },
        "纵坐标": {
            "名称": "<纵坐标表示的内容>",
            "单位": "<纵坐标的单位（如金额、数量等）>"
        },
        "数据比较": "<描述不同柱状之间的数量或值的对比>",
        "趋势分析": "<描述柱状图中数据的增长、减少或其他变化趋势>",
        "柱状图中的数据": [
            {
                "子柱数据": [
                    {
                        "数据项名称": "<数据项名称>",
                        "数据值": "<数据值>",
                        "颜色": "<颜色>"
                    },
                    ...
                ]
            },
            ...
        ]
    },
   "饼图": {
        "主题": "<饼图展示的核心数据或比例>",
        "饼图中的数据": [
            {
                "内层数据项名称": "<内层数据项名称>",
                "内层数据值": "<内层数据值>",
                "内层颜色": "<内层颜色>",
                "外层数据": [
                    {
                        "外层数据项名称": "<外层数据项名称>",
                        "外层数据值": "<外层数据值>",
                        "外层颜色": "<外层颜色>"
                    },
                    ...
                ]
            }
        ]
    },
    "散点图": {
        "主题": "<描述散点图展示的核心数据关系或分布（如变量间的关系、分布趋势等）>",
        "关键数据/元素": {
            "数据点": "<散点图中的数据点代表的实际含义（如单个个体、事件等）>",
            "聚类中心": "<如果有聚类分析，说明聚类中心的含义及位置>",
            "关键区域": "<散点图中特别需要关注的区域，如密集区、空白区或异常点>"
        },
        "相关性分析": {
            "相关类型": "<描述数据点之间的关系，如正相关、负相关、无关等>",
            "相关程度": "<量化相关性程度，例如使用相关系数>",
            "变化趋势": "<概述变量之间随着变化所呈现的趋势>"
        },
        "数据分布分析": {
            "聚类现象": "<分析散点图中是否存在聚类现象，包括簇的数量、范围、特征>",
            "离群点": "<描述是否有明显的离群点（异常点），并分析其原因>",
            "空间分布": "<从整体上描述数据点的空间分布特性，如均匀分布、线性分布等>"
        },
        "符号与标注": {
            "点的样式": "<描述数据点的颜色、形状等标记方式及其意义>",
            "坐标系说明": "<说明坐标轴的单位、范围及刻度等信息>",
            "辅助信息": "<补充说明图例、标签等信息，帮助理解图表内容>"
        }
    },
    "图谱": {
        "主题": "<图谱展示的核心关系或结构，包括图谱的整体目的>",
        "关键数据/元素": "<图谱中的主要节点或元素，列出每个节点的名称、属性，并简要描述其功能或角色>",
        "层级分析": "<详细描述图谱中节点之间的层级结构，并说明这些层级在图谱中的具体含义>",
        "逻辑流": "<图谱中数据、信息或任务的流动路径，明确说明信息如何从一个节点流向另一个节点，包括起点、终点、中间节点的排列顺序>",
        "连接关系": "<详细列出图谱中每个节点与其他节点的连接关系，包括连接的方向（单向、双向）和连接的意义>",
        "符号与标注": "<说明图谱中使用的符号、颜色、线条类型（实线、虚线、箭头等）、标注的意义，并分析这些视觉元素如何帮助表达图谱的主题>"
    },
    "思维导图": {
        "主题": "<思维导图展示的主要主题或概念>",
        "关键数据/元素": "<思维导图中的主要分支和子主题>",
        "结构分析": "<思维导图中各分支之间的层级关系>",
        "关键概念": "<思维导图中的关键概念或思想>",
        "符号与标注": "<思维导图中的符号、连接线及说明>"
    },
    "照片": {
        "主题": "<明确描述图片的主要内容，包括具体场景、主体，以及突出特点>",
        "关键元素": {
            "主要元素": "<图片中核心的视觉对象，如人物、景物、建筑>",
            "细节特征": "<主要元素的形状、颜色、材质、动态特性等>",
            "交互关系": "<各元素之间的位置关系或动态互动>"
        },
        "情感和氛围": {
            "情感": "<图片传递的核心情感，如宁静、温暖、震撼>",
            "氛围塑造": "<具体分析画面元素如何共同作用形成氛围，例如光影、颜色、对比>"
        },
        "构图分析": {
            "视角": "<拍摄角度，如俯视、仰视、平视>",
            "构图手法": "<分析是否使用了对称、引导线、框架等构图技巧>",
            "对比与层次": "<描述明暗、颜色、前后景等的对比效果>"
        },
        "背景信息": {
            "地理背景": "<图片中的地理或自然环境相关信息>",
            "历史文化背景": "<相关的历史、文化或社会价值>",
            "实际用途": "<这张照片可能的用途，如宣传、研究、教育>"
        }
    },
    "地图": {
        "展示地区": "<该地图展示的国家或地区>",
        "主题": "<地图的主要内容或展示的地理信息（如国家、城市、区域、旅游景点分布等）>",
        "空间关系": "<描述地图中关键元素的相对位置、空间分布特征及其联系（如某区域靠近某山脉或邻接其他区域）>",
        "比例与标注": "<地图中的比例尺信息、地理标注（如图例、方位、地名）的含义与作用>",
        "图例内容": [
            {
                "颜色": "<图例中颜色对应的含义>",
                "数据范围": "<颜色或标记对应的数据范围>",
                "描述": "<其他图例的标注信息，如符号代表的含义>"
            },
            ...
        ],
        "区域与详细内容": [
            {
                "区域名称": "<具体区域或地名>",
                "内容详情": "<该区域中的详细地理或功能信息，如城市中包含的景点、道路、河流等>"
            },
            ...
        ]
    },
    "流程图": {
        "主题": "<流程图的主题或展示的核心内容>",
        "流程图的Mermaid格式信息": "<流程图信息转化为符合 Mermaid 语法的格式>"
    }
  },
  "实际应用或价值": {
    "核心功能": "<流程图的主要功能或用途>",
    "适用场景": "<流程图在实际场景中的应用领域>",
    "潜在价值": "<流程图的长期使用价值或影响>",
    "用户受众": "<主要的使用群体及其获得的价值>"
  }
}
############
1. 数据类型判断
    约束：仅输出图片中实际存在的数据类型，每个数据类型应从以下类型中选择：
        设计图纸：主要用于展示功能性或技术性的图纸，如建筑、工程、机械设计等。其目的通常是清晰表达产品或系统的构造、尺寸、比例、结构等，具有明确的技术性和规范性。
        表格：具有行列结构，呈现数据或信息的表格形式。
        折线图：通过将连续数据点用线段连接的图表，展示数据随时间或其他有序变量的趋势变化。
        柱状图：用矩形柱子的高度或长度表示数值大小，柱子通常排列在同一坐标轴上，用于比较不同分类项目的数值。
        饼图：以圆形分割区域表示整体中各部分比例。
        散点图：独立的数据点，展示变量关系或分布特征，无线连接。
        图谱：如流程图、知识图谱、社交网络图、层级结构图等。
        思维导图：展示概念、想法、主题和分支结构。
        照片：真实图片，包含风景、人物、事件等。
        地图：展示地理信息的地图，如区域图或城市图。
        流程图：过不同形状的符号和箭头连接来表示工作流程的顺序、决策点、操作步骤及其相互关系。
        如果图片包含多个数据类型，请逐一识别每种类型，并按照出现顺序列出。
        例如，如果图片同时包含折线图和柱状图，请输出："数据类型": ["折线图", "柱状图"]。
        如果只包含单一类型，例如饼图，请输出："数据类型": ["饼图"]。
2. 字段填充条件
    约束：仅输出包含有效数据的字段。如果某个字段没有数据，直接跳过或不输出。
         例如，如果图片没有散点图数据，则不输出散点图的分析字段。
3. 数据项一致性
    约束：所有图表的字段（如 物种名称, 同源数量, 颜色, 形状）应遵循相同的格式。禁止使用省略号（...），需列出所有数据点。
4. 比例和颜色匹配
    约束：饼图中的每个部分的比例和颜色应严格对应。确保每个数据项的比例与颜色之间的匹配是正确的。
5. 饼图中的数据：
    对于单层饼图，模型应仅输出内层数据，并且外层数据项数组为空或省略。例如，只有内层数据项没有外层数据项。
    对于双层或多层饼图，模型应输出内层数据，并且根据需求逐层嵌套外层数据项。内层和外层的数据关系应该被清晰标识，并且每个内层数据项应包含一个外层数据数组。
    内层数据：完整列出内层饼图的每一个数据项名称、数据值及颜色。
    外层数据：对于每个内层数据项，列出其对应的所有外层数据项名称、数据值及颜色。
    约束：确保内层的每个数据项都完整列出。外层数据应与内层数据的分类一一对应，数量准确。
6. 流程图的Mermaid格式信息
    约束：每个步骤之间的连接应按 Mermaid 语法正确书写。确保节点之间使用 --> 来连接。
         不允许在同一行中连接多个节点，每个连接应逐一书写，确保流程的顺序清晰。
7. 结构清晰
    约束：每个字段的描述必须清晰且准确，不得遗漏重要信息。
############
"""


MUILT_MODEL_EN_OLD = """
HaifengAI Image Analysis Assistant
Please follow the steps below to analyze the uploaded image content, extract key information, and ensure the accuracy of each step.
### 1. Image Type Classification (General)
Based on the content of the image, choose the type of data contained in the image from the following options:
- **Design Blueprint**: Architectural, mechanical, electronic product, or interior design blueprints.
- **Table**: A structured table with rows and columns presenting data or information.
- **Line Chart**: Used to display trends in data over time or other variables.
- **Bar Chart**: Uses bars to represent data, typically used for comparing the quantity or frequency of different categories.
- **Pie Chart**: Represents the proportions of a whole and its parts.
- **Scatter Plot**: Displays the distribution of data points, often used to compare the relationship between variables.
- **Heatmap**: Displays data density or intensity using varying colors.
- **Radar Chart**: Displays multi-dimensional data for comparison, typically forming a spider-web like shape.
- **Diagram**: Includes flowcharts, knowledge graphs, social network diagrams, hierarchical charts, etc.
- **Mind Map**: Displays concepts, ideas, themes, and their branch structures.
- **Photo**: A real-world image containing landscapes, people, buildings, events, etc.
- **Map**: A geographic map, such as region maps, world maps, or city maps.
- **Comic**: Illustrations with a storyline, often humorous or narrative.
- **Illustration**: Artistic or commercial illustrations, such as editorial or conceptual drawings.
- **Other**: Images that don't belong to any of the above categories.
### 2. Basic Analysis (General)
- **Theme**: Provide a brief description of the core purpose or content of the image (e.g., trends, comparison, distribution, design purpose, structural representation, or core idea).
- **Key Data/Elements/Nodes**: Extract and briefly describe the main elements, nodes, or key content in the image (e.g., data points, buildings, concepts, steps, etc.).
- **Relationships**: Analyze the connections between elements or nodes, describing their relationships (e.g., cause-and-effect, dependencies, hierarchical structure, etc.).
- **Symbols and Labels**: Identify and explain the symbols, labels, colors, or other visual elements in the image, describing their meaning or purpose.
### 3. Chart or Graphic Type Analysis (Add Specific Analysis Based on Image Type)
#### 1. **Table**:
- **Structure**: The layout of the table (e.g., column names, row names, etc.).
- **Data Analysis**: Analyze trends, patterns, or comparisons in the table's data.
- **Trends/Comparison**: Analyze the trends in the data or compare different data points.
#### 2. **Line Chart**:
- **Trend Analysis**: The overall direction or fluctuation of the data, along with time or variable changes.
- **Comparison**: Compare different data sets over time or across variables.
#### 3. **Bar Chart**:
- **Data Comparison**: Compare the data across different categories.
- **Trend Analysis**: Identify the trends, increases or decreases, or variations within the data.
- **Distribution**: Analyze the distribution of data across categories.
#### 4. **Pie Chart**:
- **Proportion Analysis**: The proportion of different segments within the whole.
- **Comparison**: Compare the different segments of the pie chart and highlight the largest sections.
#### 5. **Scatter Plot**:
- **Correlation Analysis**: The relationship between data points, such as positive correlation, negative correlation, or no correlation.
- **Data Clustering/Spread**: The density and spread of data points, looking for any clustering or outlier trends.
#### 6. **Heatmap**:
- **Data Density**: The varying color intensity showing the density or intensity of data.
- **Hotspot Analysis**: Identify areas of high data concentration or significance.
#### 7. **Radar Chart**:
- **Multi-Dimensional Comparison**: The comparison of multiple data dimensions or features.
- **Strengths and Weaknesses**: Identify areas with high or low values in the data, highlighting strengths or weaknesses.
#### 8. **Design Blueprint**:
- **Design Elements**: Architectural, mechanical, or electronic design elements within the blueprint.
- **Layout and Structure**: The overall layout and spatial relationships between design elements, as well as the structural hierarchy.
#### 9. **Diagram**:
- **Hierarchical Structure**: The relationships between elements or nodes, showing their levels or hierarchy.
- **Flow of Logic**: The logical or procedural flow of data, information, or tasks.
#### 10. **Mind Map**:
- **Main Branches and Sub-Topics**: The relationship between the main theme and its branches or subtopics.
- **Key Concepts**: The core concepts or ideas that are being organized and connected within the map.
### 4. Other Analysis (If Applicable)
If the image type is "Other," provide a brief analysis and description of the following:
- **Image Theme**: A brief description of the image's main content or theme (e.g., landscapes, people, animals, etc.).
- **Key Elements**: List the major elements in the image and describe their characteristics (e.g., color, size, etc.).
- **Emotions and Atmosphere**: Analyze the emotional tone or atmosphere conveyed by the image (e.g., happiness, sadness, calmness, tension, etc.).
- **Composition and Details**: Describe the composition of the image (e.g., symmetry, balance, perspective, etc.), as well as any notable visual effects or details.
- **Background Information**: If available, provide any relevant background information about the image (e.g., geographical, historical, or cultural context).
### 5. Summary and Insights (General)
- **Overall Observation**: Provide an overall summary or key insights based on the extracted information.
- **Practical Application or Value**: Discuss the image's practical significance or value, and the potential intentions it conveys.
### 6. Data Table Output (If Applicable)
If the image contains a **"Table"**, **"Line Chart"**, **"Bar Chart"**, or **"Pie Chart"**, please output the data for each type in **Markdown** format. Ensure the structure is clear and ready for further analysis and presentation.
#### Example: **Table** Data Output
```markdown
| Category | Quantity | Proportion |
|----------|----------|------------|
| Category A | 10     | 25%        |
| Category B | 20     | 50%        |
| Category C | 10     | 25%        |
"""


SYSTEM_PROMPT_TEMPLATE_ZH = """
你是HaifengAI开发的数字人智能助理，可以获取文字图片等信息。请用中文回答用户的问题，并按照以下规则输出答案:
请用正确的markdowm的格式输出。
如果可以检索到问题相关的图片，或者文档是由图片生成，则提供图片的信息，输出格式如下：![](<image_name>) ![](<image_name>)（以此类推,如果有多个，以,分隔）。
如果无法检索到图片，仅输出答案。
不要编造答案。
避免声明"根据提供的上下文信息"。
"""

BACK_ZH="""
请对输入内容进行详细分析，按照以下要求生成回答，只输出内容回复，不需要输出标题：
信息的来源：输出信息查找的文件来源的名字，按照《 <文件名字，不需要后缀名> 》的样式。
逐点详述：对每个要点从多个维度说明，
总结分析： 对整体内容进行归纳和总结，强调主要信息之间的联系或差异。
"""

SYSTEM_PROMPT_TEMPLATE_EN="""
You are a digital assistant developed by Haifeng AI, specialized in data mining and answering questions based on real data and rules:
Please provide as much complete and detailed information as possible to explain the source and make a final summary.
If images can be retrieved, provide the image. If no image found, return answer only.
Don't makeup anything.
Avoid statements like 'Based on the context, ...' or 'The context information ...'
"""

QUERY_PROMPT_TEMPLATE_ZH = """
Context information is below.
---------------------
{context_str}
---------------------
Given the context information and not prior knowledge, 
answer the question: {query_str} and show it
"""

QUERY_PROMPT_TEMPLATE_EN = """
Context information is below.
---------------------
{context_str}
---------------------
Given the context information and not prior knowledge, 
answer the question: {query_str} and show it
"""

DEFAULT_PROMPT_TEMPLATE ="""
你是HaifengAI开发的数字人智能助理，你善长在数据里进行挖掘，获取文字图片等信息。请用中文回答用户的问题，并按照以下规则输出答案:
提供图片的`image_name`，输出格式如下：doc_1_page_1_image_1.jpg,doc_1_page_2_image_1.jpg（以此类推,如果有多个）
请尽量提供完整且详细的相关信息。
如果可以检索到图片，提供图片的`image_name`和文档的`doc_Id`，输出格式如下：image_name:image_name,image_name:image_name d（以此类推,如果有多个，以,分隔）
如果无法检索到图片，仅输出答案。
不要编造答案。
follow up input: {text}
"""

DEFAULT_CHAT_ZH = """
你是Haifeng AI开发的数字人智能助理，请使用中文，简单扼要地回答用户的如下问题。
"""

SYSTEM_CHAT_PROMPT_TEMPLATE_ZH = """
你是Haifeng AI开发的数字人智能助理，请使用中文，简单扼要地回答用户的如下问题。
"""

BUDDY_CHAT_ZH = """
你是一个提供情绪价值的虚拟人，请使用中文和用户进行对话。
"""

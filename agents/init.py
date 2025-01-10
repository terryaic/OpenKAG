import json

import autogen
#放变量的
import os
config_list_path = os.path.join(os.path.dirname(__file__), 'model.json')
print(config_list_path)
config_list = autogen.config_list_from_json(env_or_file=config_list_path)

location="xian"
api_key='SjvnKcNWWZ3e9Pb6Q'
base_url = 'https://api.seniverse.com/v3/weather/daily.json'
airurl=f'https://api.seniverse.com/v3/air/now.json?key={api_key}&location={location}&language=zh-Hans&scope=all'
url=f'https://api.seniverse.com/v3/weather/daily.json?key={api_key}&location={location}&language=zh-Hans&unit=c&start=-1&days=5'

# 定义城市列表，去除“市”字
cities = {
    # 河北省
    "石家庄": "shijiazhuang",
    "张家口": "zhangjiakou",
    "承德": "chengde",
    "唐山": "tangshan",
    "秦皇岛": "qinhuangdao",
    "廊坊": "langfang",
    "保定": "baoding",
    "沧州": "cangzhou",
    "衡水": "hengshui",
    "邢台": "xingtai",
    "邯郸": "handan",

    # 山西省
    '上海':'shanghai',
    "太原": "taiyuan",
    "大同": "datong",
    "朔州": "shuozhou",
    "忻州": "xinzhou",
    "阳泉": "yangquan",
    "晋中": "jinzhong",
    "吕梁": "lvliang",
    "长治": "changzhi",
    "临汾": "linfen",
    "晋城": "jincheng",
    "运城": "yuncheng",

    # 内蒙古自治区
    "呼和浩特": "huhehaote",
    "呼伦贝尔": "hulunbeier",
    "通辽": "tongliao",
    "赤峰": "chifeng",
    "巴彦淖尔": "bayannaoer",
    "乌兰察布": "wulanchabu",
    "包头": "baotou",
    "鄂尔多斯": "eerduosi",
    "乌海": "wuhai",

    # 黑龙江省
    "哈尔滨": "haerbin",
    "黑河": "heihe",
    "伊春": "yichun",
    "齐齐哈尔": "qiqihaer",
    "鹤岗": "hegang",
    "佳木斯": "jiamusi",
    "双鸭山": "shuangyashan",
    "绥化": "suihua",
    "大庆": "daqing",
    "七台河": "qitaihe",
    "鸡西": "jixi",
    "牡丹江": "mudanjiang",

    # 吉林省
    "长春": "changchun",
    "白城": "baicheng",
    "松原": "songyuan",
    "吉林": "jilin",
    "四平": "siping",
    "辽源": "liaoyuan",
    "白山": "baishan",
    "通化": "tonghua",

    # 辽宁省
    "沈阳": "shenyang",
    "铁岭": "tieling",
    "阜新": "fuxin",
    "抚顺": "fushun",
    "朝阳": "chaoyang",
    "本溪": "benxi",
    "辽阳": "liaoyang",
    "鞍山": "anshan",
    "盘锦": "panjin",
    "锦州": "jinzhou",
    "葫芦岛": "huldiao",
    "营口": "yingkou",
    "丹东": "dandong",
    "大连": "dalian",

    # 江苏省
    "南京": "nanjing",
    "连云港": "lianyungang",
    "徐州": "xuzhou",
    "宿迁": "suqian",
    "淮安": "huaian",
    "盐城": "yancheng",
    "泰州": "taizhou",
    "扬州": "yangzhou",
    "镇江": "zhenjiang",
    "南通": "nantong",
    "常州": "changzhou",
    "无锡": "wuxi",
    "苏州": "suzhou",

    # 浙江省
    "杭州": "hangzhou",
    "湖州": "huzhou",
    "嘉兴": "jiaxing",
    "绍兴": "shaoxing",
    "舟山": "zhoushan",
    "宁波": "ningbo",
    "金华": "jinhua",
    "衢州": "quzhou",
    "台州": "taizhou",
    "丽水": "lishui",
    "温州": "wenzhou",

    # 安徽省
    "合肥": "hefei",
    "淮北": "huaibei",
    "亳州": "bozhou",
    "宿州": "suzhou",
    "蚌埠": "bengbu",
    "阜阳": "fuyang",
    "淮南": "huainan",
    "滁州": "chuzhou",
    "六安": "liuan",
    "马鞍山": "maanshan",
    "芜湖": "wuhu",
    "宣城": "xuancheng",
    "铜陵": "tongling",
    "池州": "chizhou",
    "安庆": "anqing",
    "黄山": "huangshan",

    # 福建省
    "福州": "fuzhou",
    "宁德": "ningde",
    "南平": "nanping",
    "三明": "sanming",
    "莆田": "putian",
    "龙岩": "longyan",
    "泉州": "quanzhou",
    "漳州": "zhangzhou",
    "厦门": "xiamen",

    # 江西省
    "南昌": "nanchang",
    "九江": "jiujiang",
    "景德镇": "jingdezhen",
    "上饶": "shangrao",
    "鹰潭": "yingtan",
    "抚州": "fuzhou",
    "新余": "xinyu",
    "宜春": "yichun",
    "萍乡": "pingxiang",
    "吉安": "jian",
    "赣州": "ganzhou",

    # 山东省
    "济南": "jinan",
    "德州": "dezhou",
    "滨州": "binzhou",
    "东营": "dongying",
    "烟台": "yantai",
    "威海": "weihai",
    "淄博": "zibo",
    "潍坊": "weifang",
    "聊城": "liaocheng",
    "泰安": "taian",
    "莱芜": "laiwu",
    "青岛": "qingdao",
    "日照": "rizhao",
    "济宁": "jining",
    "菏泽": "heze",
    "临沂": "linyi",
    "枣庄": "zaozhuang",

    # 河南省
    "郑州": "zhengzhou",
    "安阳": "anyang",
    "鹤壁": "hebi",
    "濮阳": "puyang",
    "新乡": "xinxiang",
    "焦作": "jiaozuo",
    "三门峡": "sanmenxia",
    "开封": "kaifeng",
    "洛阳": "luoyang",
    "商丘": "shangqiu",
    "许昌": "xuchang",
    "平顶山": "pingdingshan",
    "周口": "zhoukou",
    "漯河": "luohe",
    "南阳": "nanyang",
    "驻马店": "zhumadian",
    "信阳": "xinyang",

    # 湖北省
    "武汉": "wuhan",
    "十堰": "shiyan",
    "襄樊": "xiangfan",
    "随州": "suizhou",
    "荆门": "jingmen",
    "孝感": "xiaogan",
    "宜昌": "yichang",
    "黄冈": "huanggang",
    "鄂州": "ezhou",
    "荆州": "jingzhou",
    "黄石": "huangshi",
    "咸宁": "xianning",

    # 湖南省
    "长沙": "changsha",
    "岳阳": "yueyang",
    "张家界": "zhangjiajie",
    "常德": "changde",
    "益阳": "yiyang",
    "湘潭": "xiangtan",
    "株洲": "zhuzhou",
    "娄底": "loudi",
    "怀化": "huaihua",
    "邵阳": "shaoyang",
    "衡阳": "hengyang",
    "永州": "yongzhou",
    "郴州": "chenzhou",

    # 广东省
    "广州": "guangzhou",
    "韶关": "shaoguan",
    "梅州": "meizhou",
    "河源": "heyuan",
    "清远": "qingyuan",
    "潮州": "chaozhou",
    "揭阳": "jieyang",
    "汕头": "shantou",
    "肇庆": "zhaoqing",
    "惠州": "huizhou",
    "佛山": "foshan",
    "东莞": "dongguan",
    "云浮": "yunfu",
    "汕尾": "shanwei",
    "江门": "jiangmen",
    "中山": "zhongshan",
    "深圳": "shenzhen",
    "珠海": "zhuhai",
    "阳江": "yangjiang",
    "茂名": "maoming",
    "湛江": "zhanjiang",

    # 广西壮族自治区
    "南宁": "nanning",
    "桂林": "guilin",
    "河池": "hechi",
    "贺州": "hezhou",
    "柳州": "liuzhou",
    "百色": "baise",
    "来宾": "laibin",
    "梧州": "wuzhou",
    "贵港": "guigang",
    "玉林": "yulin",
    "崇左": "chongzuo",
    "钦州": "qinzhou",
    "防城港": "fangchenggang",
    "北海": "beihai",

    # 海南省
    "海口": "haikou",
    "三亚": "sanya",
    "三沙": "sansha",
    "儋州": "danzhou",

    # 四川省
    "成都": "chengdu",
    "广元": "guangyuan",
    "巴中": "bazhong",
    "绵阳": "mianyang",
    "德阳": "deyang",
    "达州": "dazhou",
    "南充": "nanchong",
    "遂宁市": "suining",
    "广安": "guangan",
    "资阳": "ziyang",
    "眉山": "meishan",
    "雅安": "yaan",
    "内江": "neijiang",
    "乐山": "leshan",
    "自贡": "zigong",
    "泸州": "luzhou",
    "宜宾": "yibin",
    "攀枝花": "panzhihua",

    # 贵州省
    "贵阳": "guiyang",
    "遵义": "zunyi",
    "六盘水": "liupanshui",
    "安顺": "anshun",
    "铜仁": "tongren",
    "毕节": "bijie",

    # 云南省
    "昆明": "kunming",
    "昭通": "zhaotong",
    "丽江": "lijiang",
    "曲靖": "qujing",
    "保山": "baoshan",
    "玉溪": "yuxi",
    "临沧": "lincang",
    "普洱": "puer",

    # 西藏自治区
    "拉萨": "lasa",
    "日喀则": "rikaze",
    "昌都": "changdu",
    "林芝": "linzhi",
    "山南": "shannan",
    "那曲": "naqu",

    # 陕西省
    "西安": "xian",
    "榆林": "yulin",
    "延安": "yanan",
    "铜川": "tongchuan",
    "渭南": "weinan",
    "宝鸡": "baoji",
    "咸阳": "xianyang",
    "商洛": "shangluo",
    "汉中": "hanzhong",
    "安康": "ankang",

    # 甘肃省
    "兰州": "lanzhou",
    "嘉峪关": "jiayuguan",
    "酒泉": "jiuquan",
    "张掖": "zhangye",
    "金昌": "jinchang",
    "武威": "wuwei",
    "白银": "baiyin",
    "庆阳": "qingyang",
    "平凉": "pingliang",
    "定西": "dingxi",
    "天水": "tianshui",
    "陇南": "longnan",

    # 青海省
    "西宁": "xining",
    "海东": "haidong",

    # 宁夏回族自治区
    "银川": "yinchuan",
    "石嘴山": "shizuishan",
    "吴忠": "wuzhong",
    "中卫": "zhongwei",
    "固原": "guyuan",

    # 新疆维吾尔自治区
    "乌鲁木齐": "wulumuqi",
    "克拉玛依": "kelamayi",
    "吐鲁番": "tulufan",
    "哈密": "hami"
}


# with open('v1.json', 'r') as file:
#     data = json.load(file)
# print("data###################",data)
# links = [item['link'] for item in data['items']][:3]
# print(links)
# import requests
#
# api_key = 'SjvnKcNWWZ3e9Pb6Q'
# location = 'shanghai'
# base_url = 'https://api.seniverse.com/v3/weather/daily.json'
# url = f'{base_url}?key={api_key}&location={location}&language=zh-Hans&unit=c&start=-1&days=5'
#
# response = requests.get(url)
#
# if response.status_code == 200:
#     data = response.json()
#     print(data)
# else:
#     print(f'Error: {response.status_code}')

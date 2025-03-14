import vlm_client
from PIL import Image, ImageDraw

#import aiofiles



class VLLMPDFClient:
    def __init__(self):
        self.client=vlm_client.VLMClient()
        self.images=[]
    def verify(self,img, bounding_boxes_str):
        """
        根据字符串解析 bounding boxes 并在图像上绘制。
        """
        # 获取图像尺寸
        original_width, original_height = img.size

        # 解析输入格式
        bounding_boxes = []
        for item in bounding_boxes_str.splitlines():
            if ":" in item:  # 确保是有效格式
                key, coords = item.split(":")
                coords = coords.strip()
                bounding_boxes.append(coords)

        # 转换为可编辑的图像
        draw = ImageDraw.Draw(img)
        # 绘制每个矩形框
        for bbox in bounding_boxes:
            coords = bbox.split("),(")
            top_left = list(map(int, coords[0].strip("()").split(",")))
            bottom_right = list(map(int, coords[1].strip("()").split(",")))

            # 根据比例调整坐标
            top_left[0] = int(top_left[0] * original_width / 1000)
            top_left[1] = int(top_left[1] * original_height / 1000)
            bottom_right[0] = int(bottom_right[0] * original_width / 1000)
            bottom_right[1] = int(bottom_right[1] * original_height / 1000)
            extra_width = int(0.05 * original_width)
            bottom_right[0] = min(bottom_right[0] + extra_width, original_width)
            extra_height = int(0.025 * original_height)
            bottom_right[1] = min(bottom_right[1] + extra_height, original_height)


            # 绘制矩形框
            color = (0, 255, 0)  # 绿色
            draw.rectangle([tuple(top_left), tuple(bottom_right)], outline=color, width=2)
            cropped = img.crop((*top_left, *bottom_right))
            cropped.format="png"
            self.images.append(cropped)

        # 显示图像 (Pillow 不支持直接显示，需要保存后查看)


    def find_graph(self,image_filepath):
        bounding_box = []
        img = Image.open(image_filepath)  # 使用 Pillow 读取图像
            
        if_image = self.client.run_single_image(image_filepath, "Are there any image, table or graph in the given page?if it have return 1 else return 0")
        print("image:", if_image)
        if int(if_image):
            bounding_box = self.client.run_single_image(image_filepath, """you are a powerful hunter you are excal in dectect graph, spreadsheet and image. Detect the bounding box of all images in the paper. Each bounding box should include all relevant elements, such as the title, description, legend, axes and its labal, and any other associated details if possible. For every bounding box, output in this template:

        bounding_box1:(x1,y1),(x2,y2)

        If there are multiple images, please output in this template:

        bounding_box1:(x1,y1),(x2,y2)
        bounding_box2:(x1,y1),(x2,y2)
        bounding_box3:(x1,y1),(x2,y2)

        Template ends here.

        Please output the bounding box only, and a bigger bounding box that contain more information is encouraged""")
            print("enter:", image_filepath)
            print(image_filepath, "/t", bounding_box)
            self.verify(img, bounding_box)

        

    def VLLM_processing(self,result,state):
        VLLM_result=[]
        for item in result:
            VLLM_result.append(self.client.run_single_image_obj(item,state))
        return VLLM_result,result
    
    def image_process(self,image_filepath,state):
        self.find_graph(image_filepath)
        result=self.VLLM_processing(self.images,state)
        return result[0],result[1]

if __name__ == '__main__' :
    Client=VLLMPDFClient()
    image_filepath="/home/terry/Desktop/pdf_processing/pages/doc_result_page_4_svg_image_1.png"
    result1,result2 = Client.image_process(image_filepath,"what's in the image")
    for item in result2:
        item.show()
    for item in result1:
        print(item)

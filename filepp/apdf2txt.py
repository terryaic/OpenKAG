import os
import fitz
from os.path import abspath, dirname
import sys
import io
from PIL import Image
from settings import PNG_SCALE, PNG_DPI, PNG_BACKGROUND_COLOR, IMAGE_MIN_SIZE,IMAGE_MIN_WIDTH,IMAGE_MIN_HEIGHT
import cairosvg
from llm.pdf_processor import pdf_process
from llm.pdf_process.data_preprocess import load_pdf_page
from PIL import Image, ImageDraw

#使用fitz 库直接提取pdf
#参数：    pdf      源pdf文件完整路径
def pdf2txt(pdf, extract_text=False):
    doc = fitz.open(pdf)
    # 图片计数
    imgcount = 0
    lenXREF = doc.xref_length()    #获取pdf文件对象总数

    # 打印PDF的信息
    print("文件名:{}, 页数: {}, 对象: {}".format(pdf, len(doc), lenXREF - 1))
    
    #遍历doc，获取每一页
    ret = ""
    for page in doc: 
        text = page.get_text()
        if extract_text:
            import trafilatura
            text = trafilatura.extract(text)
        if text.strip() != '':
            ret += text.strip()
    return ret

def save_pdf_data_image_bbox(page, page_index, bbox, caption_box, doc_id, data_type, output_folder=None):
    # 打开 PDF
    image = load_pdf_page(page)
    
    min_x, min_y, max_x, max_y = bbox

    if len(caption_box):
        for box in caption_box:
            x0, y0, x1, y1 = box
            min_x = x0 if x0 < min_x else min_x
            min_y = y0 if y0 < min_y else min_y
            max_x = x1 if x1 > max_x else max_x
            max_y = y1 if y1 > max_y else max_y

    # draw.rectangle([min_x, min_y, max_x, max_y], outline="red", width=3)  # 绘制红色边框
    cropped_image = image.crop((min_x, min_y, max_x, max_y))

    image_name = f"doc_{doc_id}_page_{page_index + 1}_yolo_{data_type}.png"
    output_path = os.path.join(output_folder, image_name)

    # 保存或显示图像
    if output_path:
        cropped_image.save(output_path)  # 保存图像到指定路径

    return image_name 


def save_pdf_data_image(image, page_index, doc_id, data_type, index, output_folder=None):
    image_name = f"doc_{doc_id}_page_{page_index + 1}_yolo_{data_type}_{index}.png"
    output_path = os.path.join(output_folder, image_name)

    # 保存或显示图像
    if output_path:
        image.save(output_path)  # 保存图像到指定路径

    return image_name 


def save_images(images, category, page_index, doc_id, output_folder, image_name_list):
    for index, image in enumerate(images):
        if image.image:
            data_image_name = save_pdf_data_image(image.image, page_index, doc_id, category, index, output_folder)
            image_name_list.append(data_image_name)


def get_pdf_data_image(page, page_index, doc_id, output_folder):
    image_name = []
    
    # 处理 figures, graphs, formulas 三个类别的图片
    save_images(page.figures, "figure", page_index, doc_id, output_folder, image_name)
    save_images(page.graphs, "graphs", page_index, doc_id, output_folder, image_name)
    save_images(page.formulas, "formulas", page_index, doc_id, output_folder, image_name)

    return image_name


def get_pdf_all_data_image(pdf_path):
    result = pdf_process(pdf_path)
    return result

def extract_images_from_pdf(pdf_path, output_folder, doc_id:int, get_text=False, extract_text=False, png_scale=PNG_SCALE, png_dpi=PNG_DPI, png_background_color=PNG_BACKGROUND_COLOR, image_min_size=IMAGE_MIN_SIZE, image_min_width=IMAGE_MIN_WIDTH, image_min_height=IMAGE_MIN_HEIGHT):
    image_names = []
    page_nums = []
    page_texts = []
    # Open the PDF file
    pdf_file = fitz.open(pdf_path)
    xrefs = []
    all_text = ""

    data_image_info = get_pdf_all_data_image(pdf_path).pages

    # Loop through each page
    for page_num in range(pdf_file.page_count):
        page = pdf_file[page_num]
        if get_text:
            page_text = page.get_text()
            if extract_text:
                import trafilatura
                page_text = trafilatura.extract(page_text)
            page_texts.append(page_text)
            if page_text:
                all_text += page_text +"\n"
            # 如果没有文字就获取svg变成图片

            if not page_text:
                # 提取页面中的矢量图形
                svg = page.get_svg_image()
                image_filename = f"doc_{doc_id}_page_{page_num + 1}_svg_image_1.png"
                image_filepath = os.path.join(output_folder, image_filename)
                cairosvg.svg2png(
                    bytestring=svg.encode('utf-8'),  # 直接传递 SVG 字符串            
                    write_to=image_filepath,
                    background_color= png_background_color,
                    scale = png_scale,
                    dpi=png_dpi  # 设置 DPI 分辨率
                )
                image_names.append(image_filepath)
                page_nums.append(page_num)
                all_text += f"![]({image_filename})\n"

        # # Get the images on the page
        # images = page.get_images(full=True)
        
        # # Loop through each image
        # for img_index, img in enumerate(images):
        #     # Get the image XREF (reference number)
        #     xref = img[0]
        #     if xref in xrefs:
        #         continue
        #     xrefs.append(xref)
        #     # Extract the image bytes
        #     base_image = pdf_file.extract_image(xref)
        #     image_bytes = base_image["image"]
        #     image_ext = base_image["ext"]
            
        #     # Create an image object using PIL
        #     image = Image.open(io.BytesIO(image_bytes))

        #     # 进行图片的筛选
        #     if image.width * image.height < image_min_size or image.width < image_min_width or image.height < image_min_height:
        #         print(f"图片不符合要求:{image.size} {image.width} {image.height}")
        #         continue
            
        #     # Save the image
        #     image_filename = f"doc_{doc_id}_page_{page_num + 1}_image_{img_index + 1}.{image_ext}"
        #     image_filepath = os.path.join(output_folder, image_filename)
        #     image.save(image_filepath)
        #     image_names.append(image_filepath)
        #     page_nums.append(page_num)
        #     all_text += f"![]({image_filename})\n"
        #     print(f"Saved image: {image_filepath}")

        # 对yolo检测加入到text中
        data_images_nmae = get_pdf_data_image(data_image_info[page_num], page_num, doc_id, output_folder)
        for img_name in data_images_nmae:
            if img_name:
                all_text += f"![]({img_name})\n"
                print("检测加入的图片名字是",img_name)
                if img_name:
                    data_image_filepath = os.path.join(output_folder, img_name)
                    image_names.append(data_image_filepath)

    # Close the PDF file
    pdf_file.close()
    return all_text, image_names, page_nums, page_texts


def only_txt_pdf(pdf_path, extract_text):
    page_texts = []
    all_text = ""

    pdf_file = fitz.open(pdf_path)
    for page_num in range(pdf_file.page_count):
        page = pdf_file[100]
        page_text = page.get_text()
        if extract_text:
            import trafilatura
            page_text = trafilatura.extract(page_text)
        page_texts.append(page_text)
        if page_text:
            all_text += page_text +"\n"

    return all_text, page_texts


if __name__ == "__main__":
    # Usage
    import sys
    pdf_path = sys.argv[1]  # Specify the PDF file path
    output_folder = sys.argv[2]  # Specify the output folder for extracted images
    extract_images_from_pdf(pdf_path, output_folder)


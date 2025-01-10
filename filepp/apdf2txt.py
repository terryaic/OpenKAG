import os
import fitz
from os.path import abspath, dirname
import sys
import io
from PIL import Image

PNG_SCALE = 2
PNG_DPI = 600
PNG_BACKGROUND_COLOR = "white"
IMAGE_MIN_SIZE = 100*100
IMAGE_MIN_WIDTH = 40
IMAGE_MIN_HEIGHT = 40

import cairosvg

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

def extract_images_from_pdf(pdf_path, output_folder, doc_id:int, get_text=False, extract_text=False, png_scale=PNG_SCALE, png_dpi=PNG_DPI, png_background_color=PNG_BACKGROUND_COLOR, image_min_size=IMAGE_MIN_SIZE, image_min_width=IMAGE_MIN_WIDTH, image_min_height=IMAGE_MIN_HEIGHT):
    image_names = []
    page_nums = []
    page_texts = []
    # Open the PDF file
    pdf_file = fitz.open(pdf_path)
    xrefs = []
    
    # Loop through each page
    for page_num in range(pdf_file.page_count):
        page = pdf_file[page_num]
        if get_text:
            page_text = page.get_text()
            if extract_text:
                import trafilatura
                page_text = trafilatura.extract(page_text)
            page_texts.append(page_text)
            # 如果没有文字就获取svg变成图片

            if not page_text:
                # 提取页面中的矢量图形
                svg = page.get_svg_image()
                image_filename = f"{output_folder}/doc_{doc_id}_page_{page_num + 1}_svg_image_1.png"
                cairosvg.svg2png(
                    bytestring=svg.encode('utf-8'),  # 直接传递 SVG 字符串            
                    write_to=image_filename,
                    background_color= png_background_color,
                    scale = png_scale,
                    dpi=png_dpi  # 设置 DPI 分辨率
                )
                image_names.append(image_filename)
                page_nums.append(page_num)

        # Get the images on the page
        images = page.get_images(full=True)
        
        # Loop through each image
        for img_index, img in enumerate(images):
            # Get the image XREF (reference number)
            xref = img[0]
            if xref in xrefs:
                continue
            xrefs.append(xref)
            # Extract the image bytes
            base_image = pdf_file.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            # Create an image object using PIL
            image = Image.open(io.BytesIO(image_bytes))

            # 进行图片的筛选
            if image.width * image.height < image_min_size or image.width < image_min_width or image.height < image_min_height:
                print("图片不符合要求")
                print("图片的大小:",image.size)
                print("图片的宽度:",image.width)
                print("图片的长度:",image.height)
                continue
            
            # Save the image
            image_filename = f"{output_folder}/doc_{doc_id}_page_{page_num + 1}_image_{img_index + 1}.{image_ext}"
            image.save(image_filename)
            image_names.append(image_filename)
            page_nums.append(page_num)
            print(f"Saved image: {image_filename}")
    
    # Close the PDF file
    pdf_file.close()
    print("Image extraction completed.")
    return image_names, page_nums, page_texts

if __name__ == "__main__":
    # Usage
    import sys
    pdf_path = sys.argv[1]  # Specify the PDF file path
    output_folder = sys.argv[2]  # Specify the output folder for extracted images
    extract_images_from_pdf(pdf_path, output_folder)


'''
import subprocess
import os

def convert_to_pdf(input_path):
    # 获取输入文件的目录和文件名
    dir_name, file_name = os.path.split(input_path)
    # 构建输出PDF文件的路径
    output_path = os.path.join(dir_name, os.path.splitext(file_name)[0] + '.pdf')
    
    # 使用LibreOffice进行转换
    subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', input_path, '--outdir', dir_name], check=True)
    
    return output_path

import pypandoc

def p_docx_to_pdf(docx_path, pdf_path):
    output = pypandoc.convert_file(docx_path, 'pdf', outputfile=pdf_path)
    assert output == ""
'''

import mammoth
import pdfkit

def docx_to_pdf(docx_path, pdf_path):
    with open(docx_path, "rb") as docx_file:
        result = mammoth.convert_to_html(docx_file)
        html = result.value  # 获取HTML内容
    
    # 将HTML内容转换为PDF
    pdfkit_options = {'encoding': 'UTF-8'}
    pdfkit.from_string(html, pdf_path, options=pdfkit_options)

if __name__== "__main__":
    # 使用示例
    input_path = 'example.docx'
    pdf_output = 'example.docx.pdf'
    #pdf_output = convert_to_pdf(input_path)
    docx_to_pdf(input_path, pdf_output) 
    print(f'PDF file saved at: {pdf_output}')


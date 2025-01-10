import pandas as pd
from tabulate import tabulate

def excel_to_markdown(file_path, sheet_name=0):
    # 读取Excel文件
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # 将DataFrame转换为Markdown格式
    markdown = tabulate(df, headers='keys', tablefmt='pipe', showindex=False)
    
    return markdown

if __name__ == "__main__":
    # 使用示例
    file_path = 'example.xlsx'
    markdown_output = excel_to_markdown(file_path)
    print(markdown_output)
    with open('output.md', 'w') as f:
        f.write(markdown_output)



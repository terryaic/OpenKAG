import markdown

# 读取 Markdown 文件内容
with open('input.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# 将 Markdown 转换为 HTML
html_content = markdown.markdown(md_content, extensions=['tables'])

# 将 HTML 写入文件
with open('output.html', 'w', encoding='utf-8') as f:
    f.write(html_content)


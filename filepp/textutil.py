
def table_to_markdown(table_data):
    markdown = []
    if not table_data:
        return ""

    headers = table_data[0]
    markdown.append("| " + " | ".join(headers) + " |")
    markdown.append("|" + " --- |" * len(headers))

    for row in table_data[1:]:
        markdown.append("| " + " | ".join(row) + " |")

    return "\n".join(markdown)

def content_to_txt(content):

  # 打印读取到的内容
  out = ""
  for item_type, item_content in content:
    if item_type == 'paragraph':
        #print(f'Paragraph: {item_content}')
        out += item_content +"\n"
    elif item_type == 'table':
        #print('Table:')
        #for row in item_content:
        #    print(row)
        markdown_table = table_to_markdown(item_content)
        #print(markdown_table)
        out += markdown_table + "\n"
  return out

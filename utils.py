
# Get the last N URLs from an RSS feed
def getUrls(feed_url):
    import feedparser
    feed = feedparser.parse(feed_url)
    entries = feed.entries
    urls = [entry.link for entry in entries]
    return urls

# Often there are a bunch of ads and menus on pages for a news article. This uses newspaper3k to get just the text of just the article.
def getArticleText(url):
  from newspaper import Article
  article = Article(url)
  article.download()
  article.parse()
  return article.text


# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_path):
    from PyPDF2 import PdfReader
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def remove_blank_lines(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    with open(file_path, 'w', encoding='utf-8') as file:
        for line in lines:
            if line.strip():
                file.write(line)

def remove_blank_lines_folder(folder_path):
    import os
    for root,dir,files in os.walk(folder_path):
        for file in files:
            if file.endswith(".txt") or file.endswith(".md"):
                fullpath = os.path.join(root, file)
                print("cleaning file:"+fullpath)
                remove_blank_lines(fullpath) 

def rename_ext(folder_path, src, dst):
    import os
    #import shutil
    for root,dir,files in os.walk(folder_path):
        for file in files:
            if file.endswith(src):
                fullpath = os.path.join(root, file)
                dstpath = os.path.join(root, file.replace(src, dst))
                #shutil.move(fullpath, dstpath)
                os.rename(fullpath, dstpath)
                print("rename file:"+fullpath)
import re
import os
import sys

def clean_markdown_table(md_table: str) -> str:
    # Split the table into lines
    lines = md_table.strip().split('\n')

    # Use a regular expression to remove extra spaces in each line
    cleaned_lines = []
    for line in lines:
        # Remove leading and trailing spaces
        line = line.strip()
        # Replace multiple spaces between columns with a single space
        line = re.sub(r'\s{2,}', ' ', line)
        # Ensure there's exactly one space before and after each pipe
        line = re.sub(r'\s*\|\s*', ' | ', line)
        cleaned_lines.append(line)

    # Join the cleaned lines back into a single string
    cleaned_table = '\n'.join(cleaned_lines)
    return cleaned_table

# Example usage
markdown_table = """
| Column 1    | Column 2    | Column 3 |
|-------------|-------------|----------|
|   Value 1   |   Value 2   | Value 3  |
|   Value 4   | Value 5     |   Value 6|
"""

#cleaned_table = clean_markdown_table(markdown_table)
#print(cleaned_table)


def remove_images_from_markdown(md_text: str) -> str:
    # Use a regular expression to find and remove image links
    cleaned_text = re.sub(r'!\[.*?\]\(.*?\)', '', md_text)
    return cleaned_text

# Example usage
markdown_text = """
# Sample Markdown

This is a sample text with an image.

![0_image_0.png](0_image_0.png)

More text here.
"""

#cleaned_text = remove_images_from_markdown(markdown_text)
#print(cleaned_text)

def clean_markdown(content):
    cleaned_table = clean_markdown_table(content)
    cleaned = remove_images_from_markdown(cleaned_table)
    return cleaned

def process_folder(input_folder, output_folder):
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith(".md"):
                fullpath = os.path.join(root, file)
                with open(fullpath, "r", encoding='utf8') as fp:
                    content = fp.read()
                    cleaned_table = clean_markdown_table(content)
                    cleaned = remove_images_from_markdown(cleaned_table)
                    print(cleaned)
                outfilepath = os.path.join(output_folder, file)
                with open(outfilepath, 'w', encoding='utf8') as fp:
                    fp.write((cleaned))

if __name__ == "__main__":
    process_folder(sys.argv[1], sys.argv[2])
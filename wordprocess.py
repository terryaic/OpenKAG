from nltk.corpus import words
english_dictionary = set(words.words())

def insert_spaces(sentence, dictionary):
    word_start = 0
    corrected_sentence = ""

    while word_start < len(sentence):
        for word_end in range(len(sentence), word_start, -1):
            word = sentence[word_start:word_end]
            if word in dictionary or word_end == word_start + 1:
                corrected_sentence += word + " "
                word_start = word_end
                break

    return corrected_sentence.strip()

def process_words(sentence):
    return insert_spaces(sentence, english_dictionary)

def is_word(word):
    return word in english_dictionary

def count_words(text):
    """Counts the number of words in a given text.

    Args:
    text (str): The text to be analyzed.

    Returns:
    int: The number of words in the text.
    """
    words = text.split()
    return len(words)

import jieba

def count_chinese_words(text):
    """Counts the number of words in a given Chinese text.

    Args:
    text (str): The Chinese text to be analyzed.

    Returns:
    int: The number of words in the text.
    """
    words = jieba.cut(text)
    return len(list(words))

def counts_text(text):
    from langdetect import detect
    try:
        detected_language = detect(text)
        print(detected_language)
        if detected_language == 'zh-cn':
            return count_chinese_words(text)
        else:
            return count_words(text)
    except Exception as e:
        print(e)
    return 0

if __name__ == "__main__":
    # Example usage
    sample_text = "这是一个示例文本，用于演示中文词数统计脚本。"
    word_count = counts_text(sample_text)
    print(word_count)
    # Example usage
    sample_text = "This is a sample text to demonstrate the word counting script."
    word_count = counts_text(sample_text)
    print(word_count)

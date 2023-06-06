import os
import json
import tqdm
import sys
import time
import re
from multiprocessing import Pool


def load_txt(path):
    """
    Load and read text data from a file.

    Args:
        path (str): The string path to the file. For example, "./data/".

    Returns:
        list: A list of non-empty, whitespace stripped lines content from the file.
    """
    # Open file `f` in text mode with 'UTF-8' encoding (handle text data that may contain non-ASCII characters)
    # and 'ignore' errors parameter to ignore any decoding errors encountered while reading the file
    with open(path, encoding='UTF-8', errors='ignore') as f:
        # `f.readlines()` returns a list of strings where each string represents a line in the file
        # Iterates over each line `i` in the file and applies `strip()` to remove any leading or trailing whitespace characters
        # Filters out empty lines by checking whether the length of stripped line `len(i.strip())` is greater than 0
        data = [i.strip() for i in f.readlines() if len(i.strip()) > 0]
    return data


def save_txt(data, path):
    """
    Save data as text by writing its content into a file.

    Args:
        data (str or list): The text content to be saved.
        path (str): The string path to the file.

    """
    # Open file `f` in write mode 'w' to indicate that existing content in the file might be overwritten
    # `with` to ensure the file is properly opened and closed
    # `write()` is called on `f` to write the contents of `data` into the file
    with open(path, 'w', encoding='UTF-8') as f:
        f.write(data)


def load_jsonl(path):
    """
    Read a file in the JSON Lines format.

    Args:
        path (str): The string path to the file.

    Returns:
        list: A list of Python dictionaries, where each dictionary represents a JSON object.
    
    Example:
        input: 'data.jsonl'
            {"name": "John", "age": 25}
            {"name": "Alice", "age": 30}
            {"name": "Bob", "age": 35}
        output:
            [{'name': 'John', 'age': 25}, {'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 35}]

    """
    # Open file `f` in read mode 'r' to load the content of the file
    with open(path, 'r', encoding='UTF_8') as f:
        # `f.readlines()` reads all lines from the file
        # Iterate over each line `line` and filter out empty whitespace stripped lines `len(line.strip()) > 0`
        # `json.loads(line)` parses each line as a JSON object and create a dictionary, for example {'name': 'John'}
        # Return a list containing all the dictionaries
        return [json.loads(line) for line in f.readlines() if len(line.strip()) > 0]


def save_jsonl(data, path):
    with open(path, 'w', encoding='UTF-8') as f:
        f.write("\n".join(json.dumps(line, ensure_ascii=False) for line in data))


def no_at(seq, tail_length=30):
    temp_pat = re.compile(r"(@+)\S{,30} ")
    seq = temp_pat.sub("", seq)
    r_at_idx = seq.rfind("@")
    if len(seq[r_at_idx:]) < tail_length:
        seq = seq[:r_at_idx]
    return seq


def is_chinese_char(cp):
    """Checks whether CP is the codepoint of a CJK character."""
    # This defines a "chinese character" as anything in the CJK Unicode block:
    #   https://en.wikipedia.org/wiki/CJK_Unified_Ideographs_(Unicode_block)
    #
    # Note that the CJK Unicode block is NOT all Japanese and Korean characters,
    # despite its name. The modern Korean Hangul alphabet is a different block,
    # as is Japanese Hiragana and Katakana. Those alphabets are used to write
    # space-separated words, so they are not treated specially and handled
    # like the all of the other languages.
    if (
            (cp >= 0x4E00 and cp <= 0x9FFF)
            or (cp >= 0x3400 and cp <= 0x4DBF)  #
            or (cp >= 0x20000 and cp <= 0x2A6DF)  #
            or (cp >= 0x2A700 and cp <= 0x2B73F)  #
            or (cp >= 0x2B740 and cp <= 0x2B81F)  #
            or (cp >= 0x2B820 and cp <= 0x2CEAF)  #
            or (cp >= 0xF900 and cp <= 0xFAFF)
            or (cp >= 0x2F800 and cp <= 0x2FA1F)  #
    ):  #
        return True

    return False


def contains_Chinese(seq):
    for char in seq:
        cp = ord(char)
        if is_chinese_char(cp):
            return True
    return False


def contain_at(seq, tail_length=30):
    flag = re.search(r"(@+)\S{,30} ", seq)
    if flag is not None:
        return True
    r_at_idx = seq.rfind("@")
    if r_at_idx > -1 and len(seq[r_at_idx:]) < tail_length:
        return True
    return False


TM_REGEX = re.compile(r"([^a-zA-Z])(tm)([^a-zA-Z])", re.I)
BRACKETS_REGEX = re.compile(r"\[.*?\] *")
BRACKETS_REGEX2 = re.compile(r"［.*?］ *")
# BRACKETS_REGEX3 = re.compile(r"【.*?】 *")
COLON_REGEX = re.compile(r"[:\s]{4,}")


def seq_clean(seq, data_type="none"):
    if data_type == "zhihu":
        pat = re.compile(r"…* *显示全部\s*")
        seq = pat.sub("", seq)
    elif data_type == "weibo_tang":
        seq = BRACKETS_REGEX.sub("", seq)
        seq = BRACKETS_REGEX2.sub("", seq)
    if contain_at(seq):
        seq = ""
    if "尼玛" in seq:
        seq = ""
    seq = COLON_REGEX.sub("", seq)
    seq = seq.replace("[图片]", "")
    seq = seq.replace("［图片］", "")
    seq = seq.replace("我擦", "")
    seq = TM_REGEX.sub(lambda m: m.group(1) + m.group(3), seq)
    return seq


def single_func(path, outpath, extra_func=False, min_length=5, max_length=200):
    try:
        new_data = []
        print("loading", path)
        print("outpath", outpath)
        # data = load_jsonl(path)
        data = load_txt(path)
        data = [x.split("\t\t") for x in data]
        for dialog in tqdm.tqdm(data):
            new_dialog = []
            for seq in dialog:
                seq = seq.replace(" ", "")
                if extra_func:
                    if "zhihu" in path:
                        data_type = "zhihu"
                    elif "weibo_tang" in path or "weibo_sunhao" in path:
                        data_type = "weibo_tang"
                    else:
                        data_type = "none"
                    seq = seq_clean(seq, data_type)

                length = len(seq)
                if length > max_length or length < 1 or "http" in seq:
                    if len(new_dialog) > 1:  # or length < min_length
                        # flag = len(new_dialog) == 2 and len(new_dialog[1].replace(" ", "")) < min_length
                        # if not flag:
                        new_data.append(new_dialog)
                    new_dialog = []
                else:
                    new_dialog.append(seq)
            if len(new_dialog) > 1:
                # flag = len(new_dialog) == 2 and len(new_dialog[1].replace(" ", "")) < min_length
                # if not flag:
                new_data.append(new_dialog)
        # save_jsonl(new_data, outpath)
        new_data = ["\t\t".join(x[:j + 1]) for x in new_data for j in range(1, len(x)) if len(x[j]) >= min_length]
        save_txt("\n".join(new_data), outpath)
        print("over", path)
    except Exception as e:
        print("error!!!!", e)
    return


def main(indir, outdir, extra_func=False):
    paths = [os.path.join(instance[0], file)
             for instance in list(os.walk(indir))
             for file in instance[-1] if file.endswith(".txt")]

    outpaths = [path.replace(indir, outdir) for path in paths]

    # debug single
    # path, outpath = next(zip(paths, outpaths))
    # outsubdir = os.path.dirname(outpath)
    # if not os.path.exists(outsubdir):
    #     os.makedirs(outsubdir)
    # single_func(path, outpath, extra_func)
    # exit()

    p = Pool(16)
    print("start")
    for path, outpath in zip(paths, outpaths):
        outsubdir = os.path.dirname(outpath)
        if not os.path.exists(outsubdir):
            os.makedirs(outsubdir)
        p.apply_async(single_func, args=(path, outpath, extra_func))
        time.sleep(0.01)
    time.sleep(0.01)
    p.close()
    p.join()
    print("over")


if __name__ == '__main__':
    # filter_dist("./toy_data/raw/", "./toy_data/output/", True)
    main(sys.argv[1], sys.argv[2], True)

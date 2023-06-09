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
    
    Examples:
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
    """
    Convert a list of dictionaries of JSON object into JSONL format and write into a file.

    Args:
        path (str): The string path to the file.
        data (list): A list of dictionaries, where each dictionary represents a JSON object.
    
    """
    # Open file `f` in write mode 'w' to indicate existing content of file might be overwritten
    with open(path, 'w', encoding='UTF-8') as f:
        # For each `line` from the `data`, use `json.dumps()` to convert dictionary into JSON string representation
        # `ensure_ascii=False` to ensure non-ASCII characters are properly encoded
        # Each JSON string from `line` is added with '\n' as separator with `str.join()`
        # Creates a string where each JSON object is on a separate line, adhering to JSONL format and write to `f`
        f.write("\n".join(json.dumps(line, ensure_ascii=False) for line in data))


def no_at(seq, tail_length=30):
    """
    Remove '@' from input string and remove the remaining string that has a length <= `tail_length`.

    Args:
        seq (str): The input string.
        tail_length (int): The minimum limit of remaining length. If unspecified, the default is set to 30.
    
    Returns:
        A string with '@' removed.
    
    Examples:
        input: "@john have you reported to @anna ?"
        output: "have you reported to"

    """
    # Create a regular expression pattern using `re.compile` that matches one or more '@' characters
    # followed by up to 30 non-whitespace characters and a space
    # `r""` is raw string notation to preserve the literal characters without interpreting escape sequences
    # `(@+)` is capturing group `(...)` that matches one or more `+` consecutive '@' characters 
    # `\S{,30}` matches any non-whitespace character `\S` between 0 and 30 occurences `{,30}`
    temp_pat = re.compile(r"(@+)\S{,30} ")
    # Use `sub` to substitute all matches found in the input string `seq` with an empty string (remove)
    seq = temp_pat.sub("", seq)
    # Find the last occurence of '@' in the modified string `seq` using `rfind` and return index position (-1 if not found)
    r_at_idx = seq.rfind("@")
    # Check if the length of remaining substring from the last '@' is shorter than `tail_length`
    if len(seq[r_at_idx:]) < tail_length:
        # Preserve only the string `seq` up to the index position and remove the tail
        seq = seq[:r_at_idx]
    return seq


def is_chinese_char(cp):
    """
    Check whether a given Unicode code point represents a Chinese character.

    Args:
        cp (int): Integer value that represents a specific character in the Unicode standard.
    
    Returns:
        boolean: True if it is a Chinese character.

    """
    # This defines a "chinese character" as anything in the CJK Unicode block:
    #   https://en.wikipedia.org/wiki/CJK_Unified_Ideographs_(Unicode_block)
    #
    # Note that the CJK Unicode block is NOT all Japanese and Korean characters,
    # despite its name. The modern Korean Hangul alphabet is a different block,
    # as is Japanese Hiragana and Katakana. Those alphabets are used to write
    # space-separated words, so they are not treated specially and handled
    # like the all of the other languages.
    if (
            (cp >= 0x4E00 and cp <= 0x9FFF) # represents the Basic Multilingual Plane (BMP) range of CJK Unified Ideographs, which covers most commonly used Chinese characters
            or (cp >= 0x3400 and cp <= 0x4DBF)  # represents the Extended CJK-A range, which contains additional Chinese characters
            or (cp >= 0x20000 and cp <= 0x2A6DF)  # covers various supplementary ranges of CJK Unified Ideographs, which include less frequently used characters
            or (cp >= 0x2A700 and cp <= 0x2B73F)  # - " -
            or (cp >= 0x2B740 and cp <= 0x2B81F)  # - " -
            or (cp >= 0x2B820 and cp <= 0x2CEAF)  # - " -
            or (cp >= 0xF900 and cp <= 0xFAFF) # represents the Compatibility Ideographs range, which contains characters that are used for compatibility with older Chinese character standards
            or (cp >= 0x2F800 and cp <= 0x2FA1F)  # represents the  Compatibility Ideographs Supplement range, which contains additional compatibility ideographs
    ):  #
        return True

    return False


def contains_Chinese(seq):
    """
    Check whether a given string sequence contains Chinese characters.

    Args:
        seq (str): The input string.
    
    Returns:
        boolean: True if it contains Chinese characters.

    """
    for char in seq:
        # `ord` to convert character `char` to a Unicode code point `cp`
        cp = ord(char)
        if is_chinese_char(cp):
            return True
    return False


def contain_at(seq, tail_length=30):
    """
    Check whether a given string sequence contains '@' symbol.

    Args:
        seq (str): The input string.

    Returns:
        boolean: True if it contains '@'.
    """
    # Create a regular expression pattern using `re.compile` that matches one or more '@' characters
    # followed by up to 30 non-whitespace characters and a space
    # `r""` is raw string notation to preserve the literal characters without interpreting escape sequences
    # `(@+)` is capturing group `(...)` that matches one or more `+` consecutive '@' characters 
    # `\S{,30}` matches any non-whitespace character `\S` between 0 and 30 occurences `{,30}`
    flag = re.search(r"(@+)\S{,30} ", seq)
    # True if there is sequence matching the pattern
    if flag is not None:
        return True
    # Use `rfind` to find the index of last occurence of '@'
    r_at_idx = seq.rfind("@")
    # True if there exist '@' and the length of string after '@' is less than `tail_length`
    if r_at_idx > -1 and len(seq[r_at_idx:]) < tail_length:
        return True
    return False


# This pattern is used to find occurences of letters "tm" surrounded by non-alphabetic characters, when it is not part of a larger word.
# `([^a-zA-Z])` matches any non-alphabetic character (uppercase or lowercase)
# `(tm)` matches the letters "tm" literally
# `re.I` is flag indicating case-insensitive matching
TM_REGEX = re.compile(r"([^a-zA-Z])(tm)([^a-zA-Z])", re.I)

# This pattern is used to find occurences of text enclosed in square brackets, such as "[example text]".
# `\[` and `\]` matches the opening and closing square brackets
# `.*?` matches any character except newline, zero or more times in a non-greedy manner. The `?` makes the match non-greedy, so it stops at the first closing square bracket encountered
# ` *` matches one or more whitespace character after the closing square bracket
BRACKETS_REGEX = re.compile(r"\[.*?\] *")

# This pattern is used to find occurences of text enclosed in full-width square brackets, such as " [hello] "
BRACKETS_REGEX2 = re.compile(r"［.*?］ *")

# This pattern is used to find occurences of text enclosed in special square brackets, such as "【hello】"
BRACKETS_REGEX3 = re.compile(r"【.*?】 *")

# This pattern is used to find occurences of four or more consecutive colons or whitespace characters, such as "::::" and "    "
# It is useful for identifying indentation
# `[:\s]` matches either a colon ":" or any whitespace character (space, tab, etc.)
# `{4,}` matches four or more consecutive occurences of the preceeding pattern
COLON_REGEX = re.compile(r"[:\s]{4,}")


def seq_clean(seq, data_type="none"):
    """
    Clean input data according to their type.

    Args:
        seq (str): Input data.
        data_type (str): Type of input data, default is "none".
    
    Returns:
        str: Processed sequence.

    """
    if data_type == "zhihu":
        # Create pattern `pat` to match occurences of ellipsis ("...") followed by optional whitespace and phrase "show all" in Chinese
        pat = re.compile(r"…* *显示全部\s*")
        # Remove the matched pattern object from the input string `seq`
        seq = pat.sub("", seq)
    elif data_type == "weibo_tang":
        # Remove the matched pattern object of text enclosed in square brackets along with trailing whitespace
        seq = BRACKETS_REGEX.sub("", seq)
        seq = BRACKETS_REGEX2.sub("", seq)
    # `seq` is set to empty if it contains '@'
    if contain_at(seq):
        seq = ""
    # `seq` is set to empty if it contains a vulgar term in Chinese
    if "尼玛" in seq:
        seq = ""
    # Remove the matched pattern object of colons or whitespace characters
    seq = COLON_REGEX.sub("", seq)
    # Remove specific substring from `seq`, such as "[image]", " [image] " and exclamation in Chinese
    seq = seq.replace("[图片]", "")
    seq = seq.replace("［图片］", "")
    seq = seq.replace("我擦", "")
    # Remove trademark symbol "tm" surrounded by non-alphabetic characters. Replace the matches with characters before and after "tm"
    seq = TM_REGEX.sub(lambda m: m.group(1) + m.group(3), seq)
    return seq


def single_func(path, outpath, extra_func=False, min_length=5, max_length=200):
    """
    Process input file to generate output file that contains dialog data.

    Args:
        path (str): Path to the input file.
        outpath (str): Path to the output file.
        extra_func (bool): Determines whether additional cleaning operations should be applied based on the `data_type`. Default is `False`.
        min_length (int): Specifies the minimum length of a sequence to be considered. Default is 5.
        max_length (int): Specifies the maximum length of a sequence to be considered. Default is 200.

    """
    try:
        # Initialize empty list `new_data` to store the processed data
        new_data = []
        print("loading", path)
        print("outpath", outpath)
        # Load the input data from path, which is list of strings, each string correspond to one line from the original file
        # data = load_jsonl(path)
        data = load_txt(path)
        # Each string is split by the tab characters and stored as nested list in the `data`
        data = [x.split("\t\t") for x in data]
        # Each list in `data` is treated as `dialog` and iterated using `tqdm.tqdm` to display progress bar
        for dialog in tqdm.tqdm(data):
            # Initialize to store processed sequence for each dialog
            new_dialog = []
            # Each list in `dialog` is treated as `seq`
            for seq in dialog:
                # Leading and trailing spaces are removed
                seq = seq.replace(" ", "")
                # Perform cleaning if specified
                if extra_func:
                    if "zhihu" in path:
                        data_type = "zhihu"
                    elif "weibo_tang" in path or "weibo_sunhao" in path:
                        data_type = "weibo_tang"
                    else:
                        data_type = "none"
                    seq = seq_clean(seq, data_type)

                length = len(seq)
                # If length of `seq` is more than max_length, less than 1, or contains "http", considered inalid
                if length > max_length or length < 1 or "http" in seq:
                    # Add `new_dialog` to `new_data` if there is valid element in it, then reset the `new_dialog`
                    if len(new_dialog) > 1:  # or length < min_length
                        # flag = len(new_dialog) == 2 and len(new_dialog[1].replace(" ", "")) < min_length
                        # if not flag:
                        new_data.append(new_dialog)
                    new_dialog = []
                else:
                    new_dialog.append(seq)
            # If `new_dialog` has at least 2 sequences, add to `new_data`
            if len(new_dialog) > 1:
                # flag = len(new_dialog) == 2 and len(new_dialog[1].replace(" ", "")) < min_length
                # if not flag:
                new_data.append(new_dialog)
        # save_jsonl(new_data, outpath)
        # Construct `new_data` list by joining the sequences within each dialog using the tab separator
        new_data = ["\t\t".join(x[:j + 1]) for x in new_data for j in range(1, len(x)) if len(x[j]) >= min_length]
        save_txt("\n".join(new_data), outpath)
        print("over", path)
    except Exception as e:
        print("error!!!!", e)
    return


def main(indir, outdir, extra_func=False):
    """Performs processing on multiple text files in a directory `indir`. Uses multiprocessing to parallelize the processing and saves the results to output files in `outdir`."""
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

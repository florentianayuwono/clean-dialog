This project is a multi-threaded framework for cleaning dialog data from platforms like Zhihu, Weibo, and Tieba. Currently, it is relatively basic, and bug reports and optimizations are welcome, such as improving the regular expression or suffix algorithm for deduplication of repeated phrases within sentences. The code is still being refined, and comments as well as the references for some functions are pending completion.

# Directory Structure
    
    --scripts: Contains the scripts for running the program.
      ---run.sh: Runs run_dist.py using selected rules.
    --src: Main directory for the cleaning framework functionality.
      ---inputters: Contains dataloader and data access utility functions.
      ---rules: Stores rules functions for different levels.
      ---single_filter.py: The main program for a single thread called by run_dist.py. It loads and processes individual data, saves the filtered data, and any dirty data.
    ---tool_data: Contains a blacklist dictionary with one word per line.
    ---run_dist.py: The main execution file. It loads the dataloader, the blacklist, and establishes a thread pool.
    ---utils: Provides functionalities for data statistics and result checking.
      
# Running and Saving Logs

    bash ./scripts/run.sh 2>&1 | tee -a cleaning.log

# Rules
The rules include most of the cleaning rules found in current research papers:

1. Blacklist filtering, including special characters and profanity.
2. Emoji filtering.
3. Privacy filtering for email addresses, phone numbers, etc. Replacing names with NAME1, NAME2, etc.
4. URL filtering.
5. Unicode-related fixes.
6. Deduplication: Reducing repeated words, filtering out sentences with the same context, and repeated dialogues.
7. Exclusion of advertisements and general replies used in Meena and DialoGPT.

Any identified noise can be removed within the sentence. If it cannot be removed, the sentence is discarded. For single-turn dialogues, the entire dialogue is discarded. For multi-turn dialogues, the sentence acts as a separator to split the dialogue.  

NOTE THAT: 
1. When modifying a rule, ensure it does not affect other rules. The order of rule cleaning is important.
2. The blacklist, such as names and special topics, can be configured and placed under `./tool_data/`. File naming and configuration details can be found in `/run_dist.py`. You can search for blacklists on GitHub, for example: https://github.com/fighting41love/funNLP.
4. Test cases are provided above each function, with expected examples below.
5. The parameters used in `run.sh` are the features currently used by the author.

# Arguments
        
| Parameter               | Description                 |
| :---------------  | :------------------- |
| n_p               | Number of processes |
| batch_size        | Maximum number of sessions processed per process |
| tool_dir          | Directory for tool data (e.g., blacklist)|
| out_dir           | Output directory for cleaned files |
| raw_dir           | Directory containing the files to be processed  |
| dirty_dir         | Directory to store the cleaned dirty data. If empty, no storage  |
| :---------------  | :------------------- |
| split_multi_repost| Split Weibo repost data with the format "//@aaa XXXX //@bbb XXX" into multiple sentences  |
| no_utter_dup   | Remove dialogues where the context == response  |
| re_name           | Replace names with <NAME1>, <NAME2>, ... |
| no_ad             | Remove dialogues that may be advertisements (multiple contexts corresponding to the same reply), referring to the [paper](https://www.aclweb.org/anthology/D13-1096.pdf) |
| de_generic_dialog | Remove generic replies, referring to the [paper](https://arxiv.org/abs/1911.00536)|
| no_short_response | Remove all short responses at the end of the dialogue |
| :---------------  | :------------------- |
| bert_clean        | Clean sentences using functions from BertTokenizer |
| cleantext_clean | Clean using [clean-text](https://github.com/jfilter/clean-text) (phone numbers, email addresses, unicode errors, etc.) |
| :---------------  | :------------------- |
| no_short          | Remove overly short sentences |
| no_long           | Remove overly long sentences |
| de_reply_tag      | Remove "Reply @XXX:" in Weibo |
| de_hashtag        | Remove "# XXX#" in sentences |
| de_emotion        | Remove ": XXX:" in sentences |
| de_mention        | Remove "@Cindy," "@Bob:," "@Amy:" in sentences|
| no_mention       | Remove sentences containing @XXX |
| de_repost         | Remove "//XXX" in sentences |
| de_duplicated     | Reduce phrase duplication in sentences (to be optimized with suffix algorithm) |
| de_emoji          | Remove emojis (to be supplemented) |
| no_special_topic  | Filter dialogues containing specific words |
| no_str_blacklist  | Filter dialogues containing blacklist words |
| no_toupiao        | Determine if it is a Weibo poll |
| no_specific_utter | Delete specific sentences |
| contain_zh        | Delete sentences that do not contain Chinese characters |
| de_single_repost_mention| Remove "@XXX:" |
| de_weibo_url      | Remove http:\\t.c |
| de_url            | Remove URLs |
| de_angle          | Remove <XXX> where XX is non-Chinese characters |
| de_alpha_num      | Remove meaningless combinations of numbers and letters |
| de_specific       | Remove fixed patterns in sentences    |
| :---------------  | :------------------- |
| de_showall        | Remove "...show all" in specific files |
| de_brackets       | Remove "\[XXX\]" in specific files |
| :---------------  | :------------------- |
| no_word_blacklist | Filter dialogues with blacklist words after segmentation |
| no_alpha_noise    | Filter sentences containing letter combinations that do not form English words |
| check_confuse_word| Save dialogues containing confused words for recall |
| yda_dedupl        | If the ratio of occurrence of a word in a sentence exceeds |
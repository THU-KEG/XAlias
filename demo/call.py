import argparse
import json
import time
import random
import requests
from tqdm import tqdm
from src.data.load import AliasDataset
import bminf
from src.data.discover_alias import HasAlias
import numpy as np
from src.model.const import few_shot_alias_table
from src.model.pattern import Verbalizer
from demo.params import add_decode_param, reduce_args, add_test_param


def get_alias_example_tables(args):
    alias_tables = []
    # randomly sample examples from whole dataset or support pool
    for i in range(args.alias_table_num):
        # use random seed to maintain reproducing ability
        random.seed(args.seed)
        src_table = few_shot_alias_table[args.alias_type]
        example_keys = random.sample(src_table.keys(), args.task_specific_prompt_num)
        alias_table = {k: src_table[k] for k in example_keys}
        alias_tables.append(alias_table)
        # change seed for every table
        args.seed += 1
    return alias_tables


def call_prompt_generation(args):
    cpm2_kwargs = reduce_args(args)
    if args.language == 'ch':
        np.random.seed(args.seed)
        model = bminf.models.CPM2(device=args.gpu_id)
    else:
        # huggingface
        model = None
    verbalizer = Verbalizer(args.language, args.task)
    verbalizer.set_cpm2(model, cpm2_kwargs, args)
    src_word = args.src_word
    alias_tables = get_alias_example_tables(args)
    pred_words, pattern2beams = verbalizer.cpm2_gen_by_prompt(args.alias_type, src_word,
                                                              args.task_definition,
                                                              alias_tables)
    return pred_words


def google_search(question):
    key = "AIzaSyBX8jXLJHwUZng8m9PU0jxbre9JUdOLcgA"
    cx = "701eee53d90514a62"
    url = "https://customsearch.googleapis.com/customsearch/v1"
    # url = "https://www.googleapis.com/customsearch/v1"
    parameters = {
        "q": question,
        "cx": cx,
        "key": key,
        "orTerms": "alias candidate",
        "filter": "1"
    }
    print(question)
    page = requests.request("GET", url, params=parameters)
    results = json.loads(page.text)
    pred_words = []
    try:
        for item in results["item"]:
            print(item['snippet'])
            pred_words.append(item['snippet'])
    except KeyError:
        print("The Google search didn't work")
    return pred_words


def baidu_search(question):
    url = "http://www.baidu.com/s"
    user_agent = "Mozilla/4.0 (compatible;MSIE 5.5; Windows NT)"
    headers = {"User-Agent": user_agent}
    parameters = {
        "wd": question,
    }
    r = requests.get(url, headers=headers, params=parameters)
    html = r.text
    return [html]


def call_search_engine_generation(args):
    if args.language == 'en':
        question = args.src_word + " is also called?"
        pred_words = google_search(question)
    else:
        question = args.src_word + "的别名是?"
        pred_words = baidu_search(question)

    return pred_words


generation_functions = {
    "prompt": call_prompt_generation,
    "search_engine": call_search_engine_generation,
}


def main():
    parser = argparse.ArgumentParser()
    parser = add_test_param(parser)
    parser = add_decode_param(parser)
    parser.add_argument('--src_word', type=str, default='南京外国语学校', help="the name of input entity")
    parser.add_argument('--functions', type=str, default=generation_functions.keys(), nargs='+',
                        help="the generation_functions")
    args = parser.parse_args()
    for key in args.functions:
        func = generation_functions[key]
        print("**** call {} generation ****".format(key))
        time_start = time.time()
        pred_words = func(args)
        time_end = time.time()
        print(pred_words)
        print('Time cost = %fs' % (time_end - time_start))


if __name__ == "__main__":
    main()

import argparse
import json
import logging
import time
import random
import requests
from lxml import etree
from tqdm import tqdm
from src.data.load import AliasDataset
import bminf
from src.data.discover_alias import HasAlias
import numpy as np
from src.model.const import few_shot_alias_table
from src.model.pattern import Verbalizer
from demo.params import add_decode_param, reduce_args, add_test_param

proxies = {"https": "http://106.15.197.250:8001"}
types = ['prefix_extend', 'prefix_reduce', 'suffix_extend', 'suffix_reduce',
         'expansion', 'abbreviation', 'punctuation', 'synonym']
punctuation = "！？，｡＇／：；＝＠＼＾＿｀｜～､、〃和与跟同及,."


def contain_bad_punctuation(text):
    for ch in text:
        if ch in punctuation:
            return True
    return False


def get_alias_example_tables(args):
    alias_tables = []
    # randomly sample examples from whole dataset or support pool
    for i in range(args.alias_table_num):
        # use random seed to maintain reproducing ability
        random.seed(args.seed)
        src_table = few_shot_alias_table[args.language][args.alias_type]
        example_keys = random.sample(src_table.keys(), args.task_specific_prompt_num)
        alias_table = {k: src_table[k] for k in example_keys}
        alias_tables.append(alias_table)
        # change seed for every table
        args.seed += 1
    return alias_tables


def call_prompt_generation(args, model=None, tokenizer=None, _kwargs=None, device=None):
    cpm2_kwargs = reduce_args(args)
    np.random.seed(args.seed)
    if not model:
        if args.language == 'ch':
            model = bminf.models.CPM2(device=args.gpu_id)
        else:
            # huggingface
            model = None
    logging.info("Verbalizer:")
    logging.info(args.language)
    logging.info(args.alias_task)
    verbalizer = Verbalizer(args.language, args.alias_task)
    if args.language == 'ch' and args.model_name == 'cpm2':
        verbalizer.set_cpm2(model, cpm2_kwargs, args)
    else:
        verbalizer.set_glm(args, model, tokenizer, _kwargs, device)
    src_word = args.src_word
    logging.info("get_alias_example_tables:")
    alias_tables = get_alias_example_tables(args)
    if args.rank_strategy == "frequency":
        logging.info("fast_gen_by_prompt:")
        logging.info(src_word)
        logging.info(args.model_name)
        pred_words, pattern2beams = verbalizer.fast_gen_by_prompt(args.alias_type, src_word,
                                                                  args.task_definition,
                                                                  alias_tables)
    else:
        pred_words, pattern2beams = verbalizer.cpm2_gen_by_prompt(args.alias_type, src_word,
                                                                  args.task_definition,
                                                                  alias_tables)
    logging.info("Generated pred_words are:")
    logging.info(pred_words)
    return pred_words


def google_custom_search(question):
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
    proxies = {"http": "https://103.170.27.227:1080"}
    print(question)
    page = requests.request("GET", url, params=parameters, proxies=proxies)
    results = json.loads(page.text)
    pred_words = []
    try:
        for item in results["item"]:
            print(item['snippet'])
            pred_words.append(item['snippet'])
    except KeyError:
        print("The Google search didn't work")
    return pred_words


def google_magic_search(question, response_num=20):
    records = []
    PROXIES = [{
        'http': 'http://103.170.27.227:1080',
        'https': 'http://103.170.27.227:1080'
    }]
    PROXIES = [{"http": "http://103.170.27.227:1087", "https": "http://103.170.27.227:1087"}]
    # mg = MagicGoogle(PROXIES)
    # for res in mg.search(query=question, num=response_num):
    #     pprint.pprint(res)
    #     records.append(res)

    return records


def baidu_search(question, response_num):
    url = "http://www.baidu.com/s"
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36"
    # user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36"
    # cookie = "BD_UPN=123353; BIDUPSID=5BCE45F6C3A76173186601FD1E480BAA; PSTM=1644300973; __yjs_duid=1_1b5ce7a7bd1e76b4fc69096c2431ef161644301022456; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; BAIDUID=4F6D9CC05E0767BA91B696F35AB604F3:FG=1; delPer=0; BD_CK_SAM=1; PSINO=6; BAIDUID_BFESS=4F6D9CC05E0767BA91B696F35AB604F3:FG=1; BDUSS=VY0cjNLOWtaaTQ2Sk04OTJ4dFpKV0ZvT0E1SGpnSmlhNG1FdDVGTWVEc0JtVEppSVFBQUFBJCQAAAAAAAAAAAEAAADbBrE~yq66xdSqy9gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEMC2IBDAtic; BDUSS_BFESS=VY0cjNLOWtaaTQ2Sk04OTJ4dFpKV0ZvT0E1SGpnSmlhNG1FdDVGTWVEc0JtVEppSVFBQUFBJCQAAAAAAAAAAAEAAADbBrE~yq66xdSqy9gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEMC2IBDAtic; channel=baidusearch; BD_HOME=1; BDRCVFR[feWj1Vr5u3D]=I67x6TjHwwYf0; baikeVisitId=811ebe21-8d97-4979-be50-dc18c26f3292; shifen[307646945275_2554]=1644892302; BCLID=10473604784245814523; BDSFRCVID=CDDOJeC627LE67nDWT9WKlxJKmylcGrTH6aos4OFCR74_OF0XSABEG0Pbx8g0KubIktFogKKQgOTHR4F_2uxOjjg8UtVJeC6EG0Ptf8g0f5; H_BDCLCKID_SF=tJ-HoDKatKI3fP36q47HMtAt-fTMaR8XKKOLVhOg3p7keq8CD6JdQj5Wh4OULTcUWKJOaqvEMRRjsPo2y5jHhnJ3XPjmQj-JX2OloUnR0lopsIJM-RAWbT8U5f5Aab3laKviaMjjBMb1VCbDBT5h2M4qMxtOLR3pWDTm_q5TtUJMeCnTD-Dhe4tX-NFDqT-JJUK; BCLID_BFESS=10473604784245814523; BDSFRCVID_BFESS=CDDOJeC627LE67nDWT9WKlxJKmylcGrTH6aos4OFCR74_OF0XSABEG0Pbx8g0KubIktFogKKQgOTHR4F_2uxOjjg8UtVJeC6EG0Ptf8g0f5; H_BDCLCKID_SF_BFESS=tJ-HoDKatKI3fP36q47HMtAt-fTMaR8XKKOLVhOg3p7keq8CD6JdQj5Wh4OULTcUWKJOaqvEMRRjsPo2y5jHhnJ3XPjmQj-JX2OloUnR0lopsIJM-RAWbT8U5f5Aab3laKviaMjjBMb1VCbDBT5h2M4qMxtOLR3pWDTm_q5TtUJMeCnTD-Dhe4tX-NFDqT-JJUK; Hm_lvt_aec699bb6442ba076c8981c6dc490771=1644805187,1644892307; H_PS_PSSID=35834_34430_35105_31254_35765_35775_34584_35490_35542_35797_35322_26350_35881_35867_35879_35746; Hm_lpvt_aec699bb6442ba076c8981c6dc490771=1644977125; COOKIE_SESSION=84822_1_9_8_0_29_1_1_8_8_1_1_0_0_0_0_0_1644892303_1644977123|9#6349774_173_1644892301|9; sugstore=1; H_PS_645EC=fc5dZnGsEXu5XXsOOyAi+s45G8ldDEHIGeVwSSpc5R5wSiTTA6w8FTBukbgq5TThkQ1K; BA_HECTOR=0184a0ag20ak0k24hu1h0on4l0r; BDSVRTM=326"
    # headers = {"User-Agent": user_agent, "Cookie": cookie}
    headers = {"User-Agent": user_agent}
    parameters = {
        "wd": question,
        "lm": 1
    }
    r = requests.get(url, headers=headers, params=parameters, proxies=proxies)
    html_response = r.text
    print(html_response)
    baidu_html = etree.HTML(html_response, etree.HTMLParser())
    r1 = baidu_html.xpath('//h3')
    r2 = baidu_html.xpath('//*[@class="c-abstract"]')
    r3 = baidu_html.xpath('//*[@class="t"]/a/@href')
    _response_num = min(len(r1), len(r2), len(r3), response_num)
    print("response_num: ", _response_num)
    for i in range(_response_num):
        # try:
        string_r1 = r1[i].xpath('string(.)')
        string_r2 = r2[i].xpath('string(.)')
        string_r3 = r3[i]
        print(string_r1)
        print(string_r2)
        print(string_r3)
        print("-" * 18)
        # except IndexError:
        #     print("Baidu doesn't have enough responses")
        #     break
    return []


def call_search_engine_generation(args):
    if args.language == 'en':
        question = args.src_word + " is also called?"
        pred_words = google_magic_search(question)
    else:
        question = args.src_word + "的别名是?"
        pred_words = baidu_search(question, args.num_generate_sequences)

    return pred_words


generation_functions = {
    "prompt": call_prompt_generation,
    # "search_engine": call_search_engine_generation,
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


def prompt_with_json(model, clientJson, tokenizer=None, _kwargs=None, device=None):
    parser = argparse.ArgumentParser()
    parser = add_test_param(parser)
    parser = add_decode_param(parser)
    args = parser.parse_args([])
    args.src_word = clientJson["entity"]
    args.language = clientJson["lang"]
    if args.language == 'en' or _kwargs:
        args.model_name = 'glm'
    logging.warning("In prompt_with_json args are: " + str(args.__dict__))
    if clientJson["type"] != 'all':
        args.alias_type = clientJson["type"]
        pred_words = {clientJson["type"]: call_prompt_generation(args, model, tokenizer, _kwargs, device)}
    else:
        pred_words = {}
        for alias_type in types:
            args.alias_type = alias_type
            pred_words[alias_type] = call_prompt_generation(args, model, tokenizer, _kwargs, device)
    return pred_words


def coref_with_json(id2coref_alias, mention2ids, clientJson):
    src_word = clientJson["entity"]
    try:
        ids = mention2ids[src_word]
        alias_list, raw_chains = [], []
        for _id in ids:
            if _id in id2coref_alias.keys():
                coref_alias_list = id2coref_alias[_id]
                for coref_alias in coref_alias_list:
                    coref_chain = coref_alias["coref_chain"]
                    for mention in coref_chain:
                        if mention["text"] != src_word:
                            has_exist = False
                            for _exist_alias in alias_list:
                                if _exist_alias["text"] == mention["text"]:
                                    # frequency add 1
                                    _exist_alias["score"] += 1
                                    has_exist = True
                                    break
                            if not has_exist and not contain_bad_punctuation(mention["text"]):
                                # init
                                alias_data = {"text": mention["text"], "score": 1}
                                alias_list.append(alias_data)

                raw_chains.extend(coref_alias_list)
        alias_list = sorted(alias_list, key=lambda k: (k.get('score')), reverse=True)
        return alias_list, raw_chains
    except KeyError:
        return [], []


def dict_with_json(id2mention, mention2ids, clientJson):
    src_word = clientJson["entity"]
    try:
        ids = mention2ids[src_word]
        alias_list = []
        for _id in ids:
            if _id in id2mention.keys():
                mentions = id2mention[_id]
                for i, mention_text in enumerate(mentions):
                    if mention_text != src_word:
                        # init
                        # TODO use score in xlink to replace
                        alias_data = {"text": mention_text, "score": i}
                        alias_list.append(alias_data)
        alias_list = sorted(alias_list, key=lambda k: (k.get('score')), reverse=True)
        return alias_list
    except KeyError:
        return []


if __name__ == "__main__":
    main()

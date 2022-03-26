import json
import os
import re
from stanfordnlp.server import CoreNLPClient
from tqdm import tqdm
import argparse

pattern_type = re.compile("mentionType: \"(.*?)\"\\n")
# pattern = re.compile("mentionType: \"(.*?)\"\\n")
pattern_decimal = re.compile(r'\d+')


def getMention(mention_str):
    _numbers = pattern_decimal.findall(mention_str)
    quad_regex = pattern_type.search(mention_str)
    mentionType = quad_regex.group(1)
    beginIndex = int(_numbers[1])
    endIndex = int(_numbers[2])
    sentenceIndex = int(_numbers[4])
    return {
        "mentionType": mentionType,
        "beginIndex": beginIndex,
        "endIndex": endIndex,
        "sentenceIndex": sentenceIndex
    }


def parse_coref_chain(raw_str: str, document: list, separator: str):
    coref_chains = []
    chain_str_list = raw_str.split("chainID:")[1:]
    for chain_str in chain_str_list:
        mention_str_list = chain_str.split("mention {\n")[1:]
        coref_chain = []
        mention_texts = []
        for i, mention_str in enumerate(mention_str_list):
            mention = getMention(mention_str)
            if mention["mentionType"] != "PRONOMINAL":
                # Pronoun is not included in alias
                sent = document[mention["sentenceIndex"]]
                if separator == " ":
                    mention["text"] = separator.join(sent[mention["beginIndex"]:mention["endIndex"]])
                else:
                    # chinese use "" / english use " " to join
                    _text = sent[mention["beginIndex"]]
                    last_is_alpha = _text.encode('UTF-8').isalpha()
                    for word in sent[mention["beginIndex"] + 1:mention["endIndex"]]:
                        if word.encode('UTF-8').isalpha():
                            # Last token Is also en
                            if last_is_alpha:
                                _text += " "
                            last_is_alpha = True
                        else:
                            last_is_alpha = False
                        _text += word
                    mention["text"] = _text
                if mention["text"] not in mention_texts:
                    # make sure there is no repeat mentions
                    mention_texts.append(mention["text"])
                    coref_chain.append(mention)
        # print("coref_chain:")
        # print(coref_chain)
        # print("#" * 20)
        if 1 < len(coref_chain):
            # There are at least 2 co-reference mention are not pronouns
            coref_chains.append(coref_chain)

    return coref_chains


def parse_one(data_dir, function, data_id, id2coref_alias: dict):
    json_input_path = os.path.join(data_dir, f"{function}_coref_{data_id}.json")
    lines = open(json_input_path, 'r').readlines()
    total_num = len(lines)
    is_bd = data_dir.endswith('bd')

    client = None if is_bd else CoreNLPClient(annotators=['tokenize', 'ssplit'],
                                              timeout=30000, memory='16G')
    for line in tqdm(lines, total=total_num):
        coref_dict = json.loads(line)
        # entity list
        ent_list = coref_dict["input"]["entity_list"]
        # sentence and token
        if is_bd:
            document = coref_dict["document"]
            separator = ''
        else:
            ann = client.annotate(coref_dict["input"]["coref_input"]["Text"])
            document = [[str(token.word) for token in sentence.token] for sentence in ann.sentence]
            separator = ' '
        coref_chains = parse_coref_chain(coref_dict["coref"], document, separator)
        for coref_chain in coref_chains:
            for mention_idx, mention in enumerate(coref_chain):
                for entity in ent_list:
                    if entity[1] == mention["text"]:
                        # found one matched entity, this mention's coref mentions can be its alias
                        chain_dict = {
                            "coref_chain": coref_chain,
                            "mention_idx": mention_idx,
                            "document": document
                        }
                        try:
                            id2coref_alias[entity[0]].append(chain_dict)
                        except KeyError:
                            id2coref_alias[entity[0]] = [chain_dict]
                        break

    return id2coref_alias


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--data_id', type=int, default=5641488)
    parser.add_argument('--processes', type=int, default=49)
    parser.add_argument('--src_text', type=str, default='abstract', help="the input text from wiki")
    parser.add_argument('--function', type=str, default='stanford', help="the co-reference function")
    parser.add_argument('--task', type=str, default='parse_one', choices=["parse_all", "parse_one"], help="the task")
    args = parser.parse_args()
    if args.task == 'parse_one':
        id2coref_alias = parse_one(args.data_dir, args.function, args.data_id, {})
    else:
        # parse all
        origin_path = os.path.join(args.data_dir, f'standard_{args.src_text}.txt')
        lines = open(origin_path, 'r').readlines()
        turns = int(len(lines) / (args.processes - 1))
        id2coref_alias = {}
        for i in range(args.processes):
            start_idx = i * turns
            id2coref_alias = parse_one(args.data_dir, args.function, start_idx, id2coref_alias)

    # dump
    output_path = os.path.join(args.data_dir, f"coref_{args.function}_{args.task}_{args.src_text}.json")
    with open(output_path, "w") as fout:
        fout.write(json.dumps(id2coref_alias, ensure_ascii=False))


if __name__ == '__main__':
    main()

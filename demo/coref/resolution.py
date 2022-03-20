import json
import os
from tqdm import tqdm
import requests
import argparse
from stanfordnlp.server import CoreNLPClient
import multiprocessing


def check_fout(path):
    if os.path.exists(path):
        os.remove(path)
    fout = open(path, 'a')
    return fout


def restrict_length(_text, max_len=512):
    sentences = _text.split("::;")
    final_text = ""
    total_len = 0
    for sentence in sentences:
        sent_len = len(sentence.split())
        total_len += sent_len
        if total_len > max_len:
            break
        final_text += sentence + ' '
    return final_text.strip()


def parse_xlink_text(text):
    raw_text = ""
    entity_list = []
    state = 0
    ent_id = None
    start_idx = None
    for index, ch in enumerate(text):
        if state == 0:
            if ch == '[':
                state = 1
            else:
                raw_text += ch
        elif ch == '[' and state == 1:
            state = 2
            # start_idx for entity id
            start_idx = index + 1
        elif ch == '|' and state == 2:
            ent_id = text[start_idx:index]
            # start_idx for entity name
            start_idx = index + 1
            state = 3
        elif ch == ']' and state == 3:
            ent_name = text[start_idx:index]
            # entity has id and name
            entity_list.append([ent_id, ent_name])
            raw_text += ent_name
            state = 4
        elif ch == ']' and state == 4:
            state = 0

    return raw_text, entity_list


def get_coref_result(input_json, function="spanBert"):
    if function == "spanBert":
        # Use spanBert API on our server
        data_str = json.dumps(input_json)
        print("input_json is ", data_str)
        r = requests.post("http://103.238.162.32:4414/", data=data_str)
        print("return", r.text)
        quit(0)
        return r.text
    elif function == "stanford":
        # submit the request to the server
        print("input_json is ", input_json["Text"])
        with CoreNLPClient(annotators=['coref'],
                           timeout=30000, memory='16G') as client:
            ann = client.annotate(input_json["Text"])
            result = ann.corefChain
            print("return", result)
            quit(0)
    else:
        return input_json


def parse_and_coref(args):
    src_file_path = os.path.join(args.data_dir, f"standard_{args.src_text}.txt")
    tgt_file_path = os.path.join(args.data_dir, f"coref_{args.src_text}.json")
    fout = check_fout(tgt_file_path)
    with open(src_file_path, 'r') as fin:
        lines = fin.readlines()
        total_num = len(lines)
        batch = []
        entity_lists = []
        for line in tqdm(lines, total=total_num):
            id_and_txt = line.split('\t\t')
            _id = id_and_txt[0]
            # spanBert has a length limit
            _text = restrict_length(id_and_txt[1], args.max_len)
            raw_text, entity_list = parse_xlink_text(_text)
            coref_input_json = {"ID": _id, "Text": raw_text}
            batch.append(coref_input_json)
            entity_lists.append(entity_list)
            # output
            if len(batch) == args.batch_size:
                coref_result_json_str = get_coref_result(batch, args.function)
                coref_result_json = json.loads(coref_result_json_str)
                for i, _coref_result_json in enumerate(coref_result_json):
                    _coref_result_json["entity_list"] = entity_lists[i]
                    _coref_result_json["speakers"] = []
                    # write to json
                    fout.write(json.dumps(_coref_result_json))
                    fout.write("\n")
                # init
                batch = []
                entity_lists = []


def parse(args):
    src_file_path = os.path.join(args.data_dir, f"standard_{args.src_text}.txt")
    tgt_file_path = os.path.join(args.data_dir, f"standard_{args.src_text}.json")
    fout = check_fout(tgt_file_path)
    with open(src_file_path, 'r') as fin:
        lines = fin.readlines()
        total_num = len(lines)
        for line in tqdm(lines, total=total_num, desc="parsing"):
            id_and_txt = line.split('\t\t')
            _id = id_and_txt[0]
            # spanBert has a length limit
            _text = restrict_length(id_and_txt[1], args.max_len)
            raw_text, entity_list = parse_xlink_text(_text)
            coref_input_json = {"ID": _id, "Text": raw_text}
            out_json = {"entity_list": entity_list, "coref_input": coref_input_json}
            # write to json
            fout.write(json.dumps(out_json))
            fout.write("\n")


def label_stanford_coref(lines, start_idx, data_dir, language):
    tgt_file_path = os.path.join(data_dir, f"stanford_coref_{start_idx}.json")
    fout = check_fout(tgt_file_path)
    total_num = len(lines)
    if language == "chinese":
        with CoreNLPClient(
                properties="chinese",
                annotators=['coref'],
                endpoint=f"http://localhost:{5414 + start_idx % 4}",
                timeout=30000, memory='16G') as client:
            for line in tqdm(lines, total=total_num):
                _input_json = json.loads(line)
                text = _input_json["coref_input"]["Text"]
                try:
                    ann = client.annotate(text)
                    result = ann.corefChain
                    document = [[str(token.word) for token in sentence.token] for sentence in ann.sentence]
                    out_json = {"input": _input_json, "coref": str(result), "document": document}
                    # write to json
                    fout.write(json.dumps(out_json, ensure_ascii=False))
                    fout.write("\n")
                except Exception:
                    continue
    else:
        with CoreNLPClient(annotators=['coref'],
                           timeout=30000, memory='16G') as client:
            for line in tqdm(lines, total=total_num):
                _input_json = json.loads(line)
                text = _input_json["coref_input"]["Text"]
                ann = client.annotate(text)
                result = ann.corefChain
                out_json = {"input": _input_json, "coref": str(result)}
                # write to json
                fout.write(json.dumps(out_json))
                fout.write("\n")
    return None


def coref_stanford(args):
    src_file_path = os.path.join(args.data_dir, f"standard_{args.src_text}.json")

    with open(src_file_path, 'r') as fin:
        lines = fin.readlines()
        turns = int(len(lines) / (args.processes - 1))
        lst = []
        for i in range(args.processes):
            start_idx = i * turns
            end_idx = (i + 1) * turns
            input_param = (lines[start_idx:end_idx], start_idx, args.data_dir, args.language)
            lst.append(input_param)

        with multiprocessing.Pool(processes=args.processes) as pool:
            rslt = pool.starmap(label_stanford_coref, lst)
            pool.close()
            pool.join()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--language', type=str, default='chinese')
    parser.add_argument('--max_len', type=int, default=256)
    parser.add_argument('--batch_size', type=int, default=8)
    parser.add_argument('--processes', type=int, default=8)
    parser.add_argument('--src_text', type=str, default='abstract', help="the input text from wiki")
    parser.add_argument('--function', type=str, default='spanBert', help="the co-reference function")
    parser.add_argument('--task', type=str, default='parse', help="the task")
    args = parser.parse_args()
    if args.task == 'parse_and_coref':
        parse_and_coref(args)
    elif args.task == 'parse':
        parse(args)
    elif args.task == 'coref':
        if args.function == 'stanford':
            coref_stanford(args)


if __name__ == '__main__':
    main()

import argparse
import os
import json
import pickle
from tqdm import tqdm


def check_fout(path):
    if os.path.exists(path):
        os.remove(path)
    fout = open(path, 'a')
    return fout


def reverse_read(src_file_path):
    """
    :param src_file_path: A file which stores the mentions and their entity ids
                          We suppose each entity is unique, one entity can have different mentions.
    :return: Dict: key: entity_id, value: a list of mentions
    """
    id2mention = {}
    with open(src_file_path, 'r') as fin:
        lines = fin.readlines()
        len_lines = len(lines)
        for line in tqdm(lines, total=len_lines):
            pieces = line.strip().split('::=')
            mention = pieces[0]
            ids = pieces[1:]
            for entity_id in ids:
                try:
                    id2mention[entity_id].append(mention)
                except KeyError:
                    # We use list but not set. Maybe it will have duplicate mentions, let's see.
                    id2mention[entity_id] = [mention]

    return id2mention


def get_id2mention(args):
    src_file_path = os.path.join(args.data_dir, args.src_file)
    id2mention = reverse_read(src_file_path)
    pkl_result_file_path = os.path.join(args.data_dir, "{}.pkl".format(args.result_file_name))
    with open(pkl_result_file_path, 'wb') as fout:
        pickle.dump(id2mention, fout)
    print("[1]Finish reading")
    # save
    json_result_file_path = os.path.join(args.data_dir, "{}.json".format(args.result_file_name))
    with open(json_result_file_path, 'w') as json_file:
        res = json.dumps(id2mention, sort_keys=False, indent=4)
        json_file.write(res)
    print("[2]Save {}".format(json_result_file_path))
    txt_result_file_path = os.path.join(args.data_dir, "{}.txt".format(args.result_file_name))
    with open(txt_result_file_path, 'w') as txt_file:
        for entity_id, mentions in id2mention.items():
            line = entity_id
            for mention in mentions:
                line = line + "::=" + mention
            txt_file.write(line)
            txt_file.write('\n')
    print("[3]Save {}".format(txt_result_file_path))
    txt_multi_mention_path = os.path.join(args.data_dir, "{}_multi.txt".format(args.result_file_name))
    with open(txt_multi_mention_path, 'w') as txt_file:
        for entity_id, mentions in id2mention.items():
            if len(mentions) < 2:
                continue
            line = entity_id
            for mention in mentions:
                line = line + "::=" + mention
            txt_file.write(line)
            txt_file.write('\n')
    print("[4]Save {}".format(txt_result_file_path))


def get_id2ent_name(args):
    src_file_path = os.path.join(args.data_dir, args.src_file)
    id2ent_name = {}
    with open(src_file_path, 'r') as fin:
        lines = fin.readlines()
        len_lines = len(lines)
        for line in tqdm(lines, total=len_lines):
            pieces = line.strip('\n').split('\t\t')
            bdi = pieces[-1]
            assert len(pieces) == 4
            if pieces[1] == '':
                ent_name = pieces[0]
            else:
                # because in the mention text, there are hardly ever full name, we have to change it
                # ent_name = pieces[0] + pieces[1]
                ent_name = pieces[0]
                # print("Error in reading line {}".format(i))
                # print(line)
                # raise RuntimeError
            id2ent_name[bdi] = ent_name
    print("[1]Finish reading")
    result_path = os.path.join(args.data_dir, "{}.pkl".format(args.result_file_name))
    with open(result_path, 'wb') as fout:
        pickle.dump(id2ent_name, fout)
        print("[2]Save {}".format(result_path))


def get_mention2ids(args):
    src_file_path = os.path.join(args.data_dir, args.src_file)
    mention2ids = {}
    with open(src_file_path, 'r') as fin:
        lines = fin.readlines()
        len_lines = len(lines)
        for line in tqdm(lines, total=len_lines):
            pieces = line.strip('\n').split('::=')
            mention = pieces[0]
            ids = pieces[1:]
            mention2ids[mention] = ids

    print("[1]Finish reading")
    result_path = os.path.join(args.data_dir, "{}.pkl".format(args.result_file_name))
    with open(result_path, 'wb') as fout:
        pickle.dump(mention2ids, fout)
        print("[2]Save {}".format(result_path))


def get_instance_alias(args):
    id2mention_path = os.path.join(args.data_dir, 'id2mention.json')
    id2ent_name_path = os.path.join(args.data_dir, 'id2ent_name.pkl')
    result_file_path = os.path.join(args.data_dir, "{}.txt".format(args.result_file_name))
    fout = check_fout(result_file_path)
    with open(id2mention_path, 'r') as fin:
        id2mention = json.load(fin)
        id2ent_name = pickle.load(open(id2ent_name_path, 'rb'))
        for k, ent_name in id2ent_name.items():
            if k in id2mention.keys():
                mentions = id2mention[k]
                if len(mentions) > 1:
                    mentions = [mention for mention in mentions if mention != ent_name]
                    mention_str = "::;".join(mentions)
                    line = "\t\t".join([ent_name, k, mention_str])
                    fout.write(line)
                    fout.write("\n")
                elif mentions[0] != ent_name:
                    line = "\t\t".join([ent_name, k, mentions[0]])
                    fout.write(line)
                    fout.write("\n")


def get_zeshel_mention(args):
    splits = ['train', 'valid', 'test']
    id2mention = {}
    id2ent_name = {}
    mention2ids = {}
    for split in splits:
        src_file = os.path.join(args.data_dir, f"{split}.jsonl")
        with open(src_file, 'r') as fin:
            lines = fin.readlines()
            len_lines = len(lines)
            for line in tqdm(lines, total=len_lines):
                data_dict = json.loads(line)
                entity_id = str(data_dict['label_id'])
                entity_name = data_dict['label_title'].lower()
                mention = data_dict['mention']
                # id2mention
                try:
                    if mention not in id2mention[entity_id]:
                        id2mention[entity_id].append(mention)
                except KeyError:
                    id2mention[entity_id] = [mention]
                # mention2ids
                try:
                    if entity_id not in mention2ids[mention]:
                        mention2ids[mention].append(entity_id)
                except KeyError:
                    mention2ids[mention] = [entity_id]
                # entity_name
                id2ent_name[entity_id] = entity_name
                # mention2ids for entity_name
                try:
                    if entity_id not in mention2ids[entity_name]:
                        mention2ids[entity_name].append(entity_id)
                except KeyError:
                    mention2ids[entity_name] = [entity_id]
    print("[1]Finish reading")
    id2mention_path = os.path.join(args.data_dir, 'id2mention.json')
    id2ent_name_path = os.path.join(args.data_dir, 'id2ent_name.pkl')
    id2ent_name_txt_path = os.path.join(args.data_dir, 'id2ent_name.txt')
    with open(id2ent_name_path, 'wb') as fout:
        pickle.dump(id2ent_name, fout)
        print("[2]Save {}".format(id2ent_name_path))
        with open(id2ent_name_txt_path, 'w') as txt_fout:
            for ent_id, ent_name in id2ent_name.items():
                line = ent_id + "::=" + ent_name
                txt_fout.write(line)
                txt_fout.write('\n')

    with open(id2mention_path, 'w') as json_file:
        res = json.dumps(id2mention, sort_keys=False, indent=4)
        json_file.write(res)
        print("[3]Save {}".format(id2mention_path))

    txt_multi_mention_path = os.path.join(args.data_dir, 'mention_anchors.txt')
    with open(txt_multi_mention_path, 'w') as txt_file:
        for mention, entity_ids in mention2ids.items():
            line = mention
            for entity_id in entity_ids:
                line = line + "::=" + str(entity_id)
            txt_file.write(line)
            txt_file.write('\n')
    print("[4]Save {}".format(txt_multi_mention_path))


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--data_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--src_file', type=str, default='mention_anchors.txt',
                        choices=['mention_anchors.txt', 'bd_instance_ID.txt'])
    parser.add_argument('--result_file_name', type=str, default='id2mention')
    parser.add_argument('--task', type=str, default='id2mention', choices=['id2mention', 'id2ent_name',
                                                                           'mention2ids', 'instance_alias',
                                                                           'zeshel'])
    args = parser.parse_args()
    if args.task == 'id2mention':
        get_id2mention(args)
    elif args.task == 'id2ent_name':
        get_id2ent_name(args)
    elif args.task == 'mention2ids':
        get_mention2ids(args)
    elif args.task == 'instance_alias':
        get_instance_alias(args)
    elif args.task == 'zeshel':
        get_zeshel_mention(args)


if __name__ == '__main__':
    work()

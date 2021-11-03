import argparse
import os
import json


def reverse_read(src_file_path):
    """
    :param src_file_path: A file which stores the mentions and their entity ids
                          We suppose each entity is unique, one entity can have different mentions.
    :return: Dict: key: entity_id, value: a list of mentions
    """
    id2mention = {}
    with open(src_file_path, 'r') as fin:
        lines = fin.readlines()
        for line in lines:
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


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--data_dir', type=str, default='/data/tsq/xlink/bd')
    parser.add_argument('--src_file', type=str, default='mention_anchors.txt')
    parser.add_argument('--result_file_name', type=str, default='id2mention')
    args = parser.parse_args()
    src_file_path = os.path.join(args.data_dir, args.src_file)
    id2mention = reverse_read(src_file_path)
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


if __name__ == '__main__':
    work()

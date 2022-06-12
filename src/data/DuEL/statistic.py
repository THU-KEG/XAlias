import argparse
import json
import os


def work():
    parser = argparse.ArgumentParser()
    # path params
    parser.add_argument('--data_dir', type=str, default='/data/tsq/DuEL')
    parser.add_argument('--pic_dir', type=str, default='/home/tsq/ybb/pic')
    parser.add_argument('--observe_alias_num', type=int, default=7)
    # task
    parser.add_argument('--task', type=str, default='num_alias',
                        choices=['num_alias', 'observe_alias'])
    args = parser.parse_args()

    if args.task == 'num_alias':
        kb_data_path = os.path.join(args.data_dir, "kb.json")
        with open(kb_data_path, 'r') as fin:
            lines = fin.readlines()
            print(f"Total entity is {len(lines)}")
            num_count = {}
            for line in lines:
                record = json.loads(line.strip())
                alias_table = record["alias"]
                alias_num = len(alias_table)
                try:
                    num_count[alias_num] += 1
                except KeyError:
                    num_count[alias_num] = 1

            # output
            num_count = sorted(num_count.items(), key=lambda item: item[0])
            for k, v in num_count:
                print(f"{v} entities has {k} aliases")
    elif args.task == 'observe_alias':
        kb_data_path = os.path.join(args.data_dir, "kb.json")
        with open(kb_data_path, 'r') as fin:
            lines = fin.readlines()
            for line in lines:
                record = json.loads(line.strip())
                alias_table = record["alias"]
                if len(alias_table) == args.observe_alias_num:
                    name = record["subject"]
                    print(f"{name}'s alias table is:")
                    print(alias_table)
                    

if __name__ == '__main__':
    work()

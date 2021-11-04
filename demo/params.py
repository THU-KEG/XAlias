import argparse

BMINF_FILL_KEYS = ['top_p', 'top_n', 'temperature', 'frequency_penalty', 'presence_penalty']
BMINF_SAMLE_KEYS = ['max_tokens', 'top_n', 'top_p', 'temperature', 'frequency_penalty',
                    'presence_penalty']
BMINF_BEAM_KEYS = ['max_tokens',  'num_beams', 'num_return_sequences']


def get_decode_param():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', type=str, default='beam', choices=['beam', 'sample', 'greedy'])
    # parser.add_argument('--min_length', type=int, default=10)
    # parser.add_argument('--max_length', type=int, default=20)
    args = parser.parse_args()
    if args.s == 'beam':
        return get_beam_param(args)
    elif args.s == 'sample':
        return get_sample_param(args)
    else:
        return args


def get_beam_param(args):
    args.num_beams = getattr(args, 'num_beams', 4)
    args.num_beam_groups = getattr(args, 'num_beam_groups', 4)
    args.num_return_sequences = getattr(args, 'num_return_sequences', 4)
    args.no_repeat_ngram_size = getattr(args, 'no_repeat_ngram_size', 3)
    args.diversity_penalty = getattr(args, 'diversity_penalty', 1.0)
    args.length_penalty = getattr(args, 'length_penalty', 1.0)
    args.early_stopping = getattr(args, 'early_stopping', False)
    """    
    parser.add_argument('--num_beams', type=int, default=4)
    parser.add_argument('--num_beam_groups', type=int, default=4)
    parser.add_argument('--no_repeat_ngram_size', type=int, default=3)
    parser.add_argument('--diversity_penalty', type=float, default=1.0)
    parser.add_argument('--length_penalty', type=float, default=1.0)
    parser.add_argument('--early_stopping', action='store_true')
    """

    return args


def get_sample_param(args):
    args.top_k = getattr(args, 'top_k', 20)
    args.top_p = getattr(args, 'top_p', 0.95)
    args.num_return_sequences = getattr(args, 'num_return_sequences', 4)
    args.do_sample = getattr(args, 'do_sample', True)
    """ 
    parser.add_argument('--top_k', type=int, default=20)
    parser.add_argument('--top_p', type=float, default=0.95)
    parser.add_argument('--num_return_sequences', type=int, default=4)
    parser.add_argument('--do_sample', action='store_false')
    """
    return args


def reduce_args(args):
    args_dict = vars(args)
    if args.task == 'fill':
        kwargs = {k: args_dict[k] for k in BMINF_FILL_KEYS}
    elif args.task == 'generate':
        if args.num_beams is None:
            kwargs = {k: args_dict[k] for k in BMINF_SAMLE_KEYS}
        else:
            kwargs = {k: args_dict[k] for k in BMINF_BEAM_KEYS}
    else:
        kwargs = {}
    return kwargs


def get_bminf_param():
    parser = argparse.ArgumentParser()
    # task params
    parser.add_argument('--source_word', type=str, default='北京大学', choices=['北京大学', '清华大学', '江西省', '北京'])
    parser.add_argument('--language', type=str, default='ch', choices=['en', 'ch'])
    parser.add_argument('--task', type=str, default='generate', choices=['fill', 'generate'])
    # gpu device
    parser.add_argument('--gpu_id', type=int, default=0)
    # shared decode params
    parser.add_argument('--seed', type=int, default=1453)
    parser.add_argument('--top_p', type=float, default=None)
    parser.add_argument('--top_n', type=int, default=5)
    parser.add_argument('--temperature', type=float, default=0.85)
    parser.add_argument('--frequency_penalty', type=float, default=0)
    parser.add_argument('--presence_penalty', type=float, default=0)
    # generate task params
    parser.add_argument('--max_tokens', type=int, default=16)
    # beam search
    parser.add_argument('--num_beams', type=int, default=2)
    parser.add_argument('--num_return_sequences', type=int, default=None)

    args = parser.parse_args()
    kwargs = reduce_args(args)

    return args, kwargs

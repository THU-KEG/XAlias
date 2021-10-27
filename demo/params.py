import argparse


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

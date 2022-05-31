import argparse
from src.model.const import few_shot_alias_table

BMINF_FILL_KEYS = ['top_p_cpm', 'top_n', 'temperature', 'frequency_penalty', 'presence_penalty']
BMINF_SAMLE_KEYS = ['max_tokens', 'top_n', 'top_p_cpm', 'temperature', 'frequency_penalty',
                    'presence_penalty']
BMINF_BEAM_KEYS = ['max_tokens', 'num_beams_cpm', 'num_return_sequences']


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
    if args.alias_task == 'fill':
        kwargs = {k: args_dict[k] for k in BMINF_FILL_KEYS}
    elif args.alias_task == 'generate':
        if args.num_beams_cpm is None:
            kwargs = {k: args_dict[k] for k in BMINF_SAMLE_KEYS}
        else:
            kwargs = {k: args_dict[k] for k in BMINF_BEAM_KEYS}
    else:
        kwargs = {}
    return kwargs


def add_decode_param(parser: argparse.ArgumentParser):
    # verbalize params
    parser.add_argument('--language', type=str, default='ch', choices=['en', 'ch'])
    parser.add_argument('--model_name', type=str, default='cpm2', choices=['cpm2', 'glm'])
    parser.add_argument('--alias_task', type=str, default='generate', choices=['fill', 'generate'])
    # gpu device
    parser.add_argument('--gpu_id', type=int, default=0)
    # shared decode params
    parser.add_argument('--seed', type=int, default=1453)
    parser.add_argument('--top_p_cpm', type=float, default=None) # conflict with glm, we used to use None, but glm use 0
    parser.add_argument('--top_n', type=int, default=5)
    parser.add_argument('--temperature', type=float, default=0.9)
    parser.add_argument('--frequency_penalty', type=float, default=0)
    parser.add_argument('--presence_penalty', type=float, default=0)
    # how to process the generated strings
    parser.add_argument('--redundancy_strategy', type=str, default='overlap', choices=[None, 'overlap'])
    parser.add_argument('--max_overlap_scale', type=float, default=1,
                        help="str whose len(overlap with prev_str) * mos >= len(str) will be removed")
    parser.add_argument('--punctuation_strategy', type=str, default='lazy', choices=[None, 'lazy', 'all'])
    # generate task params
    parser.add_argument('--max_tokens', type=int, default=2)
    parser.add_argument('--max_tokens_scale', type=float, default=2,
                        help='the mt will be mts * len(sw) or len(sw) / mts')
    # sample
    parser.add_argument('--top_n_range', type=int, default=4,
                        help='the top_n will be [top_n-top_n_range, top_n+top_n_range]')
    parser.add_argument('--cpm2_concat_value_string', type=str, default='concat',
                        choices=[None, 'concat'],
                        help='When decoded text is short, whether to concat generated text with src_word as input')
    # beam search
    parser.add_argument('--num_beams_cpm', type=int, default=None)
    parser.add_argument('--num_return_sequences', type=int, default=500)
    parser.add_argument('--num_generate_sequences', type=int, default=1)
    return parser


def add_rescore_param(parser: argparse.ArgumentParser):
    parser.add_argument('--candidate_num', type=int, default=20)
    # ppl score
    parser.add_argument('--score_kind', type=str, default='ppl', help="the kind of score")
    parser.add_argument('--max_attribute_num', type=int, default=2)
    # info box
    parser.add_argument('--concat_way', type=str, default='distributed', choices=['distributed', 'string'],
                        help="how to concat different attribute")
    parser.add_argument('--attribute_value', type=str, default='use', choices=['use', 'ignore'],
                        help="how to concat different attribute")
    return parser


def add_test_param(parser: argparse.ArgumentParser):
    # data param
    parser.add_argument('--test', action="store_true")
    parser.add_argument('--fast', action="store_true")
    parser.add_argument('--example_num', type=int, default=20)
    parser.add_argument('--alias_type', default='synonym',
                        choices=['prefix_extend', 'prefix_reduce', 'suffix_extend', 'suffix_reduce',
                                 'expansion', 'abbreviation', 'punctuation', 'synonym'])
    parser.add_argument('--result_dir', default='/data/tsq/xlink/bd/purify/filter_english/pool_80/result')
    parser.add_argument('--data_path',
                        default='/data/tsq/xlink/bd/purify/filter_english/pool_80/has_alias_relation_record.pkl')

    # Whether to use data
    parser.add_argument('--learning', type=str, default='few_shot',
                        choices=['zero_shot', 'few_shot'])
    # few_shot
    parser.add_argument('--extra_prompt', type=str, default='task_specific',
                        choices=['task_specific', 'prefix_tuning'])
    parser.add_argument('--task_specific_prompt_num', type=int, default=4)
    parser.add_argument('--alias_table_num', type=int, default=1, help="how many  alias_tables will be sampled")
    parser.add_argument('--task_definition', action="store_true")
    parser.add_argument('--alias_example_strategy', type=str, default='random',
                        choices=['random', 'cluster'])
    parser.add_argument('--alias_data_source', type=str, default='support_pool',
                        choices=['whole_dataset', 'support_pool'])
    # re-rank
    parser.add_argument('--rank_strategy', type=str, default='frequency',
                        choices=['random', 'frequency', 'probability', 'prob_freq', 'ppl'])
    parser.add_argument('--freq_portion', type=float, default=0.5, help="how many portion will frequency has in weight")
    # parser.add_argument('--calculate_prob', type=str, default='origin',
    #                     choices=['origin', 'softmax'],
    #                     help="how to transfer the logits of CPM2 to probability used in ranking")
    return parser


def get_bminf_param():
    parser = argparse.ArgumentParser()
    # task params
    # parser.add_argument('--source_word', type=str, default='北京大学', choices=['北京大学', '清华大学', '北京航空航天大学', '江西省', '北京'])
    parser.add_argument('--source_word', type=str, default='北京大学')
    # prompt parameter
    parser.add_argument('--prefix_type', type=str, default='void', choices=few_shot_alias_table['ch'].keys())
    parser = add_decode_param(parser)

    args = parser.parse_args()
    kwargs = reduce_args(args)

    return args, kwargs

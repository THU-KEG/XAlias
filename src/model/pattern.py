import argparse
import logging
from src.model.GLM.generate_samples import call_glm_generate
import bminf
import numpy as np
import stanfordnlp
from src.model.decode import beam_search, Beam, generate_return_beam
from src.data.discover_alias import punctuation
from difflib import SequenceMatcher
from src.model.const import patterns, few_shot_alias_table
from collections import Counter
from typing import List, Tuple

signal_arg_keys = ['max_tokens_scale', 'top_n_range']


# signal_arg_keys = []


def strip_redundant_words(words, max_overlap_scale: float):
    if max_overlap_scale == 1:
        # print("[2]max_overlap_scale is 1")
        chosen_words = list(set(words))
    else:
        chosen_words = []
        for word in words:
            flag = False
            for prev_word in chosen_words:
                s = SequenceMatcher(None, word, prev_word)
                overlap = s.find_longest_match(0, len(word), 0, len(prev_word)).size

                if overlap * max_overlap_scale >= min(len(word), len(prev_word)):
                    flag = True
                    break

            if not flag:
                chosen_words.append(word)

    return chosen_words


class Verbalizer(object):
    def __init__(self, language, task):
        """
        :param language: en / ch
        :param task: 'fill' / 'generate'
        """
        self.language = language
        self.task = task
        self.patterns = patterns[language][task]
        self.g_patterns = patterns[language]['generate']
        # cpm2 param
        self.model = None
        self.kwargs = None
        self.args = None
        self.signal_args = {}
        # glm params
        self.glm_args = None
        self.tokenizer = None
        self.device = None
        # stanford nlp
        self.nlp = None

    def convert_all(self, prefix_type, src_word, task_def=False, alias_table=None):
        if alias_table is None:
            alias_table = few_shot_alias_table[self.language][prefix_type]
        results = []
        for p_id in range(len(self.patterns[prefix_type])):
            prefix = ''
            if task_def:
                if self.language == 'ch':
                    prefix += '接下来进行别名生成，比如'
                else:
                    prefix += 'Next we will generate alias. Such as'
            if prefix_type != 'void':
                for key_word, alias_list in alias_table.items():
                    for alias in alias_list:
                        if self.language == 'ch':
                            prefix += key_word + self.g_patterns[prefix_type][p_id] + alias + '，'
                        else:
                            prefix += key_word + ' ' + self.g_patterns[prefix_type][p_id] + ' ' + alias + '. '
            sequence = self.convert(prefix, prefix_type, src_word, p_id)
            results.append(sequence)
        return results

    def convert(self, prefix, prefix_type, src_word, pattern_id=0):
        pattern = self.patterns[prefix_type][pattern_id]
        if self.language == 'ch':
            if self.glm_args:
                return prefix + src_word + pattern + '[MASK]。'
            return prefix + src_word + pattern
        else:
            # only glm
            return prefix + ' ' + src_word + ' ' + pattern + ' [MASK].'

    def set_cpm2(self, model: bminf.models.CPM2, kwargs: dict, args: argparse.ArgumentParser):
        self.model = model
        self.kwargs = kwargs
        self.args = args
        if 'top_p_cpm' in self.kwargs.keys():
            self.kwargs['top_p'] = self.kwargs['top_p_cpm']
            del self.kwargs['top_p_cpm']
        if 'num_beams_cpm' in self.kwargs.keys():
            self.kwargs['num_beams'] = self.kwargs['num_beams_cpm']
            del self.kwargs['num_beams_cpm']
        for k in signal_arg_keys:
            v = args.__dict__[k]
            # if k == 'alias_table_num':
            #     # default is 1, when > 1 , it provides us extra results by changing alias table
            #     if v > 1:
            #         self.signal_args[k] = v
            # else:
            # default is None
            if v is not None:
                self.signal_args[k] = v

    def set_glm(self, args: argparse.ArgumentParser, model, tokenizer, glm_args, device):
        # = init_glm()
        self.args = args
        self.model = model
        self.tokenizer = tokenizer
        self.glm_args = glm_args
        self.device = device

    def set_for_rerank(self, args: argparse.ArgumentParser):
        self.args = args
        if self.language == 'ch':
            self.nlp = stanfordnlp.Pipeline(lang='zh', processors='tokenize,mwt,pos')
        else:
            self.nlp = stanfordnlp.Pipeline(lang=self.language, processors='tokenize,mwt,pos')

    def cpm2_beam_search(self, text):
        result_strings = beam_search(self.model, text, **self.kwargs)
        return result_strings

    def cpm2_sample(self, text) -> Beam:
        stoped = False
        total_len = 0
        result_beam = None
        while not stoped:
            if total_len > self.kwargs['max_tokens']:
                break
            value, stoped = generate_return_beam(
                self.model,
                text, **self.kwargs
            )
            value_string = value.tokens
            if result_beam:
                # merge the 2 beams
                result_beam.tokens += value_string
                result_beam.log_probs += value.log_probs
            else:
                result_beam = value
            total_len += len(value_string)
            if self.args.cpm2_concat_value_string == 'concat':
                text += value_string

        return result_beam

    def pattern_num(self, prefix_type):
        return len(self.g_patterns[prefix_type])

    def cpm2_gen_by_prompt(self, prefix_type, src_word, task_def, alias_tables=None) \
            -> Tuple[List[List[str]], List[List]]:
        pattern2beams = [[] for _ in range(self.pattern_num(prefix_type))]
        for alias_table in alias_tables:
            input_texts = self.convert_all(prefix_type, src_word, task_def, alias_table)
            for pattern_id, input_text in enumerate(input_texts):
                if self.task == 'fill':
                    # fill_blank(model, input_text, kwargs)
                    return [['']], [[]]
                else:
                    beams = []
                    if 'num_beams' in self.kwargs.keys():
                        # beam search
                        beams = self.cpm2_beam_search(input_text)
                    else:
                        # sample with different params
                        passes = self.args.num_generate_sequences // (len(self.signal_args) * len(alias_tables))
                        rotation_num = 1 + passes
                        for i in range(rotation_num):
                            if len(beams) >= self.args.num_generate_sequences:
                                break
                            np.random.seed(i * self.args.seed)
                            if len(self.signal_args) > 0:
                                # change args
                                for signal_arg in self.signal_args:
                                    if signal_arg == 'max_tokens_scale':
                                        l_sw = len(src_word)
                                        if i % 3 == 0:
                                            self.kwargs['max_tokens'] = int(l_sw * self.signal_args['max_tokens_scale'])
                                        elif i % 3 == 1:
                                            self.kwargs['max_tokens'] = l_sw
                                        else:
                                            self.kwargs['max_tokens'] = int(l_sw / self.signal_args['max_tokens_scale'])
                                    elif signal_arg == 'top_n_range':
                                        tnr_order = i % (2 * self.signal_args['top_n_range'])
                                        self.kwargs['top_n'] = self.args.top_n - self.signal_args[
                                            'top_n_range'] + tnr_order
                                    # generate with new kwargs
                                    new_beam = self.cpm2_sample(input_text)
                                    beams.append(new_beam)
                            else:
                                # only change seed
                                beams.append(self.cpm2_sample(input_text))
                    pattern2beams[pattern_id].extend(beams)
        # process and truncate
        final_pattern2strings = []
        for beams in pattern2beams:
            pure_strings = self.process(beams)
            final_pattern2strings.append(pure_strings[:self.args.num_return_sequences])
        return final_pattern2strings, pattern2beams

    def process(self, beams: List[Beam]) -> List[str]:
        # default strategy is None
        # print("[0] enter process", strings)
        if self.args.punctuation_strategy:
            beams = self.rm_punctuation(beams)
        if self.args.rank_strategy != 'random':
            strings = self.rank(beams)
        else:
            # don't need rank
            if self.args.redundancy_strategy:
                # print("[1] Before rm_redundancy", strings)
                strings = self.rm_redundancy(beams)
                # print("[3] After rm_redundancy", strings)
            # print("[4] out process", strings)
            else:
                strings = [b.tokens for b in beams]
        return strings

    def rm_punctuation(self, beams: List[Beam]) -> List[Beam]:
        tidy_beams = []
        stopped_chars = "！？，｡、＂＇（）：；\n"
        if self.args.punctuation_strategy == 'lazy':
            # only split the ， 。 \n
            separated_chars = '，。\n'
        else:
            separated_chars = stopped_chars
        for beam in beams:
            string = beam.tokens
            striped = string.strip(stopped_chars)
            tidy_beams.append(Beam(striped, beam.log_probs, beam.context))
            for separated_char in separated_chars:
                if separated_char in striped:
                    sp_words = striped.split(separated_char)
                    # new beam will success the prob
                    new_beams = [Beam(word, beam.log_probs, beam.context) for word in sp_words]
                    tidy_beams.extend(new_beams)
        return tidy_beams

    def rm_redundancy(self, beams: List[Beam]) -> List[str]:
        tidy_strings = []
        strings = [b.tokens for b in beams]
        if self.args.redundancy_strategy == 'overlap':
            tidy_strings = strip_redundant_words(strings, self.args.max_overlap_scale)
        return tidy_strings

    def rank(self, beams: List[Beam]) -> List[str]:
        ranked_strings = []
        strings = [b.tokens for b in beams]
        if self.args.rank_strategy == 'frequency':
            # sort by frequency of words
            counter = Counter(strings)
            ranked_string_tuples = counter.most_common(self.args.num_return_sequences)
            ranked_strings = [t[0] for t in ranked_string_tuples]
        elif self.args.rank_strategy == 'probability':
            # sort by average probability of token
            _beams = []
            str2beam_index = set()
            for beam in beams:
                string = beam.tokens
                if string not in str2beam_index:
                    # new string
                    _beams.append(beam)
                    str2beam_index.add(string)
            # However, different beams with same tokens may have different probs due to their succession
            _beams.sort(key=lambda b: b.avg_log_prob, reverse=True)
            ranked_strings = [b.tokens for b in _beams]
        elif self.args.rank_strategy == 'prob_freq':
            # sort by weighted frequency
            # weight is average probability of token
            freq_beams = []
            str2beam_index = {}
            for beam in beams:
                string = beam.tokens
                try:
                    beam_index = str2beam_index[string]
                    freq_beams[beam_index].set_freq()
                except KeyError:
                    # new string
                    str2beam_index[string] = len(freq_beams)
                    beam.set_freq(init=True)
                    freq_beams.append(beam)
            freq_beams.sort(key=lambda b: b.log_freq_add_prob(self.args.freq_portion), reverse=True)
            ranked_strings = [b.tokens for b in freq_beams]
        return ranked_strings

    def rerank(self, src_word, pattern2beams):
        # process and truncate
        final_pattern2strings = []
        for beams in pattern2beams:
            pred_words = self.process(beams)
            # filter these pred_words by POS parsing
            if self.args.pos_type == 'upos':
                pred_words = self.filter_by_pos(src_word, pred_words)
            final_pattern2strings.append(pred_words[:self.args.num_return_sequences])
        return final_pattern2strings

    def filter_by_pos(self, src_word, pred_words):
        def parse_doc(_pred_word):
            if self.args.concat_parse == 'yes':
                _pred_word = src_word + "叫" + _pred_word
            try:
                _doc = self.nlp(_pred_word)
            except AssertionError:
                print("AssertionError at word {}".format(_pred_word))
                return None
            return _doc

        pure_strings = []
        for pred_word in pred_words:
            if pred_word is None or len(pred_word) <= 0:
                continue
            valid = True
            doc = parse_doc(pred_word)
            if not doc:
                continue
            pos_tags = [word.upos for sent in doc.sentences for word in sent.words]
            src_tags = []
            start_index = 0
            for _index, word in enumerate(doc.sentences[0].words):
                if "叫" in str(word):
                    start_index = _index + 1
                    break
                else:
                    src_tags.append(word.upos)
            pred_pos_tags = pos_tags[start_index:]

            # rule1: contain words that are not permitted
            if 'rule1' in self.args.pos_rules:
                if len(pred_pos_tags) == 0:
                    print("#" * 8)
                    print("No pred_pos_tags")
                    print(pred_word)
                    valid = False
                for pos_tag in pred_pos_tags:
                    if pos_tag not in self.args.permit_pos_tags and pos_tag not in src_tags:
                        print("-" * 8)
                        print("src: ", src_tags)
                        print("pred_pos_tags: ", pred_pos_tags)
                        print(pos_tag)
                        print("No permit_pos_tags and src_tags")
                        print(pred_word)
                        valid = False
                        break
            # rule2: check for punctuation, the punctuation within pred_word is not allowed
            if 'rule2' in self.args.pos_rules:
                if self.args.alias_type == 'punctuation':
                    # On 'punctuation' domain, we permit pred_word starts like 《 or “
                    check_list = pred_pos_tags[1:-1]
                else:
                    if pred_word[-1] in punctuation:
                        continue
                    else:
                        # Because the stanford nlp parser tends to view the last token as PUNCT
                        check_list = pred_pos_tags[:-1]

                if 'PUNCT' in check_list and 'PUNCT' not in src_tags:
                    valid = False

            if valid:
                pure_strings.append(pred_word)

        return pure_strings

    def rerank_stings_with_info_box(self, src_sv, old_pred_words, pred_word2sv):
        score_strings = []
        # check whether the entity has info box
        if not src_sv.attributes:
            return old_pred_words, score_strings
        # only top_k in old_pred_words will participate in re-ranking
        top_k = len(pred_word2sv)
        assert top_k <= len(old_pred_words)
        participate_old_pred_words = old_pred_words[:top_k]
        unparticipate_old_pred_words = old_pred_words[top_k:]
        for i, old_pred_word in enumerate(participate_old_pred_words):
            dic = {'word': old_pred_word, 'score': 0}
            # assign each word with a score
            pred_sv = pred_word2sv[i]
            if self.args.concat_way == 'string':
                if self.args.attribute_value == 'use':
                    # only one ppl
                    perplexity = pred_sv.ppls[0]
                    score = perplexity.ppl
                else:
                    raise ValueError()
            else:
                if self.args.rerank_by == 'similarity':
                    # we will compare similarity between src and pred
                    score = self.get_similarity_from_vectors(src_sv, pred_sv)
                else:
                    # each word has a vector of m scores, will squeeze them into a scalar
                    score = self.get_score_from_vector(pred_sv)

            dic['score'] = score
            score_strings.append(dic)
        # rank by score
        if self.args.score_kind == 'ppl':
            score_strings.sort(key=lambda b: b['score'], reverse=False)
        else:
            score_strings.sort(key=lambda b: b['score'], reverse=True)
        pure_strings = [s['word'] for s in score_strings] + unparticipate_old_pred_words
        final_strings = pure_strings[:self.args.num_return_sequences]
        return final_strings, score_strings

    def get_score_from_vector(self, score_vector):
        final_score = 0
        ppl_list = []
        for ppl in score_vector.ppls:
            ppl_list.append(ppl.ppl)
        if self.args.vector_squeeze_strategy == 'avg':
            final_score = sum(ppl_list) / len(ppl_list)
        elif self.args.vector_squeeze_strategy == 'min':
            final_score = min(ppl_list)
        return final_score

    def get_similarity_from_vectors(self, src_sv, pred_sv):
        """
        :param src_sv: ScoreVector
        :param pred_sv: ScoreVector
        :return: similarity of the 2 vector, float, [0,1]
        """

        # Now we only compare the similarity of the first token,
        # because we don't know how to decode until stop and record this ppl
        def get_sim_vec(score_vector):
            score_list = []
            if self.args.similarity_vector_dimension == 'm':
                for ppl in score_vector.ppls:
                    score_list.append(ppl.ppl)
            elif self.args.similarity_vector_dimension == 'mxd':
                score_list = [token_logit for token_logit in score_vector.last_token_logits]
            return score_list

        final_similarity = 0
        src_vec = get_sim_vec(src_sv)
        pred_vec = get_sim_vec(pred_sv)
        if self.args.vector_similarity == 'cosine':
            if self.args.similarity_vector_dimension == 'm':
                final_similarity = get_cos_similar(src_vec, pred_vec)
            elif self.args.similarity_vector_dimension == 'mxd':
                attribute_num = len(src_vec)
                for i in range(attribute_num):
                    final_similarity += get_cos_similar(src_vec[i], pred_vec[i])
                # final_similarity = get_cos_similar_matrix(src_vec, pred_vec)
        elif self.args.vector_similarity == 'euclid':
            final_similarity = np.linalg.norm(np.array(src_vec) - np.array(pred_vec))
        return float(final_similarity)

    def fast_gen_by_prompt(self, prefix_type, src_word, task_def, alias_tables=None) \
            -> Tuple[List[List[str]], List[List]]:
        pattern2beams = [[] for _ in range(self.pattern_num(prefix_type))]
        for alias_table in alias_tables:
            input_texts = self.convert_all(prefix_type, src_word, task_def, alias_table)
            for pattern_id, input_text in enumerate(input_texts):
                if self.task == 'fill':
                    # fill_blank(model, input_text, kwargs)
                    return [['']], [[]]
                else:
                    beams = []
                    if self.kwargs:
                        #  cpm2 can use beam search there with kwargs
                        if 'num_beams' in self.kwargs.keys():
                            # beam search
                            beams = self.cpm2_beam_search(input_text)
                        else:
                            beams.append(self.cpm2_sample_text(input_text))
                    else:
                        # sample with different params
                        if self.args.model_name == 'cpm2':
                            beams.append(self.cpm2_sample_text(input_text))
                        else:
                            # glm
                            beams.append(self.glm_sample_text(input_text))
                    pattern2beams[pattern_id].extend(beams)
        # process and truncate
        logging.info("raw pattern2beams are:")
        logging.info(pattern2beams)
        final_pattern2strings = []
        for beams in pattern2beams:
            pure_strings = self.fast_process(beams)
            final_pattern2strings.append(pure_strings[:self.args.num_return_sequences])
        return final_pattern2strings, pattern2beams

    def fast_process(self, beams: List[str]) -> List[str]:
        # default strategy is None
        tidy_beams = []
        # deal with punctuation
        if self.args.language == 'ch':
            separated_chars = '，。\n'
            stopped_chars = "！？，｡、＂＇（）：；\n“"
        else:
            separated_chars = [',', '\n', '.', 'or', 'and']
            stopped_chars = "!?,.＇();:\n"
        for beam in beams:
            striped = beam.strip(stopped_chars)
            has_separated_char = False
            for separated_char in separated_chars:
                if separated_char in striped:
                    sp_words = striped.split(separated_char)
                    for sp_word in sp_words:
                        if len(sp_word) > 0:
                            tidy_beams.append(sp_word)
                    has_separated_char = True
            if not has_separated_char and len(striped) > 0:
                tidy_beams.append(striped)
        logging.info("tidy_beams are:")
        logging.info(tidy_beams)
        # sort by frequency of words
        counter = Counter(tidy_beams)
        ranked_string_tuples = counter.most_common(self.args.num_return_sequences)
        ranked_strings = [t[0] for t in ranked_string_tuples]
        logging.info("ranked_strings are:")
        logging.info(ranked_strings)
        # deal with redundancy
        tidy_strings = strip_redundant_words(ranked_strings, self.args.max_overlap_scale)
        return tidy_strings

    def cpm2_sample_text(self, text) -> str:
        stoped = False
        total_len = 0
        result_string = ""
        while not stoped:
            if total_len > self.kwargs['max_tokens']:
                break
            value, stoped = self.model.generate(
                text, **self.kwargs
            )
            result_string += value
            total_len += len(value)

        return result_string

    def glm_sample_text(self, input_text) -> str:
        result_string = call_glm_generate(self.model, self.tokenizer, self.glm_args, self.device, input_text)
        result = result_string.split("<|startofpiece|>")[1].strip()
        return result


def get_cos_similar_matrix(v1, v2):
    num = np.dot(v1, np.array(v2).T)
    denom = np.linalg.norm(v1, axis=1).reshape(-1, 1) * np.linalg.norm(v2, axis=1)
    res = num / denom
    res[np.isneginf(res)] = 0
    return 0.5 + 0.5 * res


def get_cos_similar(v1: list, v2: list):
    num = float(np.dot(v1, v2))
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    return 0.5 + 0.5 * (num / denom) if denom != 0 else 0


"""
    def cpm2_sample(self, text):
        stoped = False
        total_len = 0
        result_string = ""
        while not stoped:
            if total_len > self.kwargs['max_tokens']:
                break
            value, stoped = self.model.generate(
                text, **self.kwargs
            )
            result_string += value
            total_len += len(value)

        return result_string
    

"""

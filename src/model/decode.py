import bminf
import copy
import cupy
import numpy as np
from typing import Optional, Tuple, Union, List

SPAN_TOKEN = "<span>"
SOS = 189
SOS_ENCODED = 26239
EOD = 7
DEBUG = False
special_tokens = [SOS_ENCODED, EOD]


class Beam(object):
    def __init__(self, tokens, log_probs, context):
        self.tokens = tokens
        self.log_probs = log_probs
        self.context = context

    def extend(self, token, log_prob, context):
        return Beam(tokens=self.tokens + [token],
                    log_probs=self.log_probs + [log_prob],
                    context=context)

    def has_repeat_token(self, repeat_num):
        token_dic = {}
        for token in self.tokens:
            if token in token_dic.keys():
                token_dic[token] += 1
                if token_dic[token] > repeat_num:
                    return True
            else:
                token_dic[token] = 1
        return False

    def clear_special_tokens(self):
        for token in special_tokens:
            if token in self.tokens:
                self.tokens.remove(token)

    @property
    def latest_token(self):
        return self.tokens[-1]

    @property
    def avg_log_prob(self):
        if len(self.tokens) == 0:
            return 1e-6
        return sum(self.log_probs) / len(self.tokens)


def get_topk_tokens(logits: cupy.ndarray, k: int):
    logits -= logits.max()
    logits = cupy.exp(logits)
    logits /= logits.sum()
    cpu_probs = cupy.asnumpy(logits).astype(np.float32)
    # Default is in descending order (This bug confused me for a while)
    idx = cpu_probs.argsort()
    cpu_probs.sort()
    return idx[-k::-1], cpu_probs[-k::-1]


def sort_beams(beams):
    return sorted(beams, key=lambda h: h.avg_log_prob, reverse=True)


def finalize(chosen_beams, num_return_sequences):
    beams = sort_beams(chosen_beams)[:num_return_sequences]
    for beam in beams:
        beam.clear_special_tokens()
    return beams


def beam_search(model: bminf.models.CPM2,
                input_sentence: str,
                max_tokens: int = 128,
                num_beams: int = None,
                num_return_sequences: int = None,
                stop_tokens: Optional[List[str]] = None,
                ) -> List[str]:
    if stop_tokens is None:
        stop_tokens = []
    else:
        stop_tokens = [model.tokenizer.encode(i) for i in stop_tokens]

    # <eod> must be in the set of stop words.
    if not model.tokenizer.eod_id in stop_tokens:
        stop_tokens.append(model.tokenizer.eod_id)

    ctx, sampler, _ = model.pre_processing(
        input_sentence + SPAN_TOKEN,
        [len(input_sentence)],
        max_tokens, None, None, 0.9,
        0, 0, 189
    )
    # This decode_step will initialize the context
    logits = model.decode_step(ctx, [model.tokenizer.sod_id])[0]  # shape of logits is (vocab_size,)
    decoder_ipts = [model.tokenizer.get_span(SOS)]
    beams = [Beam(tokens=decoder_ipts,
                  log_probs=[0.0],
                  context=copy.deepcopy(ctx))
             for i in range(num_beams)]
    chosen_beams = []
    # Decode by beam search
    for steps in range(max_tokens):
        if DEBUG:
            print("*" * 16)
            print("Step {}".format(steps))
            print(beams[0].context.step_pos)
        num_orig_beams = 1 if steps == 0 else num_beams
        new_beams = []
        all_beams = []
        for i in range(num_orig_beams):
            h = beams[i]
            logits_i = model.decode_step(h.context, h.tokens[-1:])[0]
            context_i = copy.deepcopy(h.context)
            # topk
            topk_ids, topk_log_probs = get_topk_tokens(logits_i, num_beams * 2)
            if DEBUG:
                print("{} beam last token is {}".format(i, h.tokens[-1]))
                print(topk_ids)
                print(topk_log_probs)
            for j in range(num_beams * 2):  # for each of the top 2*beam_size hyps:
                new_beam = h.extend(token=topk_ids[j].item(),
                                    log_prob=topk_log_probs[j].item(),
                                    context=context_i)
                all_beams.append(new_beam)

        # prune new beams to number b, and pop results when reaching <eod>
        for h in sort_beams(all_beams):
            if h.latest_token == model.tokenizer.eod_id:
                if len(chosen_beams) < num_beams:
                    # Maybe we should add min_length restriction?
                    chosen_beams.append(h)
            else:
                new_beams.append(h)
            if len(new_beams) == num_beams:
                break
        beams = new_beams
        # results = [model.id_to_text(beam.tokens) for beam in beams]
    # Finish decoding, convert ids to string
    if len(chosen_beams) == 0:
        chosen_beams = beams[:num_beams]
    final_beams = finalize(chosen_beams, num_return_sequences)
    results = [model.id_to_text(beam.tokens) for beam in final_beams]
    return results

import bminf
from typing import Optional, Tuple, Union, List

SPAN_TOKEN = "<span>"


class Beam(object):
    def __init__(self, tokens, log_probs, state, context, coverage):
        self.tokens = tokens
        self.log_probs = log_probs
        self.state = state
        self.context = context
        self.coverage = coverage

    def extend(self, token, log_prob, state, context, coverage):
        return Beam(tokens=self.tokens + [token],
                    log_probs=self.log_probs + [log_prob],
                    state=state,
                    context=context,
                    coverage=coverage)

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

    @property
    def latest_token(self):
        return self.tokens[-1]

    @property
    def avg_log_prob(self):
        if (len(self.tokens) == 0):
            return 1e-6
        return sum(self.log_probs) / len(self.tokens)


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

    logits = model.decode_step(ctx, [model.tokenizer.sod_id])[0]
    decoder_ipts = [model.tokenizer.get_span(189)]
    blanks = []

    stoped = False

    for _ in range(max_tokens):
        # shape of logits  is (vocab_size,)
        print("*" * 16)
        print(decoder_ipts)
        print(ctx.step_pos)
        logits = model.decode_step(ctx, decoder_ipts[-1:])[0]
        # decoder_ipts is an index of a word in the vocab
        next_token = sampler.sample(logits)
        if next_token in stop_tokens:
            stoped = True
            break
        # prune new beams to number b, and pop results when reaching <end>
        blanks.append(next_token)
        decoder_ipts.append(next_token)
        print(model.id_to_text(blanks))

    return [model.id_to_text(blanks)]

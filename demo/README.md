[TOC]

# Quick start

To use cpm1 by huggingface:

```
python -m demo.try_cpm -s sample
```

To use cpm2 :

In gpt2 style:

```
python -m demo.generate_cpm2 --task generate --max_tokens 16 --temperature 0.85 --top_n 5 --top_p 1.0 
```

In Bert style:

```
python -m demo.generate_cpm2 --task fill --temperature 0.5 --top_n 5 --top_p 0.95 
```



# Some bugs to solve

## cpm1 by huggingface

### gpu

For cpm_gpu.py, we have to parallelize and use multi-gpu, but we get this:

```
Traceback (most recent call last):
  File "/home/tsq/ybb/demo/cpm_gpt2.py", line 21, in <module>
    outputs = model.generate(input_ids=input_ids.to(DEVICE), max_length=20, do_sample=True, bad_words_ids=None)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/torch/autograd/grad_mode.py", line 27, in decorate_context
    return func(*args, **kwargs)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/transformers/generation_utils.py", line 1007, in generate
    **model_kwargs,
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/transformers/generation_utils.py", line 1516, in sample
    output_hidden_states=output_hidden_states,
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/torch/nn/modules/module.py", line 889, in _call_impl
    result = self.forward(*input, **kwargs)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/transformers/models/gpt2/modeling_gpt2.py", line 954, in forward
    return_dict=return_dict,
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/torch/nn/modules/module.py", line 889, in _call_impl
    result = self.forward(*input, **kwargs)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/transformers/models/gpt2/modeling_gpt2.py", line 797, in forward
    output_attentions=output_attentions,
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/torch/nn/modules/module.py", line 889, in _call_impl
    result = self.forward(*input, **kwargs)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/transformers/models/gpt2/modeling_gpt2.py", line 323, in forward
    output_attentions=output_attentions,
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/torch/nn/modules/module.py", line 889, in _call_impl
    result = self.forward(*input, **kwargs)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/transformers/models/gpt2/modeling_gpt2.py", line 242, in forward
    query, key, value = self.c_attn(hidden_states).split(self.split_size, dim=2)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/torch/nn/modules/module.py", line 889, in _call_impl
    result = self.forward(*input, **kwargs)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/transformers/modeling_utils.py", line 1400, in forward
    x = torch.addmm(self.bias, x.view(-1, x.size(-1)), self.weight)
RuntimeError: Expected tensor for 'out' to have the same device as tensor for argument #2 'mat1'; but device 4 does not equal 3 (while checking arguments for addmm)

```

### length parameter

For the generation pipeline of huggingface, we want to use the 'max_length' and 'min_length' to restrict the generated text, but we get:

```
Traceback (most recent call last):
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/runpy.py", line 193, in _run_module_as_main
    "__main__", mod_spec)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/runpy.py", line 85, in _run_code
    exec(code, run_globals)
  File "/home/tsq/ybb/demo/try_cpm.py", line 34, in <module>
    work(decode_args)
  File "/home/tsq/ybb/demo/try_cpm.py", line 11, in work
    res = text_generator(TEXT, **vars(decode_args))
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/transformers/pipelines/text_generation.py", line 148, in __call__
    output_sequences = self.model.generate(input_ids=input_ids, **generate_kwargs)  # BS x SL
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/torch/autograd/grad_mode.py", line 27, in decorate_context
    return func(*args, **kwargs)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/transformers/generation_utils.py", line 979, in generate
    **model_kwargs,
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/transformers/generation_utils.py", line 1305, in greedy_search
    next_tokens_scores = logits_processor(input_ids, next_token_logits)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/transformers/generation_logits_process.py", line 93, in __call__
    scores = processor(input_ids, scores)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/transformers/generation_logits_process.py", line 121, in __call__
    scores[:, self.eos_token_id] = -float("inf")
IndexError: index 50256 is out of bounds for dimension 1 with size 30000

```

## cpm2

### bminf reproduction

I use the [bminf](https://github.com/OpenBMB/BMInf/blob/master/README-ZH.md) package to load CPM2.

Now, we can get some reasonable outputs like 北京大学也称为“北大”

But I don't why this can not be reproduced even if I use the same parameters.

I will check the API of bminf in the weekends !
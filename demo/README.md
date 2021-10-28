[TOC]

# Quick start

To use cpm1 by huggingface:

```
python -m demo.try_cpm -s sample
```

To use cpm2 **(still have bugs yet)**:

```
python -m demo.generate_cpm2 -task generate
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

### bminf

I use the [bminf](https://github.com/OpenBMB/BMInf/blob/master/README-ZH.md) package to load CPM2.

But I get an error about cublas:

```
Loading model
Input:  北京环球度假区相关负责人介绍，北京环球影城指定单日门票将采用____制度，即推出淡季日、平季日、旺季日和特定日门票。____价格为418元，____价格为528元，____价格为638元，____价格为____元。北京环球度假区将提供90天滚动价格日历，以方便游客提前规划行程。
Traceback (most recent call last):
  File "/home/tsq/ybb/demo/generate_cpm2.py", line 54, in <module>
    main()
  File "/home/tsq/ybb/demo/generate_cpm2.py", line 50, in main
    fill_blank(cpm2_1, input_1)
  File "/home/tsq/ybb/demo/generate_cpm2.py", line 18, in fill_blank
    presence_penalty=0
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/bminf/models/cpm2.py", line 151, in fill_blank
    frequency_penalty, presence_penalty, 0)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/bminf/models/cpm2.py", line 103, in pre_processing
    ctx = self.encode(np.array([idx], dtype=np.int64), [input_length])
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/bminf/arch/t5/model.py", line 238, in encode
    True
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/bminf/layers/transformer_block.py", line 42, in forward
    x = self.self_attention.forward(allocator, x, attention_mask, self_attn_position_bias)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/bminf/layers/attention.py", line 63, in forward
    qkv_i32
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/bminf/functions/gemm.py", line 86, in igemm
    _igemm(allocator, a, aT, b, bT, c, device, stream)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/bminf/functions/gemm.py", line 102, in _igemm
    lthandle = get_handle(device)
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/bminf/functions/gemm.py", line 66, in get_handle
    cublasLt.checkCublasStatus(cublasLt.cublasLtCreate( v ))
  File "/home/tsq/miniconda3/envs/ybb/lib/python3.7/site-packages/bminf/backend/cublaslt.py", line 101, in checkCublasStatus
    raise RuntimeError("cublas error: %s" % cublas_errors[cublas_status])
RuntimeError: cublas error: CUBLAS_STATUS_NOT_INITIALIZED
```

I debug the process and find that the function `get_handle(device)` defines a global variable `cublasLt_handles` but it is empty when our process reaches this function. That's why it will throw `CUBLAS_STATUS_NOT_INITIALIZED` error.

I searched the google and some people said that it may be the problem of OOM, so I will change a larger gpu device (like RTX 3090 on server 32) and try it again.
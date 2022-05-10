#!/bin/bash
#CHECKPOINT_PATH=/root/data/checkpoints
#CHECKPOINT_PATH=/data/wyq/workspace/GLM/checkpoints
CHECKPOINT_PATH=/data/tsq/glm
export CUDA_VISIBLE_DEVICES=0
source $1
#BertWordPieceTokenizer
MPSIZE=1
MAXSEQLEN=512

#SAMPLING ARGS
TEMP=0.9
#If TOPK/TOPP are 0 it defaults to greedy sampling, top-k will also override top-p
TOPK=40
TOPP=0


python -m torch.distributed.launch generate_samples.py \
       --DDP-impl none \
       --model-parallel-size $MPSIZE \
       $MODEL_ARGS \
       --fp16 \
       --cache-dir cache \
       --out-seq-length $MAXSEQLEN \
       --seq-length 512 \
       --temperature $TEMP \
       --top_k $TOPK \
       --top_p $TOPP

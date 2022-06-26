PROCESS_SIZE=16
CTX_SIZE=1000
SRC_TXT="sample_entity_fill_1000tokens"
DATA_DIR="/data/tsq/DuEL/filtered/coref/ctx1000/bd"

python -m src.data.DuEL.filter --task 'sample' \
                               --search_passage_with 'entity' \
                               --duel_dir /data/tsq/DuEL/filtered \
                               --output_dir /data/tsq/DuEL/filtered \
                               --context_window ${CTX_SIZE} \
                               --missing_tokens_policy fill

python -m src.data.DuEL.adapter --context_window ${CTX_SIZE} --src_text ${SRC_TXT} --task parse

python -m demo.coref.resolution --src_text ${SRC_TXT} \
                                --function 'stanford' \
                                --data_dir ${DATA_DIR} \
                                --max_len 256 \
                                --task 'coref' \
                                --processes ${PROCESS_SIZE}

python -m demo.coref.parse_stanford -src_text ${SRC_TXT} \
                                --function 'stanford' \
                                --data_dir ${DATA_DIR} \
                                --max_len 256 \
                                --task 'parse_all' \
                                --processes ${PROCESS_SIZE}

python -m src.data.DuEL.adapter --context_window ${CTX_SIZE} --src_text ${SRC_TXT} --task evaluate
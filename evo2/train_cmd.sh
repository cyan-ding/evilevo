MAX_STEPS=100
VAL_CHECK_INTERVAL=50
WARMUP_STEPS=100

train_evo2 \
    -d train_data_config.yml \
    --dataset-dir ./preprocessed \
    --result-dir pretraining_demo \
    --experiment-name evo2 \
    --model-size 1b \
    --devices 1 \
    --num-nodes 1 \
    --seq-length 8192 \
    --micro-batch-size 2 \
    --lr 0.000015 \
    --min-lr 0.0000149 \
    --warmup-steps ${WARMUP_STEPS} \
    --grad-acc-batches 4 \
    --max-steps ${MAX_STEPS} \
    --ckpt-dir nemo2_evo2_1b_8k \
    --clip-grad 250 \
    --wd 0.001 \
    --attention-dropout 0.01 \
    --hidden-dropout 0.01 \
    --val-check-interval ${VAL_CHECK_INTERVAL} \
    --activation-checkpoint-recompute-num-layers 5 \
    --create-tensorboard-logger \
    --ckpt-async-save
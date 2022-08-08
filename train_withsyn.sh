CUDA_VISIBLE_DEVICES=1 nohup python train.py --config config/syn_chinese_rbt_large.yaml \
                                        --data_directory ccl2022 \
                                        --save_checkpoints \
                                        --workers 1 > train_mytokenize_wisyn_before_addfw.log 2>&1 &
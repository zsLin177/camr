CUDA_VISIBLE_DEVICES=1 nohup python train.py --config config/chinese_rbt_large.yaml \
                                        --data_directory ccl2022 \
                                        --save_checkpoints \
                                        --workers 1 > train_ccl_wowandb.log 2>&1 &
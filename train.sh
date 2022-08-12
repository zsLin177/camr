CUDA_VISIBLE_DEVICES=0 nohup python train.py --config config/chinese_rbt_large.yaml \
                                        --data_directory ccl2022 \
                                        --save_checkpoints \
                                        --workers 1 > train_catdev_wofw_wosyn.log 2>&1 &
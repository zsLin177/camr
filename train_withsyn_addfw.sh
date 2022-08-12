CUDA_VISIBLE_DEVICES=0 nohup python train.py --config config/addfw_syn_chinese_rbt_large.yaml \
                                        --data_directory ccl2022 \
                                        --save_checkpoints \
                                        --workers 1 > train_catdev_lstm_syn_addfw.log 2>&1 &
                                        (34452)
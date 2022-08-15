CUDA_VISIBLE_DEVICES=0 nohup python train.py --config config/addfw_syn_chinese_rbt_large.yaml \
                                        --data_directory ccl2022 \
                                        --save_checkpoints \
                                        --workers 1 > train_catdev_lstm_syn_addfw.log 2>&1 &
                                        (34452)

CUDA_VISIBLE_DEVICES=0 nohup python train.py --config config/addfw_syn_chinese_rbt_large.yaml \
                                        --data_directory ccl2022 \
                                        --save_checkpoints \
                                        --workers 1 > train_catdev_lstm_syn_addfw_seed121.log 2>&1 &
                                        (124388)
                                    

CUDA_VISIBLE_DEVICES=0 nohup python train.py --config config/addfw_syn_chinese_rbt_large.yaml \
                                        --data_directory ccl2022 \
                                        --save_checkpoints \
                                        --workers 1 > train_catdev_lstm_syn_addfw_seed121_lr1.5e4.log 2>&1 &
                                        (174661)

CUDA_VISIBLE_DEVICES=0 nohup python train.py --config config/ens_addfw_syn_chinese_rbt_large.yaml \
                                        --data_directory ccl2022 \
                                        --save_checkpoints \
                                        --workers 1 > ens_train_catdev_lstm_syn_addfw_s123_lr1.5.log 2>&1 &
                                        (62668)
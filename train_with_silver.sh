CUDA_VISIBLE_DEVICES=0 python train.py --config config/with_silver.yaml \
                                        --data_directory ccl2022 \
                                        --save_checkpoints \
                                        --workers 1
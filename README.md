# SUDA-HUAWEI at CAMR2022
This repository contains the system we submitted at [CAMR2022](https://github.com/GoThereGit/Chinese-AMR). Our model is built based on [PERIN](https://github.com/ufal/perin).
Report is supported [here](CAMR_SUDA_HUAWEI.pdf).

## Install
The installation is mostly the same as Perin, except the mtool.
We modified the label normalization to fit chinese amr.
The modified mtool is [here](https://github.com/zsLin177/my_mtool).

## Train
```shell
CUDA_VISIBLE_DEVICES=3 python train.py --config config/addfw_chinese_rbt_large.yaml \
                                        --data_directory ccl2022 \
                                        --save_checkpoints \
                                        --workers 1

```

## Inference
```shell
CUDA_VISIBLE_DEVICES=5 python inference.py --checkpoint outputs/08-25-22_17-21-05/best_checkpoint.h5  --data_directory ccl2022
```

## Multi-graph Ensembling
```shell
python graph_ensemble_aug.py --dir wisyn_testb_graph_ens \
                             --len_file max_len_testB.txt \
                             --outname testb.tup
```
* "--dir" means the directory containg all predictions (in mrp format) of different model
* "--len_file" is [here](https://github.com/GoThereGit/Chinese-AMR/blob/main/data/test/test_B/max_len_testB.txt).

## Evaluation
We use AlignSmatch as the metric.
We use the [script](https://github.com/GoThereGit/Chinese-AMR/tree/main/tools) from camr2022.

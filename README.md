# SUDA-HUAWEI at CAMRP2022
This repository contains the system we submitted at [CAMRP2022](https://github.com/GoThereGit/Chinese-AMR). Our model is built based on [PERIN](https://github.com/ufal/perin).
Report is supported [here](CAMR_SUDA_HUAWEI.pdf).

## Data Preprocess
* From raw file to mrp file.
```shell
# first use preprocess/filte_duplicate.py to filte duplicate notes
python filte_duplicate.py --raw_file camr_dev.txt --out new_camr_dev.txt

# next use mtool to create file in .mrp
cd mtool
./main.py --read camr --write mrp new_camr_dev.txt camr_dev_fdomain.mrp

# here may happen some errors, for example:
# failed to parse #export_amr.1272 ‘(x56 / causation :arg1 (x58 / and :op1 (x1 / 有-03 :arg1 (x4 / 落款-01 :arg0 (x101 / government-organization :name (x2_x3 / name :op1 __0__ :op2 __1__ )))) :op2 (x7 / 有-03 :arg1 (x17 / 要求-04 :arg1 (x16 / 数量) :arg0-of (x68 / mean :arg1 (x12 / 刷-01 :arg0 (x69 / and :op1 (x9 / 乡镇 :mod (x8 / 各)) :op2 (x11 / 部门 :mod (x10 / 各))) :arg1 (x14 / 票 :quant (x13 / 多少)))))) :op3 (x24 / 发布-01 :location (x104 / publication :name (x22_x23_1 / name :op1 __2__ :op2 x23_1/网 )))) :arg2 (x82 / and :op1 (x31 / 能-01 :mod (x30 / 还) :arg0 (x32 / 说-01 :arg1 (x42 / 行为 :poss (x38 / 好心人 :quant (x36 / 个别)) :domain (x33 / 这) :mod (x34 / 只) :arg0-of (x41 / 个人-01))) :mode (x43_x44 / interrogative)) :op2 (x46 / 能-01 :mod (x45 / 还) :arg0 (x47 / 说-01 :arg1 (x51_2 / 有-01 :polarity (x51_1 / -) :arg1 (x52 / 责任) :arg0 (x48 / 你 :arg0-of (x97 / mean :arg1 (x49_x50 / x101))))) :mode (x53_x54 / interrogative))))’; exit.

# This is caused by some "op", for example "op2 x23_1/网", we change these ops to "op2 x23/网"

# next add functional word to edge label
python preprocess/add_fw.py --tup_train ccl2022/camr_official/camr_tuples/tuples_train.txt \
                            --raw_train ccl2022/camr_official/camr/camr_train.txt \
                            --tgt_tup_file ccl2022/camr_official/camr_tuples/tuples_dev.txt \
                            --tgt_raw_file ccl2022/camr_official/camr/camr_dev.txt \
                            --tgt_mrp_file ccl2022/tmp_camr_dev_fdomain.mrp \
                            --out ccl2022/addfw_camr_dev_fdomain.mrp

# add pos and syn
python preprocess/add_pos-syn.py --mrp ccl2022/addfw_camr_dev_fdomain.mrp \
                                 --conllu ccl2022/camr_official/camr_dev.txt.out.conllu \
                                 --out ccl2022/mytokenize_camr_dev_fdomain.mrp

```

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

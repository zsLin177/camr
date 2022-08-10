
import argparse
import os
import torch

import collections


def average_params(dir_path):
    ens_model_name = 'ens.model'
    if ens_model_name in os.listdir(dir_path):
        print('ens model exists')
        return

    model_path_lst = [os.path.join(dir_path, filename) for filename in os.listdir(dir_path)]
    print('ensembling:', model_path_lst)

    fed_state_dict = collections.OrderedDict()

    all_dic = torch.load(model_path_lst[0])

    checkpoint_state_dict = all_dic["model"]
    weight_keys = list(checkpoint_state_dict.keys())
    for key in weight_keys:
        fed_state_dict[key] = checkpoint_state_dict[key]

    for model_path in model_path_lst[1:]:
        checkpoint_state_dict = torch.load(model_path)["model"]
        for key in weight_keys:
            fed_state_dict[key] += checkpoint_state_dict[key]
    
    for key in weight_keys:
        fed_state_dict[key] = fed_state_dict[key] / len(model_path_lst)
    
    all_dic['model'] = fed_state_dict
    all_dic.pop('epoch')
    all_dic.pop('performance')

    torch.save(all_dic, os.path.join(dir_path, ens_model_name))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("--checkpoint", type=str, required=True, help='one best_checkpoint.h5_new')
    # parser.add_argument("--data_directory", type=str, default="/home/samueld/mrp_update/mrp")
    parser.add_argument("--dir", type=str, default="outputs/all_best_new", help='The directory which contain all best_checkpoint.h5_new.')
    args = parser.parse_args()

    # checkpoint = torch.load(args.checkpoint)
    # args = Params().load_state_dict(checkpoint["args"]).init_data_paths(args.data_directory)
    # args.log_wandb = False
    # args.encoder = '/data4/slzhou/PLMs/chinese-roberta-wwm-ext-large'

    # device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    # dataset = SharedDataset(args)
    # dataset.load_state_dict(args, checkpoint['dataset'])
    # dataset.load_datasets(args, 0, 1, build_vocab=False)


    average_params(args.dir)

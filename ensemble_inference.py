
import argparse
import torch
import os
import pickle

from model.model import Model
from data.shared_dataset import SharedDataset
from utility.initialize import initialize
from config.params import Params
from utility.ensemble_predict import ensemble_predict

def check_field(d1_vocab, d2_vocab):
    """
    dataset1 and dataset2 are the output of dataset.get_vocabs_for_compare()
    """
    # d1_vocab, d2_vocab = dataset1.get_vocabs_for_compare(), dataset2.get_vocabs_for_compare()
    s = ''
    diff_property_vocabs = False
    if d1_vocab['property vocabs'] != d2_vocab['property vocabs']:
        diff_property_vocabs = True
        s += 'different property vocabs; '
    
    diff_property_keys = False
    if d1_vocab['property keys'] != d2_vocab['property keys']:
        diff_property_keys = True
        s += 'different property keys; '

    other_dic_diff_lst = {key: False for key in d1_vocab['vocabs'].keys()}
    for key in other_dic_diff_lst.keys():
        v_1, v_2 = d1_vocab['vocabs'][key], d2_vocab['vocabs'][key]
        if v_1 != v_2:
            other_dic_diff_lst[key] = True
            s += f'different {key} vocab; '
    
    print(s)
    if any([diff_property_vocabs, diff_property_keys] + list(other_dic_diff_lst.values())):
        # has something different
        return False
    else:
        return True

def load_saved_dataset(dict):
    res = {}
    p_r_dic = dict[('amr', 'zho')]
    property_keys = p_r_dic["property keys"]
    property_field_vocabs = pickle.loads(p_r_dic["property vocabs"])
    vocabs = {}
    for key, value in p_r_dic["vocabs"].items():
        vocabs[key] = pickle.loads(value)

    res['property vocabs'] = property_field_vocabs
    res['property keys'] = property_keys
    res['vocabs'] = vocabs
    return res


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, required=True, help='The dirctory which containg all models need to be ensembled.')
    parser.add_argument("--data_directory", type=str, default="/home/samueld/mrp_update/mrp")
    args = parser.parse_args()

    model_path_lst = [os.path.join(args.dir, filename) for filename in os.listdir(args.dir)]
    model_lst = []
    if len(model_path_lst) == 0:
        raise ValueError('no model in this dir')

    checkpoint = torch.load(model_path_lst[0])
    args = Params().load_state_dict(checkpoint["args"]).init_data_paths(args.data_directory)
    args.log_wandb = False
    args.encoder = '/opt/data/private/slzhou/PLMs/chinese-roberta-wwm-ext-large'

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    directory = initialize(args, create_directory=True, init_wandb=False, directory_prefix="inference_")

    dataset = SharedDataset(args)
    dataset.load_state_dict(args, checkpoint['dataset'])
    dataset.load_datasets(args, 0, 1, build_vocab=False)

    print(f'loading model in {model_path_lst[0]}')
    model = Model(dataset, args)
    model.load_state_dict(checkpoint["model"])
    model = model.to(device)
    model_lst.append(model)

    child_dataset_1_vocab = dataset.child_datasets[('amr', 'zho')].get_vocabs_for_compare()

    for p in model_path_lst[1:]:
        print(f'loading model in {p}')
        model = Model(dataset, args)
        tmp_ckp = torch.load(p)

        c_child_dataset_vocab = load_saved_dataset(tmp_ckp['dataset'])
        if check_field(child_dataset_1_vocab, c_child_dataset_vocab):
            print(f'{p} has the same vocab with {model_path_lst[0]}')
        else:
            print(f'{p} has the different vocab with {model_path_lst[0]}')
            exit()
            # raise ValueError(f'{p} has the different vocab with {model_path_lst[0]}')

        model.load_state_dict(tmp_ckp['model'])
        model = model.to(device)
        model_lst.append(model)

    print("inference of validation data", flush=True)
    ensemble_predict(model_lst, dataset.val, args.validation_data, args, directory, 0, run_evaluation=True, epoch=0)

    print("inference of test data", flush=True)
    ensemble_predict(model_lst, dataset.test, args.test_data, args, f"{directory}/test_predictions", 0)
    

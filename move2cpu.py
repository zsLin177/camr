import argparse
import torch
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--out_dir", type=str, default="outputs/all_best_new")
    args = parser.parse_args()

    if not os.path.exists(args.out_dir):
        os.mkdir(args.out_dir)

    checkpoint = torch.load(args.input)

    for key in checkpoint['model'].keys():
        checkpoint['model'][key] = checkpoint['model'][key].cpu()

    new_chkp = {'epoch': checkpoint['epoch'], 
                'dataset': checkpoint['dataset'],
                'performance': checkpoint['performance'],
                'model': checkpoint['model'],
                'args':checkpoint['args']}
    
    all_f1 = new_chkp['performance']['evaluation all f1']
    all_f1_s = f'f1_{all_f1:.4f}'

    torch.save(new_chkp, os.path.join(args.out_dir, all_f1_s+'.model'))


    
import json
import argparse

def read_syn_pos(input_file):
    res = {}
    with open(input_file, 'r') as f:
        line_lsts = [line for line in f]

    sentence_lsts = []
    start, i = 0, 0
    for line in line_lsts:
        if line == '\n':
            sentence_lsts.append(line_lsts[start:i])
            start = i + 1
        i += 1

    for sentence_lst in sentence_lsts:
        this_res = {}
        export_amr_id = sentence_lst[0].strip().split('#')[1]
        pos1_lst = []
        pos2_lst = []
        syn_lst = []
        for sent_line in sentence_lst[1:]:
            sent_line_lst = sent_line.strip().split('\t')
            pos1_lst.append(sent_line_lst[3])
            pos2_lst.append(sent_line_lst[4])
            syn_lst.append(sent_line_lst[7])
        if pos1_lst != pos2_lst:
            print(f'{export_amr_id} pos1 != pos2 !')
        this_res['pos1'] = pos1_lst
        this_res['pos2'] = pos2_lst
        this_res['syn'] = syn_lst
        res[export_amr_id] = this_res

    return res


def write(mrp_file, syn_res, new_file):
    with open(mrp_file, 'r', encoding='utf8') as f:
        all_res = []
        for line in f.readlines():
            all_res.append(json.loads(line))
    
    for dic in all_res:
        snt_id = dic['id']
        dic['pos'] = syn_res[snt_id]['pos1']
        dic['syn'] = syn_res[snt_id]['syn']
    
    with open(new_file, 'w',  encoding='utf8') as f:
        for dic in all_res:
            f.write(json.dumps(dic, ensure_ascii=False)+'\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mrp', type=str)
    parser.add_argument('--conllu', type=str)
    parser.add_argument('--out', type=str)

    args = parser.parse_args()

    syn_res = read_syn_pos(args.conllu)
    write(args.mrp, syn_res, args.out)
    
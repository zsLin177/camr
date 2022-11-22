# add the onformation of functional word by using the combination label

import argparse
import json
from collections import Counter



def read_mrp(file_name):
    with open(file_name, 'r', encoding='utf8') as f:
        lines = f.readlines()
        all_sent_res = []
        for line in lines:
            all_sent_res.append(json.loads(line))
    return all_sent_res

def add_fw(mrp_res, fw_info, count_large1_lst):
    assert len(mrp_res) == len(fw_info)
    for mrp_dic in mrp_res:
        id = mrp_dic['id'].split('.')[1]
        sent_fw_info = fw_info[id]
        if len(sent_fw_info) == 0:
            continue
        
        nodeid2label = {}
        for node in mrp_dic['nodes']:
            id = node['id']
            label = node['label']
            nodeid2label[id] = label
        
        tup2fw = {}
        for info in sent_fw_info:
            new_label = info['rel'] + '+' + info['fw']
            if new_label in count_large1_lst:
                # del those rare labels
                tup = (info['source'], info['target'], info['rel'])
                tup2fw[tup] = info['fw']
        
        for edge_item in mrp_dic['edges']:
            mrp_tup = (nodeid2label[edge_item['source']], nodeid2label[edge_item['target']], edge_item['label'])
            if mrp_tup in tup2fw:
                fw = tup2fw[mrp_tup]
                edge_item['label'] = edge_item['label'] + '+' + fw
                if 'normal' in edge_item:
                    edge_item['normal'] = edge_item['normal'] + '+' + fw

    return mrp_res

def write_new_mrp(mrp_res, file_name):
    with open(file_name, 'w', encoding='utf8') as f:
        for mrp_dic in mrp_res:
            f.write(json.dumps(mrp_dic, ensure_ascii=False)+'\n')


def read_tup(file_name, raw_camr_file):
    with open(raw_camr_file, 'r') as f:
        line_lsts = [line for line in f]
        sentence_lsts = []
        start, i = 0, 0
        for line in line_lsts:
            if line == '\n':
                sentence_lsts.append(line_lsts[start:i])
                start = i + 1
            i += 1
        
        token_dic = {}
        for sentence_lst in sentence_lsts:
            sent_id = sentence_lst[0].strip().split()[2].split('.')[1]
            tokens = sentence_lst[1].strip()[8:].split()
            token_dic[sent_id] = tokens


    with open(file_name, 'r', encoding='utf8') as f:
        for i in range(3):
            f.readline()
        line_lsts = [line for line in f]
        sentence_lsts = []
        start, i = 0, 0
        for line in line_lsts:
            if line == '\n':
                sentence_lsts.append(line_lsts[start:i])
                start = i + 1
            i += 1
        
        res = {}
        sum_num = 0
        one_word_fw = 0
        all_relfw_lst = []
        for sent_lines_lst in sentence_lsts:
            sent_res = []
            sent_id = sent_lines_lst[0].strip().split('\t')[0]
            for line in sent_lines_lst:
                lst = line.strip().split('\t')
                rel_align, fw = lst[5], lst[6]
                if rel_align != '-':
                    tmp_lst = rel_align.split('_')
                    if len(tmp_lst) == 1:
                        one_word_fw += 1
                    # try:
                    #     rel_align_lst = [int(al_s[1:])-1 for al_s in rel_align.split('_')]
                    # except:
                    #     import pdb
                    #     pdb.set_trace()
                    # full_s = ''.join([token_dic[sent_id][al_id] for al_id in rel_align_lst])
                    # if full_s != fw:
                    #     import pdb
                    #     pdb.set_trace()
                if lst[6] != '-':
                    all_relfw_lst.append(lst[4].split(':')[1]+'+'+fw)
                    sent_res.append({'source': lst[2], 'target': lst[8], 'fw': fw, 'rel': lst[4].split(':')[1]})
            sum_num += len(sent_res)
            res[sent_id] = sent_res
        counter = Counter(all_relfw_lst)
        # print(counter.most_common())
        count_large_1 = []
        count_eq_1 = []
        count_large_2 = []
        for key, value in counter.items():
            if value > 2:
                count_large_2.append(key)
            if value > 1:
                count_large_1.append(key)
            else:
                count_eq_1.append(key)
        print('sum_edge_labels:', len(counter))
        print('count_large_2:', len(count_large_2))
        print('count_large_1:', len(count_large_1))
        print('count_eq_1:', len(count_eq_1))
        print('count_large_2/sum_edge_labels:', len(count_large_2)/len(counter))
        print('count_eq_1/sum_edge_labels:', len(count_eq_1)/len(counter))

    print('sum_num:', sum_num)
    print('one_word_fw:', one_word_fw)
    print('one_word_fw/sum_num:', one_word_fw/sum_num)
    return res, count_large_1

                


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tup_train", type=str, default='camr_official/camr_tuples/tuples_train.txt', help="path to the train tuple file")
    parser.add_argument("--raw_train", type=str, default='camr_official/camr/camr_train.txt', help="path to the raw train file")
    parser.add_argument("--tgt_tup_file", type=str, default='camr_official/camr_tuples/tuples_dev.txt')
    parser.add_argument("--tgt_raw_file", type=str, default='camr_official/camr/camr_dev.txt')
    parser.add_argument("--tgt_mrp_file", type=str, default='camr_dev_fdomain.mrp')
    parser.add_argument("--out", type=str, default='addfw_camr_dev_fdomain.mrp')
    args = parser.parse_args()

    train_tup_file = args.tup_train
    _, count_large_1 = read_tup(train_tup_file, args.raw_train)
    tup_file = args.tgt_tup_file
    fw_info, _ = read_tup(tup_file, args.tgt_raw_file)
    mrp_res = read_mrp(args.tgt_mrp_file)
    new_mrp_res = add_fw(mrp_res, fw_info, count_large_1)
    new_file_name = args.out
    write_new_mrp(new_mrp_res, new_file_name)



    # # do not change
    # train_tup_file = 'camr_official/camr_tuples/tuples_train.txt'
    # _, count_large_1 = read_tup(train_tup_file, 'camr_official/camr/camr_train.txt')

    # # can change
    # tup_file = 'camr_official/camr_tuples/tuples_dev.txt'
    # fw_info, _ = read_tup(tup_file, 'camr_official/camr/camr_dev.txt')
    # mrp_res = read_mrp('mytokenize_camr_dev_fdomain.mrp')
    # new_mrp_res = add_fw(mrp_res, fw_info, count_large_1)
    # new_file_name = 'addfw_mytokenize_camr_dev_fdomain.mrp'
    # write_new_mrp(new_mrp_res, new_file_name)

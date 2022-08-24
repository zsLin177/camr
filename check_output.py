# this is used to check the output num and order

import json
import argparse

def reorder_mrp(file_name, maxlen_file, new_file_name):
    ordered_sntid_lst = read_maxlen_file(maxlen_file)
    with open(file_name, 'r', encoding='utf8') as f:
        raw_res = {}
        for line in f.readlines():
            if len(line) > 1:
                dic = json.loads(line)
                raw_res[dic['id']] = dic
        
    new_res_lst = []
    for ss_id in ordered_sntid_lst:
        amr_id = 'export_amr.'+ss_id
        new_res_lst.append(raw_res[amr_id])
    
    with open(new_file_name, 'w', encoding='utf8') as f:
        for res in new_res_lst:
            f.write(json.dumps(res, ensure_ascii=False)+'\n')

def read_maxlen_file(file_name):
    ordered_sntid_lst = []
    with open(file_name, 'r') as f:
        for line in f.readlines():
            if len(line) > 1:
                ss_id = line.strip().split('\t')[0]
                ordered_sntid_lst.append(ss_id)
    return ordered_sntid_lst

def read_tup_file(file_name):
    with open(file_name, 'r') as f:
        for i in range(3):
            f.readline()
        line_lsts = [line.strip().split('\t') for line in f]
        
        sentence_tup_lsts = []
        start, i = 0, 0
        for line in line_lsts:
            if len(line) == 1:
                sentence_tup_lsts.append(line_lsts[start:i])
                start = i + 1
            i += 1

    output_order = []
    for sent_tup_lst in sentence_tup_lsts:
        output_order.append(sent_tup_lst[0][0])
        continue

    return output_order

def check_label(file_name):
    with open(file_name, 'r') as f:
        for i in range(3):
            f.readline()
        line_lsts = [line.strip().split('\t') for line in f]
        
        sentence_tup_lsts = []
        start, i = 0, 0
        for line in line_lsts:
            if len(line) == 1:
                sentence_tup_lsts.append(line_lsts[start:i])
                start = i + 1
            i += 1

        for sent_tup_lst in sentence_tup_lsts:
            for tup_lst in sent_tup_lst:
                if tup_lst[2].startswith('x') or tup_lst[8].startswith('x'):
                    print(tup_lst)
        

if __name__ == '__main__':
    # testa_mrp_file_name = 'mtool/data/sample/camr/camr_test_fdomain.mrp'
    # testa_max_len_file = 'ccl2022/ccl_test/Chinese-AMR-main/data/test/test_A/max_len_testA.txt'
    # new_tesea_mrp_file = 'ccl2022/pseudo_testa_fdomain.mrp'
    # reorder_mrp(testa_mrp_file_name, testa_max_len_file, new_tesea_mrp_file)

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, required=True, help="the output tup file")
    parser.add_argument("--len_file", type=str, required=True, help="the file of max_len")
    args = parser.parse_args()

    gold_order_sid = read_maxlen_file(args.len_file)
    pred_order_sid = read_tup_file(args.output)

    if gold_order_sid == pred_order_sid:
        print('Yes! They have same number of sentences and the order is right.')
    else:
        print('False! Have problems!!!')
    



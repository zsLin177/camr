import argparse
import json
import mtool.main
import mtool.score.mces

import mtool.score.core
from mtool.score.smatch import smatch, tuples
from collections import defaultdict

def read_graph_frommrp(filename):
    normalize = {"anchors", "case", "edges", "attributes"}
    with open(filename, encoding="utf8") as f:
        graphs, _ = mtool.main.read_graphs(f, format="mrp", frameworks=['amr'], normalize=normalize)
        for graph in graphs:
            graph._language = None
    return graphs

def read_tuples(graphs, prefix, values={"tops", "labels", "properties", "anchors", "edges", "attributes"}, faith=False):
    """
    ginstances:
        [('instance', 'g0', '复印-01'), ('instance', 'g1', '我们'), ('instance', 'g2', '最近'), ('instance', 'g3', '通过-01'), ('instance', 'g4', '人士'), ('instance', 'g5', '知情'), ('instance', 'g6', '凭证'), ('instance', 'g7', '11'), ('instance', 'g8', '发票'), ('instance', 'g9', '部分'), ('instance', 'g10', '原始-01'), ('instance', 'g11', '份'), ('instance', 'g12', 'mean'), ('instance', 'g13', '共计-01'), ('instance', 'g14', 'thing'), ('instance', 'g15', '余'), ('instance', 'g16', '30'), ('instance', 'g17', '份'), ('instance', 'g18', '部门'), ('instance', 'g19', '财务'), ('instance', 'g20', 'government-organization'), ('instance', 'g21', 'name'), ('instance', 'g22', 'city'), ('instance', 'g23', 'name')]
    gattributes:
        [('anchor', 'g0', 'frozenset({36, 37})'), ('TOP', 'g0', ''), ('anchor', 'g1', 'frozenset({5, 6})'), ('anchor', 'g2', 'frozenset({0, 1})'), ('anchor', 'g3', 'frozenset({8, 9})'), ('anchor', 'g4', 'frozenset({14, 15})'), ('anchor', 'g5', 'frozenset({11, 12})'), ('anchor', 'g6', 'frozenset({50, 51})'), ('anchor', 'g7', 'frozenset({53, 54})'), ('anchor', 'g8', 'frozenset({48, 47})'), ('anchor', 'g9', 'frozenset({41, 42})'), ('anchor', 'g10', 'frozenset({44, 45})'), ('anchor', 'g11', 'frozenset({56})'), ('anchor', 'g13', 'frozenset({60, 61})'), ('anchor', 'g15', 'frozenset({67})'), ('anchor', 'g16', 'frozenset({65, 66})'), ('anchor', 'g17', 'frozenset({69})'), ('anchor', 'g18', 'frozenset({33, 34})'), ('anchor', 'g19', 'frozenset({30, 31})'), ('anchor', 'g21', 'frozenset({23, 24, 26, 27, 28})'), ('op1', 'g21', '殡葬'), ('op2', 'g21', '管理处'), ('anchor', 'g23', 'frozenset({19, 20, 21})'), ('op1', 'g23', '衡阳市')]
    grelations:
        [('arg0', 'g0', 'g1'), ('op1', 'g15', 'g16'), ('arg1', 'g0', 'g6'), ('quant', 'g8', 'g9'), ('dcopy', 'g14', 'g6'), ('name', 'g22', 'g23'), ('arg1', 'g3', 'g4'), ('arg0', 'g10', 'g8'), ('time', 'g0', 'g2'), ('domain', 'g19', 'g18'), ('domain', 'g8', 'g6'), ('cunit', 'g6', 'g11'), ('arg0', 'g12', 'g6'), ('quant', 'g14', 'g15'), ('arg0', 'g13', 'g14'), ('location', 'g0', 'g18'), ('arg0', 'g5', 'g4'), ('arg1', 'g12', 'g13'), ('name', 'g20', 'g21'), ('manner', 'g0', 'g3'), ('quant', 'g6', 'g7'), ('part', 'g20', 'g18'), ('cunit', 'g14', 'g17'), ('location', 'g20', 'g22'), ('arg0', 'g3', 'g1')]
    """
    all_res = []
    graphs_clone = [] + graphs
    sent_ids = []
    for g, _ in mtool.score.core.intersect(graphs, graphs_clone):
        sent_ids.append(g.id.split('.')[1])
        ginstances, gattributes, grelations, gn = tuples(g, prefix, values, faith)
        node_dic, top_id = normalize_concept_align(ginstances, gattributes, g.input)
        rels = get_rels(node_dic, top_id, grelations, g.input.strip().split())
        all_res.append(rels)

    return all_res, sent_ids

def write_tuple_file(file_name, all_res, sent_ids):
    with open(file_name, 'w', encoding='utf-8') as f:
        line_0 = '\t'.join(['句子编号', '节点编号1', '概念1', '同指节点1', '关系', '关系编号', '关系对齐词', '节点编号2', '概念2', '同指节点2'])
        f.write(line_0+'\n')
        line_1 = '\t'.join(['sid', 'nid1', 'concept1', 'coref1', 'rel', 'rid','ralign', 'nid2', 'concept2', 'coref2'])
        f.write(line_1+'\n')
        f.write('\n')

        for sent_res, sent_id in zip(all_res, sent_ids):
            for rel_dic in sent_res:
                line_lst = [sent_id, rel_dic['head'][1], rel_dic['head'][0], '-', rel_dic['rel'], rel_dic['fw_align'], rel_dic['fw'], rel_dic['tail'][1], rel_dic['tail'][0], '-']
                f.write('\t'.join(line_lst)+'\n')
            f.write('\n')
        
def get_rels(node_dic, top_id, relations, tokens):
    res = []
    res.append({'head': ('root', 'x0'), 'tail': node_dic[top_id], 'rel': ':top', 'fw':'-', 'fw_align': '-'})
    for rel, head_id, tail_id in relations:
        if head_id not in node_dic or tail_id not in node_dic:
            continue
        
        if len(rel.split('+')) == 2:
            rel, fw = rel.split('+')
            if rel == 'fdomain':
                rel = ':mod'
                h, t = node_dic[tail_id], node_dic[head_id]
            else:
                rel = ':'+rel
                h, t = node_dic[head_id], node_dic[tail_id]
            h_align_str, t_align_str = h[1], t[1]
            fw_align_str = 'x' + str(match_fw(fw, tokens, h_align_str, t_align_str))
            res.append({'head': h, 'tail': t, 'rel': rel, 'fw':fw, 'fw_align': fw_align_str})
        elif rel == 'fdomain':
            rel = ':mod'
            res.append({'head': node_dic[tail_id], 'tail': node_dic[head_id], 'rel': rel, 'fw':'-', 'fw_align': '-'})
        else:
            rel = ':'+rel
            res.append({'head': node_dic[head_id], 'tail': node_dic[tail_id], 'rel': rel, 'fw':'-', 'fw_align': '-'})
    return res

def match_fw(fw, tokens, head_align_str, tail_align_str):
    """
    Find the alignment of the fw in tokens.
    Currently, search fw is seen as a whole
    """
    # start from 0
    h_a_idx = int(head_align_str.split('_')[0].split('x')[1]) - 1
    t_a_idx = int(tail_align_str.split('_')[0].split('x')[1]) - 1
    if h_a_idx < len(tokens):
        core_idx = h_a_idx
    elif t_a_idx < len(tokens):
        core_idx = t_a_idx
    else:
        core_idx = len(tokens) // 2
    
    matched_idx = find(fw, tokens, core_idx)
    if matched_idx != -1:
        # start from 1
        return matched_idx+1
    else:
        if core_idx == len(tokens)-1:
            return core_idx + 1 - 1
        else:
            return core_idx + 1 + 1
    
def find(fw, tokens, core_idx):
    if tokens[core_idx] == fw:
        return core_idx
    # find behind first
    if fw in tokens[core_idx+1:]:
        return tokens.index(fw, core_idx+1)
    if fw in tokens[0: core_idx]:
        reversed_lst = list(reversed(tokens[0: core_idx]))
        return len(reversed_lst) - 1 - reversed_lst.index(fw)
    # not finded
    return -1


def normalize_concept_align(instances, attributes, sent):
    """
    change ('instance', 'g0', '复印-01') ('anchor', 'g0', 'frozenset({36, 37})') to
    (g0, x13, 复印-01)
    """
    norm_con_label_dic = {}
    name_con_label_dic = {}
    norm_con_attr_dic = defaultdict(list)
    name_con_attr_dic = defaultdict(list)
    for _, id, label in instances:
        if label == 'name':
            name_con_label_dic[id] = 'name'
        else:
            norm_con_label_dic[id] = label
    
    top_id = None
    ignore_ids = []
    for attr_name, id, value in attributes:
        if attr_name == 'TOP':
            top_id = id
            continue
        if id in norm_con_label_dic:
            norm_con_attr_dic[id].append((attr_name, value))
        else:
            name_con_attr_dic[id].append((attr_name, value))
    
    tokens = sent.split()
    outer_align = len(tokens)+10
    char_level_seg = []
    start = 0
    for token in tokens:
        token_len = len(token)
        char_level_seg.append((start, start+token_len-1))
        start = start + token_len + 1

    node_dic = {}

    # process normal concept
    for id, label in norm_con_label_dic.items():
        attr_lst = norm_con_attr_dic[id]
        if len(attr_lst) == 0:
            align_token_id = outer_align
            outer_align += 1
            node_dic[id] = (label, 'x' + str(align_token_id))
            continue
        
        # flag = 0
        anchor_set = None
        for attr_name, value in attr_lst:
            if attr_name == 'anchor':
                anchor_set = eval(value)
            else:
                # raise ValueError(f'normal concept id: {id} label: {label} has {attr_name}: {value}')
                print(f'normal concept id: {id} label: {label} has {attr_name}: {value}')
        
        # if flag == 1 and id != top_id:
        #     print(f'normal concept id: {id} label: {label} has {attr_name}: {value} ignore!')
        #     continue

        if anchor_set is None or len(anchor_set) == 0:
            # this concept has no alignment
            align_token_id = outer_align
            outer_align += 1
            node_dic[id] = (label, 'x' + str(align_token_id))
        else:
            sorted_lst = sorted(anchor_set)
            v = combine(sorted_lst, char_level_seg, sent, tokens, label)
            node_dic[id] = (label, v)

    # process name concept
    for id, label in name_con_label_dic.items():
        attr_lst = name_con_attr_dic[id]
        if len(attr_lst) == 0:
            print(f'name concept id: {id} label: {label} has no attr, ignore!')
            ignore_ids.append(id)
            # align_token_id = outer_align
            # outer_align += 1
            # node_dic[id] = (label, 'x' + str(align_token_id))
            continue

        anchor_set = None
        op_lst = []
        for attr_name, value in attr_lst:
            if attr_name == 'anchor':
                anchor_set = eval(value)
            elif attr_name.startswith('op'):
                op_lst.append((attr_name, value))
            else:
                # raise ValueError(f'name concept id: {id} label: {label} has {attr_name}')
                print(f'name concept id: {id} label: {label} has {attr_name}: {value}')
                continue
        if len(op_lst) > 0:
            op_lst = sorted(op_lst, key=lambda x:x[0])
            new_label = ''.join([op_value for op_name, op_value in op_lst])
        else:
            if id != top_id:
                print(f'name concept id: {id} label: {label} has no op attr, ignore!')
                ignore_ids.append(id)
                continue
            else:
                new_label = 'name'

        if anchor_set is None or len(anchor_set) == 0:
            # this concept has no alignment
            align_token_id = outer_align
            outer_align += 1
            node_dic[id] = (new_label, 'x' + str(align_token_id))
        else:
            sorted_lst = sorted(anchor_set)
            v, new_label = combine(sorted_lst, char_level_seg, sent, tokens, new_label, if_name_node=True)
            node_dic[id] = (new_label, v)
    return node_dic, top_id

def combine(char_anchor_lst, word_spans, sent, tokens, label, if_name_node=False):
    res  = []
    word_ids = []
    for ca in char_anchor_lst:
        word_id = None
        for i, (st, ed) in enumerate(word_spans, 1):
            if ca >= st and ca <= ed:
                word_id = i
                break
        if word_id is None:
            raise ValueError('a error in combine')
        word_ids.append(word_id)
    
    word_level_res = []
    word_level_wordid = []
    st = 0
    curr = 0
    while curr < len(word_ids):
        st_word_id = word_ids[st]
        cu_word_id = word_ids[curr]
        if cu_word_id == st_word_id:
            curr += 1
        else:
            word_level_res.append(char_anchor_lst[st:curr])
            word_level_wordid.append(word_ids[st])
            st = curr
    word_level_res.append(char_anchor_lst[st:curr])
    word_level_wordid.append(word_ids[-1])

    s_lst = []
    if not if_name_node:
        for i, lst in enumerate(word_level_res):
            word_id = word_level_wordid[i]
            word = tokens[word_id-1]
            if label in word:
                if label == word:
                    s_lst.append('x'+str(word_id))
                else:
                    char_st = word.index(label) + 1
                    tmp_chr_lst = [str(char_st+ci) for ci in range(len(label))]
                    s_lst.append('x'+str(word_id)+'_'+'_'.join(tmp_chr_lst))
            else:
                if len(lst) == len(word):
                    s_lst.append('x'+str(word_id))
                else:
                    sub_s = '_'.join([str(char_id-word_spans[word_id-1][0]+1) for char_id in lst])
                    s_lst.append('x'+str(word_id)+'_'+sub_s)
        return '_'.join(s_lst)
    else:
        # name concept
        new_label_str = ''
        for i, lst in enumerate(word_level_res):
            word_id = word_level_wordid[i]
            word = tokens[word_id-1]

            for c_i in lst:
                new_label_str += sent[c_i]
            
            if len(lst) == len(word):
                s_lst.append('x'+str(word_id))
            else:
                sub_s = '_'.join([str(char_id-word_spans[word_id-1][0]+1) for char_id in lst])
                s_lst.append('x'+str(word_id)+'_'+sub_s)

        return '_'.join(s_lst), new_label_str


def check_sent_id(raw_camr_file, sent_id_from_mrp):
    with open(raw_camr_file, 'r') as f:
        line_lsts = [line for line in f]

    sentence_lsts = []
    start, i = 0, 0
    for line in line_lsts:
        if line == '\n':
            sentence_lsts.append(line_lsts[start:i])
            start = i + 1
        i += 1
    
    sent_ids = []
    for sentence_lst in sentence_lsts:
        sent_ids.append(sentence_lst[0].strip().split()[2].split('.')[1])
    
    return sent_ids == sent_id_from_mrp
    

def write_len_file(file_name, out_file):
    res = []
    with open(file_name, 'r') as f:
        lines = f.readlines()
        for line in lines:
            dic = json.loads(line)
            id = dic['id'].split('.')[1]
            length = len(dic['input'].split())
            res.append((id, str(length)))
    
    with open(out_file, 'w') as f:
        for t in res:
            f.write('\t'.join(t)+'\n')



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mrp", type=str, default=None, help="path to the input mrp file")
    parser.add_argument("--tup", type=str, default=None, help="path to the output tuple file")
    args = parser.parse_args()

    print('starting transform.')
    graphs = read_graph_frommrp(args.mrp)
    all_res, sent_ids = read_tuples(graphs, 'g')
    write_tuple_file(args.tup, all_res, sent_ids)
    print('transform finished.')





    # # file_name = '/opt/data/private/slzhou/slzhou@127/perin/ccl2022/camr_dev.mrp'
    # file_name = '/opt/data/private/slzhou/slzhou@127/perin/outputs/inference_08-01-22_02-20-49/prediction_amr_zho.json'
    # # file_name = '/opt/data/private/slzhou/slzhou@127/perin/ccl2022/camr_test_fdomain.mrp'

    # graphs = read_graph_frommrp(file_name)
    # all_res, sent_ids = read_tuples(graphs, 'g')
    # out_file = '/opt/data/private/slzhou/slzhou\@127/perin/Chinese-AMR/tools/camr_test.tup'
    # # out_file = '/opt/data/private/slzhou/slzhou@127/perin/ccl2022/from_gold_mrp_camr_dev.tup'
    # # out_file = '/opt/data/private/slzhou/slzhou@127/perin/Chinese-AMR/tools/from_gold_mrp_camr_fdomain_test.tup'

    # write_tuple_file(out_file, all_res, sent_ids)

    # # raw_camr_file = '/opt/data/private/slzhou/slzhou@127/perin/ccl2022/camr_official/camr/camr_dev.txt'
    # # print(check_sent_id(raw_camr_file, sent_ids))





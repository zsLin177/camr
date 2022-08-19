import argparse
import os
import math
import mtool.main
import mtool.score.mces

import mtool.score.core
from mtool.score.smatch import smatch, tuples
from collections import defaultdict
from mrp2tuple import normalize_concept_align, get_rels, n_write_tuple_file
from multiprocessing import Pool, Manager

manager = Manager()
all_sent_res_dic = manager.dict()

def read_graph_frommrp(filename):
    normalize = {"anchors", "case", "edges", "attributes"}
    res = {}
    with open(filename, encoding="utf8") as f:
        graphs, _ = mtool.main.read_graphs(f, format="mrp", frameworks=['amr'], normalize=normalize)
        for graph in graphs:
            graph._language = None
    for g in graphs:
        res[g.id] = g
    return res

def get_smatch(gold_graph_dict, pred_graph_dict):
    for key, g_g in gold_graph_dict.items():
        p_g = pred_graph_dict[key]
        for g, s in mtool.score.core.intersect([g_g], [p_g]):
            c_num, gold_num, p_num, mapping, ginstances, gattributes, grelations, sinstances, sattributes, srelations = smatch(g, s, 5, {"tops", "labels", "properties", "anchors", "edges", "attributes"}, 0, False, print_align=True, return_tup=True)
            
def get_map(g1, g2):
    for g, s in mtool.score.core.intersect([g1], [g2]):
        c_num, gold_num, p_num, mapping = smatch(g, s, 5, {"tops", "labels", "properties", "anchors", "edges", "attributes"}, 0, False, print_align=False, return_tup=False)
        return mapping

def ensemble(graph_lst):
    assert len(graph_lst) > 1
    # threshold = math.ceil(len(graph_lst)//2)
    global th_rate
    print('th_rate', th_rate)
    threshold = len(graph_lst) * th_rate
    max_support = 0
    ge_node_tab, ge_edge_tab, ge_attr_tab = None, None, None
    for i, g_pivot in enumerate(graph_lst):
        other_g_lst = graph_lst[0:i] + graph_lst[i+1:]
        # 'c' means core
        c_node_tab, c_edge_tab, c_attr_tab, c_attributes, c_relations = initialise(g_pivot, 'c')
        for j, g_curr in enumerate(other_g_lst):
            c_node_tab, c_edge_tab, c_attr_tab = update_tab(c_node_tab, c_edge_tab, c_attr_tab, j, g_curr, g_pivot)
        top_node_id = find_top(c_attributes)
        # TODO: c_relations need to be updated according to c_edge_tab? and generate new c_instances?
        c_node_tab, c_edge_tab, c_attr_tab, this_support = filter_tab(c_node_tab, c_edge_tab, c_attr_tab, top_node_id, threshold)
        if this_support > max_support:
            ge_node_tab, ge_edge_tab, ge_attr_tab = c_node_tab, c_edge_tab, c_attr_tab
            max_support = this_support
    
    return ge_node_tab, ge_edge_tab, ge_attr_tab, max_support

def find_top(attrs):
    for attr_item in attrs:
        if attr_item[0] == 'TOP':
            top_node_id = int(attr_item[1][1:])
            return top_node_id
    print('Do not find top node return 0.')
    return 0

def create_ins_rel(node_tab, edge_tab, attr_tab):
    prefix = 'c'
    # assert attributes[0][1].startswith(prefix)
    instance_lst = []
    for node_id, dic in node_tab.items():
        if len(dic) == 0:
            instance_lst.append(('instance', prefix+str(node_id), '[NULL]'))
            continue
        else:
            assert len(dic) == 1
            instance_lst.append(('instance', prefix+str(node_id), list(dic.keys())[0]))
    
    rel_lst = []
    for (h_id, t_id), dic in edge_tab.items():
        if len(dic) == 0:
            continue
        else:
            assert len(dic) == 1
            rel_lst.append((list(dic.keys())[0], prefix+str(h_id), prefix+str(t_id)))

    attr_lst = []
    for (node_id, attr_name), dic in attr_tab.items():
        if len(dic) == 0:
            # print((node_id, attr_name) is none)
            continue
        else:
            assert len(dic) == 1
            attr_lst.append((attr_name, prefix+str(node_id), list(dic.keys())[0]))

    return instance_lst, attr_lst, rel_lst

def update_tab(c_node_tab, c_edge_tab, c_attr_tab, curr_g_id, curr_g, g_povit):
    s_prefix = 's' + str(curr_g_id)
    s_node_tab, s_edge_tab, s_attr_tab, s_attributes, s_relations = initialise(curr_g, s_prefix)
    mapping = get_map(g_povit, curr_g)
    # update node table
    for povit_node_id, map_node_id in enumerate(mapping):
        if map_node_id == -1:
            continue
        node_label_count_dic = s_node_tab[map_node_id]
        assert len(node_label_count_dic) == 1
        node_label, node_label_count = list(node_label_count_dic.items())[0]
        assert node_label_count == 1
        c_node_tab[povit_node_id][node_label] = c_node_tab[povit_node_id].get(node_label, 0) + node_label_count
    # update edge table
    for c_h_id, c_t_id in c_edge_tab.keys():
        map_h_id, map_t_id = mapping[c_h_id], mapping[c_t_id]
        if map_h_id == -1 or map_t_id == -1:
            continue
        if (map_h_id, map_t_id) not in s_edge_tab:
            continue
        edge_label_count_dic = s_edge_tab[(map_h_id, map_t_id)]
        assert len(edge_label_count_dic) == 1
        edge_label, edge_label_count = list(edge_label_count_dic.items())[0]
        assert edge_label_count == 1
        c_edge_tab[(c_h_id, c_t_id)][edge_label] = c_edge_tab[(c_h_id, c_t_id)].get(edge_label, 0) + edge_label_count
    
    # update attr table
    for node_id, attr_name in c_attr_tab.keys():
        map_node_id = mapping[node_id]
        if map_node_id == -1:
            continue
        if (map_node_id, attr_name) in s_attr_tab:
            s_attr_value_dic = s_attr_tab[(map_node_id, attr_name)]
            value, value_c = list(s_attr_value_dic.items())[0]
            assert value_c == 1
            c_attr_tab[(node_id, attr_name)][value] = c_attr_tab[(node_id, attr_name)].get(value, 0) + 1

    return c_node_tab, c_edge_tab, c_attr_tab

def filter_tab(c_node_tab, c_edge_tab, c_attr_tab, top_node_id, threshold):
    # first delete the ones less than threshold,
    # then choose the largest one.
    
    # currently return the largest one, even it is smaller than threshold,
    # later can chage to real?

    # still use real first
    support_sum = 0
    need_del_nodes = []
    for c_node_id in c_node_tab.keys():
        if c_node_id == top_node_id:
            if 'name' in c_node_tab[c_node_id] and len(c_node_tab[c_node_id]) > 1:
                c_node_tab[c_node_id].pop('name')
            label_count_dic = c_node_tab[c_node_id]
            try:
                new_label_count_dic = {max(label_count_dic): label_count_dic[max(label_count_dic)]}
                support_sum += label_count_dic[max(label_count_dic)]
            except:
                import pdb
                pdb.set_trace()
            c_node_tab[c_node_id] = new_label_count_dic
            continue

        label_count_dic = c_node_tab[c_node_id]
        item_lst = list(label_count_dic.items())
        for node_label, count in item_lst:
            if count < threshold:
                c_node_tab[c_node_id].pop(node_label)
        if len(c_node_tab[c_node_id]) == 0:
            need_del_nodes.append(c_node_id)
            continue
        # choose the largest one
        new_label_count_dic = {max(c_node_tab[c_node_id]): c_node_tab[c_node_id][max(c_node_tab[c_node_id])]}
        support_sum += c_node_tab[c_node_id][max(c_node_tab[c_node_id])]
        c_node_tab[c_node_id] = new_label_count_dic

    for h_id, t_id in c_edge_tab.keys():
        if h_id in need_del_nodes or t_id in need_del_nodes:
            c_edge_tab[(h_id, t_id)] = {}
            continue
        
        label_count_dic = c_edge_tab[(h_id, t_id)]
        item_lst = list(label_count_dic.items())
        for edge_label, count in item_lst:
            if count < threshold:
                c_edge_tab[(h_id, t_id)].pop(edge_label)
        if len(c_edge_tab[(h_id, t_id)]) == 0:
            continue
        # choose the largest one
        new_label_count_dic = {max(c_edge_tab[(h_id, t_id)]): c_edge_tab[(h_id, t_id)][max(c_edge_tab[(h_id, t_id)])]}
        support_sum += c_edge_tab[(h_id, t_id)][max(c_edge_tab[(h_id, t_id)])]
        c_edge_tab[(h_id, t_id)] = new_label_count_dic

    # filter attr table
    for c_node_id, attr_name in c_attr_tab.keys():
        # do not delete (xx, 'TOP')
        if c_node_id == top_node_id and attr_name == 'TOP':
            # TOP only value is ''
            assert len(c_attr_tab[(c_node_id, attr_name)]) == 1
            support_sum += c_attr_tab[(c_node_id, attr_name)]['']
            continue

        value_count_dic = c_attr_tab[(c_node_id, attr_name)]
        item_lst = list(value_count_dic.items())
        for value, count in item_lst:
            if count < threshold:
                c_attr_tab[(c_node_id, attr_name)].pop(value)
        if len(c_attr_tab[(c_node_id, attr_name)]) == 0:
            continue
        new_value_count_dic = {max(c_attr_tab[(c_node_id, attr_name)]): c_attr_tab[(c_node_id, attr_name)][max(c_attr_tab[(c_node_id, attr_name)])]}
        support_sum += c_attr_tab[(c_node_id, attr_name)][max(c_attr_tab[(c_node_id, attr_name)])]
        c_attr_tab[(c_node_id, attr_name)] = new_value_count_dic

    return c_node_tab, c_edge_tab, c_attr_tab, support_sum
    
def initialise(graph, prefix, values={"tops", "labels", "properties", "anchors", "edges", "attributes"}, faith=False):
    for g, _ in mtool.score.core.intersect([graph], []+[graph]):
        instances, attributes, relations, n = tuples(g, prefix, values, faith)
        node_tab = defaultdict(dict)
        nodestr2id = {}
        for i, instance_item in enumerate(instances):
            node_tab[i][instance_item[2]] = 1
            nodestr2id[instance_item[1]] = i
        
        edge_tab = defaultdict(dict)
        for edge_item in relations:
            h_id, t_id = nodestr2id[edge_item[1]], nodestr2id[edge_item[2]]
            edge_tab[(h_id, t_id)][edge_item[0]] = 1

        attr_tab = defaultdict(dict)
        for attr_item in attributes:
            node_id = nodestr2id[attr_item[1]]
            attr_name = attr_item[0]
            attr_tab[(node_id, attr_name)][attr_item[2]] = 1

        return node_tab, edge_tab, attr_tab, attributes, relations

def main(dir_path, len_file, outname):
    global all_sent_res_dic
    ens_file_name = outname
    out_file_name = os.path.join(dir_path, ens_file_name)
    if ens_file_name in os.listdir(dir_path):
        print('ensemble file exists')
        return
    
    pred_path_lst = [os.path.join(dir_path, filename) for filename in os.listdir(dir_path)]
    print('ensembling:', pred_path_lst)

    all_pred_res = []
    for pred_path in pred_path_lst:
        all_pred_res.append(read_graph_frommrp(pred_path))
    
    send_ids = list(all_pred_res[0].keys())
    

    n_cpus = 20
    all_input_dict = []
    for sent_id in send_ids:
        this_dict = {}
        this_dict['sent_id'] = sent_id
        graph_lst = [res_dic[sent_id] for res_dic in all_pred_res]
        this_dict['graph_lst'] = graph_lst
        all_input_dict.append(this_dict)

    pool = Pool(n_cpus)
    pool.map(process, all_input_dict)
    pool.close()
    pool.join()
    n_write_tuple_file(out_file_name, all_sent_res_dic, len_file)


def process(input_dict):
    global all_sent_res_dic
    sent_id = input_dict['sent_id']
    graph_lst = input_dict['graph_lst']
    print(f'processing sent: {sent_id}')
    ge_node_tab, ge_edge_tab, ge_attr_tab, max_support = ensemble(graph_lst)
    ge_inst, ge_attr, ge_rel = create_ins_rel(ge_node_tab, ge_edge_tab, ge_attr_tab)
    node_dic, top_id = normalize_concept_align(ge_inst, ge_attr, graph_lst[0].input)

    rels = get_rels(node_dic, top_id, ge_rel, graph_lst[0].input.strip().split())
    all_sent_res_dic[sent_id.split('.')[1]] = rels





if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, required=True, help="the directory containing all predictions in form of mrp")
    parser.add_argument("--len_file", type=str, required=True, help="the file of max_len")
    parser.add_argument("--outname", type=str, default='ens.tup', help="name of outfile")
    parser.add_argument("--th_rate", type=float, default=0.5, help="rate of threshold")
    args = parser.parse_args()
    global th_rate
    th_rate = args.th_rate

    main(args.dir, args.len_file, args.outname)

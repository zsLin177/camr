import argparse
import re

def read_sentences(file_name, need_syntax=False):
    '''
    # ::id export_amr.1 ::cid export_amr.1 ::2018-07-28 14:46:49
    # ::snt 最近 ， 我们 通过 知情 人士 从 衡阳市 殡葬 管理处 财务 部门 复印 出 部分 原始 发票 凭证 11 份 （ 共计 有 30余 份 ） 。
    # ::wid x1_最近 x2_， x3_我们 x4_通过 x5_知情 x6_人士 x7_从 x8_衡阳市 x9_殡葬 x10_管理处 x11_财务 x12_部门 x13_复印 x14_出 x15_部分 x16_原始 x17_发票 x18_凭证 x19_11 x20_份 x21_（ x22_共计 x23_有 x24_30余 x25_份 x26_） x27_。
    # ::pos_tags ["NT", "PU", "PN", "P", "JJ", "NN", "P", "NR", "NN", "NN", "NN", "NN", "VV", "VV", "CD", "JJ", "NN", "NN", "CD", "M", "PU", "AD", "VE", "CD", "M", "PU", "PU"]
    # ::dependency_edges [13, 13, 13, 13, 6, 4, 13, 10, 10, 12, 12, 7, 0, 13, 18, 17, 18, 13, 20, 13, 23, 23, 20, 25, 23, 23, 13]
    # ::dependency_rels ["tmod", "punct", "nsubj", "prep", "amod", "pobj", "prep", "nn", "nn", "nn", "nn", "pobj", "root", "rcomp", "nummod", "amod", "nn", "dobj", "nummod", "range", "punct", "advmod", "dep", "nummod", "dep", "punct", "punct"]
    (x13 / 复印-01
        :arg0() (x3 / 我们)
        :time() (x1 / 最近)
        :manner() (x4 / 通过-01
                :arg1() (x6 / 人士
                    :arg0-of() (x5 / 知情))
                :arg0() x3 )
        :arg1(x14/出) (x18 / 凭证
                :quant() (x19 / 11)
                :mod() (x17 / 发票
                    :quant() (x15 / 部分)
                    :arg0-of() (x16 / 原始-01))
                :cunit() (x20 / 份)
                :arg0-of() (x90 / mean
                    :arg1() (x22 / 共计-01
                            :arg0(x23/有) (x92 / thing
                                :quant() (x24_3 / 余
                                        :op1() (x24_1_2 / 30))
                                :cunit() (x25 / 份)
                                :dcopy() x18 ))))
        :location(x7/从) (x12 / 部门
                :mod() (x11 / 财务)
                :part-of() (x85 / government-organization
                    :name() (x9_x10 / name :op1 x9/殡葬 :op2 x10/管理处 )
                    :location() (x87 / city
                            :name() (x8 / name :op1 x8/衡阳市 )))))

    return: tokens
    [
        ['最近', '，', '我们', '通过', '知情', '人士', '从', '衡阳市', '殡葬', '管理处', '财务', '部门', '复印', '出', '部分', '原始', '发票', '凭证', '11', '份', '（', '共计', '有', '30余', '份', '）', '。'],
        ['（', '完', '）']
    ]

    '''
    with open(file_name, 'r') as f:
        line_lsts = [line for line in f]

    sentence_lsts = []
    start, i = 0, 0
    for line in line_lsts:
        if line == '\n':
            sentence_lsts.append(line_lsts[start:i])
            start = i + 1
        i += 1
    
    tokens = []
    poses = []
    syntax_labels = []
    sent_ids = []
    for sentence_lst in sentence_lsts:
        sent_ids.append(sentence_lst[0].strip().split()[2])
        tokens.append(sentence_lst[1].strip()[8:])

    if need_syntax:
        return tokens, sent_ids, poses, syntax_labels
    else:
        return tokens, sent_ids

def write(tokens, sent_ids, file_name):
    with open(file_name, 'w') as f:
        for text, id in zip(tokens, sent_ids):
            f.write('\t'.join([id, text])+'\n')

def filter_duplicate_node(file_name, out_name):
    with open(file_name, 'r') as f:
        line_lsts = [line for line in f]

    sentence_lsts = []
    start, i = 0, 0
    for line in line_lsts:
        if line == '\n':
            sentence_lsts.append(line_lsts[start:i])
            start = i + 1
        i += 1
    
    regex = r"(\((x\d+_?)+ / [^ \).]+[ \n\)])"
    # regex = r"(\((x\d+_?)+ / [^ \).]+\)[ \n])"

    import pdb
    new_sent_lsts = []
    for sentence_lst in sentence_lsts:
        new_sent_lst = [] + sentence_lst[0:3]
        already_set = set()
        for amr_line in sentence_lst[3:]:
            groups = re.findall(regex, amr_line)
            if len(groups) == 0:
                new_sent_lst.append(amr_line)
                continue
            for group in groups:
                raw_tgt = group[0]
                tgt = raw_tgt.strip()
                # del (
                tgt = tgt[1:]
                if tgt[-1] == ')':
                    tgt = tgt[0:-1]
                if tgt not in already_set:
                    already_set.add(tgt)
                else:
                    remain = tgt.split()[0]
                    amr_line = amr_line.replace(raw_tgt, remain)
            new_sent_lst.append(amr_line)
        new_sent_lsts.append(new_sent_lst)
    
    with open(out_name, 'w') as f:
        for sent_lst in new_sent_lsts:
            for line in sent_lst:
                f.write(line)
            f.write('\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw_file", type=str, default='camr_dev.txt', help="path to the raw file")
    parser.add_argument("--out", type=str, default=None, help="path to the outpit file")
    args = parser.parse_args()

    # file_name = 'camr_dev.txt'
    # out_name = 'tmp_new_camr_dev.txt'
    file_name = args.raw_file
    out_name = args.out
    filter_duplicate_node(file_name, out_name)
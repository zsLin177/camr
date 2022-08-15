#!/usr/bin/env python3
# conding=utf-8
#
# Copyright 2020 Institute of Formal and Applied Linguistics, Faculty of
# Mathematics and Physics, Charles University, Czech Republic.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import torch

from data.batch import Batch
from utility.evaluate import evaluate


def sentence_condition(s, f, l):
    return ("framework" not in s or f == s["framework"]) and ("framework" in s or f in s["targets"])

@torch.no_grad()
def ensemble_predict(model_lst, data, input_paths, args, output_directory, gpu, run_evaluation=False, epoch=None):
    for model in model_lst:
        model.eval()
    input_files = {(f, l): input_paths[(f, l)] for f, l in args.frameworks}

    sentences = {(f, l): {} for f, l in args.frameworks}
    for framework, language in args.frameworks:
        with open(input_files[(framework, language)], encoding="utf8") as f:
            for line in f.readlines():
                line = json.loads(line)

                if not sentence_condition(line, framework, language):
                    continue

                line["nodes"] = []
                line["edges"] = []
                line["tops"] = []
                line["framework"] = framework
                line["language"] = language
                sentences[(framework, language)][line["id"]] = line

    for i, batch in enumerate(data):
        with torch.no_grad():
            # all_predictions = model(Batch.to(batch, gpu), inference=True)
            all_predictions = ensemble_forward(model_lst, batch, gpu)

        for (framework, language), predictions in all_predictions.items():
            for prediction in predictions:
                for key, value in prediction.items():
                    sentences[(framework, language)][prediction["id"]][key] = value

    for framework, language in args.frameworks:
        output_path = f"{output_directory}/prediction_{framework}_{language}.json"
        with open(output_path, "w", encoding="utf8") as f:
            for sentence in sentences[(framework, language)].values():
                json.dump(sentence, f, ensure_ascii=False)
                f.write("\n")
                f.flush()

        if args.log_wandb:
            import wandb
            wandb.save(output_path)

        if run_evaluation:
            # this should be run in parallel, if your setup allows it
            evaluate(output_directory, epoch, framework, language, input_files[(framework, language)])


@torch.no_grad()
def ensemble_forward(model_lst, batch, gpu, inference=True):
    output = {}

    batch = Batch.to(batch, gpu)
    every_input, word_lens = batch["every_input"]
    # the query_length of different models should be same
    decoder_lens = model_lst[0].query_length * word_lens
    batch_size, input_len = every_input.size(0), every_input.size(1)
    device = every_input.device
    sel_inputs_lst = [model.get_selected_inputs(batch, every_input, word_lens, decoder_lens, batch_size, input_len, device) for model in model_lst]

    avg_label_pred, avg_anchor_pred = 0, 0
    decoder_output_lst = []
    for model, (encoder_output, decoder_output, encoder_mask, decoder_mask, n_batch) in zip(model_lst, sel_inputs_lst):
        this_labelp, this_anchorp = model.heads[0].get_labelp_anchorp(encoder_output, decoder_output, encoder_mask, decoder_mask, n_batch)
        decoder_output_lst.append(decoder_output)
        avg_label_pred += this_labelp
        avg_anchor_pred += this_anchorp
    avg_label_pred /= len(model_lst)
    avg_anchor_pred /= len(model_lst)

    labels, anchors, decoder_output_lst = model_lst[0].heads[0].get_labels_anchors(avg_label_pred, avg_anchor_pred, batch_size, word_lens, decoder_lens, decoder_output_lst)

    properties, tops, edge_presence, edge_labels =  0, 0, 0, 0
    for model, decoder_output in zip(model_lst, decoder_output_lst):
        t_properties, t_tops, t_edge_presence, t_edge_labels, t_edge_attributes = model.heads[0].get_pro_top_edp_edl_eda(decoder_output)
        properties += t_properties
        tops += t_tops
        edge_presence += t_edge_presence
        edge_labels += t_edge_labels
        
    edge_attributes = None
    properties /= len(model_lst)
    tops /= len(model_lst)
    edge_presence /= len(model_lst)
    edge_labels /= len(model_lst)
    
    output[model_lst[0].dataset.id_to_framework[0]] = model_lst[0].heads[0].get_output(labels, anchors, properties, tops, edge_presence, edge_labels, edge_attributes, sel_inputs_lst[0][-1], word_lens, batch_size)

    return output

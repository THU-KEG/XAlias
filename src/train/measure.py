import numpy as np


def hit_evaluate(records, num_return_sequences):
    hits = []
    num_q = len(records)
    for q in range(num_q):
        record = records[q]
        pattern2predicts = record['pred']
        assert len(pattern2predicts) == 1
        pred_words = pattern2predicts[0]
        tgt_words = record['tgt']
        has_answers_q = [True if pred_word in tgt_words else False for pred_word in pred_words]
        pred_words_num = len(pred_words)
        hits_q = [1] * pred_words_num
        for i, h in enumerate(has_answers_q):
            if h:
                break
            else:
                hits_q[i] = 0
        # Note: pred_words_num may be <= num_return_sequences
        if pred_words_num < num_return_sequences:
            if hits_q[-1] == 0:
                hits_q += [0] * (num_return_sequences - pred_words_num)
            else:
                hits_q += [1] * (num_return_sequences - pred_words_num)
        hits.append(hits_q)
    # So now we don't need to check the length again!
    # complete_hits = []
    # for hit_list in hits:
    #     if len(hit_list) == num_return_sequences:
    #         complete_hits.append(hit_list)
    # result_hits = np.array(complete_hits)
    result_hits = np.array(hits)
    result_np = result_hits.mean(0)
    result = result_np.tolist()

    # print("{} in {} question has no answer".format(no_ans_question_num, num_q))
    return {"hits@" + str(i): v * 100 for i, v in enumerate(result)}


def get_avg_generate_nums(records):
    pattern_num = len(records[0]['pred'])
    avg_predict_nums = [0] * pattern_num
    for record in records:
        pattern2predicts = record['pred']
        for i, pattern2predict in enumerate(pattern2predicts):
            avg_predict_nums[i] += len(pattern2predict)
    for k in range(pattern_num):
        avg_predict_nums[k] = avg_predict_nums[k] / len(records)
    return avg_predict_nums

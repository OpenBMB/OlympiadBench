import os, sys, re
import json
import argparse
sys.path.append('code')
from evaluators.math_judger import MathJudger


def calculate_merged_accuracy(text_only):
	if text_only:
		print('*'*20 + ' evaluating in text-only mode ' + '*'*20)

	for model in os.listdir('merged_result'):
		print('-'*10 + model + '-'*10)
		total_scored_num = 0
		total_correct_num = 0
		for dataset_fn in os.listdir(os.path.join('merged_result', model)):
			if dataset_fn[-5:] != '.json':
				continue
			dataset = dataset_fn[:-5]
			full_num = 0
			machine_scored_num = 0
			correct_num = 0
			
			# with open(os.path.join(reference_dir, datasets_file[dataset]), 'r', encoding='utf-8') as f:
			# 	ref_json = json.load(f)
			# 	if text_only:
			# 		ref_json = [d for d in ref_json if 'https://cdn' not in d.get('Context', '')+d['题目']]
			# 	ref_id_list = [d['id'] for d in ref_json]
			# 	scoring_ref_id_list = [d['id'] for d in ref_json if d['是否可机评']]
				
			generated_id_list = []
			machine_scored_list = []

			single_result_path = os.path.join('merged_result', model, dataset_fn)
			with open(single_result_path, 'r', encoding='utf-8') as f:
				single_result_dict = json.load(f)
				if text_only:
					single_result_dict = [d for d in single_result_dict if 'https://cdn' not in d.get('Context', '')+d['题目']]

				available_single_result_dict = [d for d in single_result_dict if (len(d['model_output'][model]['raw_output'])>0 and d['model_output'][model]['raw_output'] != '<Inappropriate content in response>' and d['model_output'][model]['raw_output']!='<No response>' and ('code:' not in d['model_output'][model]['raw_output'] or 'message:' not in d['model_output'][model]['raw_output']))]
				# generated_id_list += [d['id'] for d in available_single_result_dict if (d['id'] in ref_id_list)]
				# TODO：是否可机评+统计一下missing id
				# machine_scored_list += [d['id'] for d in available_single_result_dict if (d['是否可机评'] and d['id'] in ref_id_list)]
				correct_num += len([1 for d in available_single_result_dict if (d['是否可机评'] and d['model_output'][model]['correctness'] and d['id'] in ref_id_list)])

			full_num = len(generated_id_list)
			machine_scored_num = len(machine_scored_list)
			# missing_id_list = [id for id in ref_id_list if id not in generated_id_list]
			# missing_scoring_id_list = [id for id in scoring_ref_id_list if id not in machine_scored_list]
			# id_path = os.path.join('merged_result', model, f'{dataset}_missing_id.txt')
			# with open(id_path, 'w', encoding='utf-8') as id_f:
			# 	id_f.write(str(missing_id_list))
			# 	id_f.write('\n')
			# 	id_f.write(str(missing_scoring_id_list))
			accuracy = -1
			if machine_scored_num > 0:
				accuracy = (correct_num + 0.0) / machine_scored_num * 100
			print('-'*3 + dataset)
			print(f'{full_num} finished\t|{machine_scored_num} scored\t|accuracy={accuracy:.2f}%\t|{len(missing_scoring_id_list)} missing\t|{correct_num} correct')
			total_scored_num += machine_scored_num
			total_correct_num += correct_num
		print('Average accuracy: ', (total_correct_num + 0.0) / total_scored_num * 100)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--text_only", action='store_true') 
	args = parser.parse_args()
	calculate_merged_accuracy(text_only=args.text_only)
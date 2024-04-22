import os, sys, re
import json
from tqdm import tqdm
sys.path.append('code')
from evaluators.math_judger import MathJudger

def extract_answer(is_chinese, model_output, is_deepseek=False):
	# deepseekmath has special answering format
	if is_deepseek:
		if is_chinese:
			matches = re.findall('## 解题答案(.*)', model_output)
		else:
			matches = re.findall('The answer is: (.*)', model_output)
    
		# 检测是否至少找到一个匹配，如果没有就直接整个送进去找\boxed{}
		if matches:
			# 如果找到多个匹配，取最后一个
			model_answer = matches[-1].strip()
			return model_answer
		else:
			return model_output
		
	if is_chinese:
		matches = re.findall('所以最终答案是(.*)', model_output)
	else:
		matches = re.findall('So the final answer is (.*)', model_output)

	# 检测是否至少找到一个匹配，如果没有就直接整个送进去找\boxed{}
	if matches:
		# 如果找到多个匹配，取最后一个
		model_answer = matches[-1].strip()
		return model_answer
	else:
		return model_output


def judge_result():
	judger = MathJudger()

	for dataset in os.listdir('generated'):
	# for dataset in ['pho']:
		print('-'*10 + dataset + '-'*10)
		for model in os.listdir(os.path.join('generated', dataset)):
			is_deepseek = True if 'deepseek' in model else False
			print(model)
			results_path = os.path.join('generated', dataset, model)
			if os.path.exists(results_path):
				full_num = 0
				machine_scored_num = 0
				correct_num = 0
				available_id_list = []	# deduplication
				merged_result = []
				for single_result in tqdm(os.listdir(results_path)):
					if single_result[-5:] != '.json':
						continue
					single_result_path = os.path.join(results_path, single_result)
					single_result_dict = []
					with open(single_result_path, 'r', encoding='utf-8') as f:
						single_result_dict = json.load(f)
						for id, question in enumerate(single_result_dict):
							if (len(question['model_output'][model]['raw_output'])>0 and question['model_output'][model]['raw_output'] != '<Inappropriate content in response>' and question['model_output'][model]['raw_output']!='<No response>' and ('code:' not in question['model_output'][model]['raw_output'] or 'message:' not in question['model_output'][model]['raw_output'])):
								if question['id'] in available_id_list:	# 重复数据
									continue
								else:
									available_id_list.append(question['id'])
							full_num += 1
							# TODO：改成整个数据集层面的
							if question['是否可机评']:
								machine_scored_num += 1
								is_chinese = 'Chinese' in question['classification']
								model_answer = question['model_output'][model]['raw_output']
								model_answer = extract_answer(is_chinese, model_answer, is_deepseek)

								answer_type = question['answer_type']
								if ('Need_human_evaluate' in answer_type) or ('Tuple' in answer_type):
									judge_result = judger.judge(model_answer, question['final_answer'][0])
								else:
									if ',' in question['error']:
										precisions = question['error'].split(',')
										precisions = [float(p) for p in precisions]
										judge_result = judger.judge(model_answer, question['final_answer'][0], precisions)
									else:
										if question['error']:
											precision = float(question['error'])
											judge_result = judger.judge(model_answer, question['final_answer'][0], precision)
										else:
											judge_result = judger.judge(model_answer, question['final_answer'][0])

								if judge_result:
									correct_num += 1
								single_result_dict[id]['model_output'][model]['answer'] = model_answer
								single_result_dict[id]['model_output'][model]['correctness'] = judge_result
						merged_result += single_result_dict

				if not os.path.exists(os.path.join('merged_result', model)):
					os.makedirs(os.path.join('merged_result', model))
				with open(os.path.join('merged_result', model, f'{dataset}.json'), 'w', encoding='utf-8') as f:
					json.dump(merged_result, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
	judge_result()

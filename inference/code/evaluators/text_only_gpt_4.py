import os
import re
from tqdm import tqdm
import openai
from evaluators.evaluator import Evaluator
from time import sleep
import time
import concurrent.futures
import requests
from requests.exceptions import RequestException
import json


def make_input(prompt, question_content, is_chinese, is_math):
	if is_chinese:
		subject = '数学' if is_math else '物理'
		question_message = prompt + '\n' + question_content
		messages = [
			{
				'role': 'system',
				'content': f'你是一个中文人工智能助手。请根据要求，完成下面的{subject}竞赛题目。'
			},
			{
				'role': 'user',
				'content': question_message
			}
		]
	else:
		subject = 'Math' if is_math else 'Physics'
		question_message = prompt + '\n' + question_content
		messages = [
			{
				'role': 'system',
				'content': f'You are an AI assistant. Please answer the following {subject} competition questions as required.'
			},
			{
				'role': 'user',
				'content': question_message
			}
		]
	return messages

# 发送请求到OpenAI
def call_openai(api_key, endpoint, input):

	headers = {   
		"Content-Type": "application/json",   
		"Authorization": f"Bearer {api_key}",
	} 

	data = { 
		"model": "gpt-4-0125-preview",
		"messages": input,
		"temperature": 0.,
		"max_tokens": 2048
	}   
	response = requests.post(endpoint, headers=headers, json=data)
	response.raise_for_status()  # 如果请求失败，抛出异常
	return response.json()

def judge_answer(judger, is_chinese, origin_answer, model_output):
	if is_chinese:
		matches = re.findall('所以最终答案是(.*)', model_output)
	else:
		matches = re.findall('So the final answer is (.*)', model_output)

	# 检测是否至少找到一个匹配，如果没有就直接整个送进去找\boxed{}
	if matches:
		# 如果找到多个匹配，取最后一个
		model_answer = matches[-1].strip()
		return model_answer, judger.judge(origin_answer, model_answer)
	else:
		return model_output, judger.judge(origin_answer, model_output)

# 线程工作函数
def worker(subset_questions, judger, model_name):
	api_list = [
		{
			'endpoint': YOUR_ENDPOINT,
			'api_key': YOUR_API_KEY
		}
	]
	result_list = []
	print('Running question', subset_questions[0]['id'])
	for question in subset_questions:
		retries = 0
		is_chinese = 'Chinese' in question['classification']
		is_math = 'Math' in question['classification']
		if is_math:
			input = make_input(question['prompt'], question['question'], is_chinese, is_math)
		else:
			if 'Context' in question.keys():
				input = make_input(question['prompt'], question['context']+'\n'+question['question'], is_chinese, is_math)
			else:
				input = make_input(question['prompt'], question['question'], is_chinese, is_math)
		while retries < 10:  # 最多重试10次
			try:
				api = api_list[retries % len(api_list)]
				result = call_openai(api['api_key'], api['endpoint'], input)
				# print(result)
				answer = result['choices'][0]['message']['content']

				if 'model_output' not in question.keys():
					question['model_output'] = {model_name:{'raw_output':answer}}
				else:
					question['model_output'][model_name] = {'raw_output':answer}
				result_list.append(question)
				break  # 请求成功，跳出循环
			except RequestException as e:
				print(str(e))
				wait = 2 ** retries  # 指数等待
				print(f"Request failed, retrying in {wait} seconds...")
				time.sleep(wait)
				retries += 1
	return result_list

class Text_Only_GPT_4_Evaluator(Evaluator):
	def __init__(self, model_name, k=-1):
		super(Text_Only_GPT_4_Evaluator, self).__init__(model_name, k)

	def eval_dataset(self, json_dataset_path, json_dataset, save_result_dir):
		self.json_dataset_path = json_dataset_path
		self.get_image_mapping_dict()
		self.is_theorem_proving = 'TP' in json_dataset_path
		self.is_math = 'maths' in json_dataset_path
		self.is_chinese = 'zh' in json_dataset_path
		
		if not os.path.exists(save_result_dir):
			os.mkdir(save_result_dir)
		json_result = []
		new_json_dataset = []

		for id in tqdm(range(len(json_dataset))):
			question = json_dataset[id]
			prompt = self.make_prompt(question)
			question['prompt'] = prompt
		reported_num = 0
		with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
			futures = []
			for i in range(0, len(new_json_dataset), 10):
				future = executor.submit(worker, new_json_dataset[i:i+10], self.judger, self.model_name)
				futures.append(future)
			for future in concurrent.futures.as_completed(futures):
				json_result += future.result()
				if int(len(json_result)/500) > (reported_num/500):
					print(f'Now finished {len(json_result)} questions.')
		with open(os.path.join(save_result_dir, f'{self.model_name}_0_to_end.json'), 'w', encoding='utf-8') as f:
			json.dump(json_result, f, ensure_ascii=False, indent=4)
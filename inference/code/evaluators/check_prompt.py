import os
import json
from tqdm import tqdm
import openai
from evaluators.evaluator import Evaluator
from time import sleep
import re


class Check_Prompt_Evaluator(Evaluator):
	def __init__(self, model_name, k=-1):
		super(Check_Prompt_Evaluator, self).__init__(model_name, k)
		
	def make_input(self, prompt, question_content):
		return prompt

	def get_answer(self, input):
		return input

	def eval_dataset(self, is_chinese, is_math, json_dataset, save_result_dir):
		if not os.path.exists(save_result_dir):
			os.mkdir(save_result_dir)
		temp_result = []
		for id in tqdm(range(len(json_dataset))):
			question = json_dataset[id]
			prompt = self.make_prompt(question)
			input = self.make_input(prompt, question['question'], is_chinese, is_math)
			answer = self.get_answer(input)
			if 'model_output' not in question.keys():
				question['model_output'] = {self.model_name:{'raw_output':answer}}
			else:
				question['model_output'][self.model_name] = {'raw_output':answer}
			temp_result.append(question)
		with open(os.path.join(save_result_dir, f'{self.model_name}.json'), 'w', encoding='utf-8') as f:
			json.dump(temp_result, f, ensure_ascii=False, indent=4)
		return json_dataset
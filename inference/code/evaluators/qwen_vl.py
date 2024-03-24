from evaluators.evaluator import Evaluator
from time import sleep
import os, re
from http import HTTPStatus
import dashscope
from dashscope import MultiModalConversation


class Qwen_VL_Evaluator(Evaluator):
	def __init__(self, model_name, k=-1):
		super(Qwen_VL_Evaluator, self).__init__(model_name, k)
		self.api_pool = [
			YOUR_API_KEY
		]
		
	def split_markdown(self, md):
		# use regex to extract image property
		items = re.split('(<img_\d+>)', md)

		# 从分割后的字符串列表中去除空的元素（完全由空白符、换行符或制表符构成的字符串）
		items = [item for item in items if item and not item.isspace()]
		message_items = []
		for item in items:
			if item[:5] == '<img_':
				image_path = os.path.join(self.image_parent_dir, item[1:-1]+'.jpg')
				if not os.path.exists(image_path):
					print('Image file not found!')
				image_abs_path = os.path.abspath(image_path)
				message_items.append({
					'image': f'file://{image_abs_path}'
				})
			else:
				message_items.append({
					'text': item.strip()
				})

		return message_items

	def make_input(self, prompt, question_content):
		if self.is_chinese:
			subject = '数学' if self.is_math else '物理'
			question_message = self.split_markdown(prompt + '\n' + question_content)
			messages = [
				{
					'role': 'system',
					'content': [{'text': f'你是一个中文人工智能助手。请根据要求，完成下面的{subject}竞赛题目。'}]
				},
				{
					'role': 'user',
					'content': question_message
				}
			]
		else:
			subject = 'Math' if self.is_math else 'Physics'
			question_message = self.split_markdown(prompt + '\n' + question_content)
			messages = [
				{
					'role': 'system',
					'content': [{'text': f'You are an AI assistant. Please answer the following {subject} competition problems as required.'}]
				},
				{
					'role': 'user',
					'content': question_message
				}
			]
		return messages

	def get_answer(self, input):
		model_response = None
		timeout_counter = 0
		retry_counter = 0
		retry_message = ''
		api_key = ''
		while model_response is None and timeout_counter<=5 and retry_counter<=5:
			try:
				api_key = self.api_pool[retry_counter % len(self.api_pool)]
				response = dashscope.MultiModalConversation.call(
					model='qwen-vl-max',
					api_key=api_key,
					messages=input,
					top_k=1,
				)
				if response.status_code == HTTPStatus.OK:
					response_content = response['output']['choices'][0]['message']['content']
					if len(response_content) == 1:
						model_response = response_content[0]['text']
					else:
						model_response = ''
						for c in response_content:
							if 'text' in c.keys():
								model_response += c['text'] + '\n'
							elif 'image' in c.keys():
								model_response += f'![]({c["image"]})' + '\n'
				else:
					print(response.code)  # The error code.
					print(response.message)  # The error message.
					retry_message = f'code:{response.code}\nmessage:{response.message}'
					if 'inappropriate content' in retry_message:
						answer = retry_message
						return answer
					if 'Range of input length' in retry_message:
						answer = retry_message
						return answer
					if 'quota' in retry_message:
						print(retry_message)
						self.api_pool.remove(api_key)
						print(f'Deleting api_key {api_key}')
						with open('./qwen_api.txt', 'a', encoding='utf-8') as f:
							f.write(f'Deleting api_key {api_key}\n')
						if len(self.api_pool)==0:
							exit()
					retry_counter += 1
			except Exception as msg:
				if "timeout=600" in str(msg):
					timeout_counter+=1
				print(msg)
				retry_message = msg
				retry_counter += 1
				sleep(2 ** retry_counter)
				continue
		if model_response==None:
			answer = retry_message
		else:
			answer = model_response
		return answer

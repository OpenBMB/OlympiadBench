import json
from evaluators.evaluator import Evaluator
from time import sleep
import re, os
import requests
from PIL import Image
from io import BytesIO
import google.generativeai as genai


class Gemini_Pro_Vision_Evaluator(Evaluator):
	def __init__(self, model_name, k=-1):
		super(Gemini_Pro_Vision_Evaluator, self).__init__(model_name, k)
		genai.configure(api_key=YOUR_API_KEY, transport='rest')
		self.vl_model = genai.GenerativeModel('gemini-pro-vision')
		self.text_model = genai.GenerativeModel('gemini-pro')

	def split_markdown(self, md):
		# use regex to extract image property
		items = re.split('(<img_\d+>)', md)

		# 从分割后的字符串列表中去除空的元素（完全由空白符、换行符或制表符构成的字符串）
		items = [item for item in items if item and not item.isspace()]
		message_items = []
		text_only = True
		for item in items:
			if item[:5] == '<img_':
				text_only = False
				image_path = os.path.join(self.image_parent_dir, item[1:-1]+'.jpg')
				if not os.path.exists(image_path):
					print('Image file not found!')
				image_pil = Image.open(image_path)
				message_items.append(image_pil)
			else:
				message_items.append(item.strip())
		return message_items, text_only

	def make_input(self, prompt, question_content):
		messages, text_only = self.split_markdown(prompt + '\n' + question_content)
		return {
			'messages': messages,
			'text_only': text_only
		}

	def get_answer(self, input):
		response=None
		timeout_counter=0
		while response is None and timeout_counter<=5:
			try:
				if input['text_only']:
					model_response = self.text_model.generate_content(input['messages'][0])
				else:
					model_response = self.vl_model.generate_content(input['messages'])
				model_response.resolve()
				response = model_response.parts[0].text
			except Exception as msg:
				if "timeout=600" in str(msg):
					timeout_counter+=1
				if 'but none were returned.' in str(msg):
					answer = '<No response>'
					return answer
				print(msg)
				sleep(5)
				continue
		if response==None:
			answer = ''
		else:
			answer = response
		return answer
# OlympiadBench Evaluation

## Sample Code for Evaluation
The `code` folder contains evaluation code used by OlympiadBench. It includes invocation of open-source/closed-source models to answer each problem, and evaluate those parts that can use automated scoring pipeline, in the end verifies its results. The experimental results in the paper are all obtained by running this code, though some prompts were slightly adjusted for publishing due to the modification of the name of dataset items.

### Code Structure
#### Running
All the evaluators are imported in `code/evaluate_all.py`. You can comment out evaluators of the models that are not needed to avoid installing unnecessary libraries.
1. Closed-source models (GPT-4V, GPT-4, Gemini, Qwen)
```
# install packages
pip install -r api_requirements.txt
cd code/
# run evaluation
python evaluate_all.py --model_name <MODEL_NAME: gpt-4v/text-only-gpt-4/qwen-vl/gemini-pro-vision> --dataset_name <DATASET_NAME>
# automated judging
cd ..
python judge.py
# print final results
python calculate_accuracy.py
```
2. DeepseekMath-7B
Install package and download the model as demonstrated in [deepseek huggingface repo](https://huggingface.co/deepseek-ai/deepseek-math-7b-rl).
```
cd code/
# run evaluation
python evaluate_all.py --model_name <PATH_TO_MODEL_FOLDER> --dataset_name <DATASET_NAME>
# automated judging
cd ..
python judge.py
# print final results
python calculate_accuracy.py
```

#### Code Explanation
All model evaluations are based on the Evaluator class in `code/evaluators/evaluator.py`. This base class implements the following functions:

- Providing the prompt used for testing according to the attributes of the problem (e.g. language, subject, answer type, etc.): `make_prompt()`function.
- A pipeline that processes data, calls the model, and saves the results: `eval_dataset()`function.

Each model inherits the `Evaluator` class to define a corresponding subclass (e.g. the `GPT_4V_Evaluator` class), and defines the folowing functions in the subclass:

- Intergrating the prompt and the question into an input that complies with the model's input rules: `make_input()`function.
- Receiving the input, calling the model to obtain the output: `get_answer()`function.
- Other function that is needed for using the model (e.g. processing the image data to the required format).

During evaluation, run in the `code` folder `python evaluate_all.py` to evaluate the model, with command line parameters:

- `--model_name` (required): The name of the model to be evaluated. For closed-source models, sometimes it should be the path to the model.
- `--dataset_path`(required): The dataset to be evaluated.
- `--save_dir`: Path to save the generated result, default to `generated`.
- `--saving_name`: The name of the folder to save results under `save_dir`, default to `model_name` if not given.
- `--cuda_device`: Used for closed-source models.

After generating the answer, you can run `judge.py` to extract the model's answer for open-ended problems and determine their correctness. The automated scoring pipeline is defined in `code/math_judger.py`. You can print the results by running `calculate_accuracy.py`.


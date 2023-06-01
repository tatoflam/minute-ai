import os

base_dir = os.path.dirname(__file__)
logging_conf = os.path.join(base_dir, 'config/logging.json')
gpt_model = "gpt-3.5-turbo"
#gpt_model = "gpt-4"
max_token_length = 4097 # gpt-3.5-turbo
# max_token_length = 8192 # gpt-4
# max_token_length = 32768 # gpt-4-32k
completion_token_length = 256 # gpt-3.5-turbo
completion_token_length = 0 # gpt-4 (as it is not explicitly described on completion prompt)
token_overhead = 1000
whisper_model = "whisper-1"
whisper_pricing_per_min = 0.006 # as of April 2023
gpt_pricing_per_1k_token = 0.002
num_short_text = 200
temp_short_mp3 = "./data/temp_short.mp3"
openai_api_key_name = "OPENAI_API_KEY"
# Langchain summary prompt ("refine", "map_reduce", or other(no use of langchain))
SUMMARY_PROMPT = "refine"

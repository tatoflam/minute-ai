import json
import argparse
import os
import sys
import traceback
from logging import config, getLogger

from util import detect_lang_by_whisper, detect_lang_by_langdetect, \
    tokenize, split_transcript, detect_lang_code, serialize
from constants import logging_conf, openai_api_key_name, gpt_model, \
    whisper_pricing_per_min, gpt_pricing_per_1k_token,  max_token_length, \
    token_overhead
from api import transcribe_files, get_summarized_content, set_key, get_translated_content, get_summarized_content_by_langchain
from prompt import summary_chunks_user_content
# from sample import sample_text, sample_summary_str
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter

config_dict = None
with open(logging_conf, 'r', encoding='utf-8') as f:
    config_dict = json.load(f)

config.dictConfig(config_dict)
logger = getLogger(__name__)

def add_module_path():
    base_dir = os.path.dirname(__file__)
    if base_dir not in sys.path:
        sys.path.append(base_dir)

def get_arguments():
    parser =  argparse.ArgumentParser(description='Transcribe audio file, summarize it (and translate the summary in provided language)')
    parser.add_argument('--script_file', type=str, help='script file name',
                        required=True)
    parser.add_argument('--files', nargs='*', type=str, default=None, help='Input audio files')
    parser.add_argument('--org_lang', type=str, default=None, help='Language in original audio in ISO-639-1 language code')
    parser.add_argument('--lang', type=str, default=None, help='Translated Language in ISO-639-1 language code')    
    parser.add_argument('--length', type=float, default=None, help='Length in minutes of the input audio file')    
    parser.add_argument('--do_transcribe', type=str, default=None, help='y if doing transcribe')
    parser.add_argument('--user_prompt', type=str, default=None, help='user prompt for additional instruction')
    

    args = parser.parse_args()
    return args
    
def make_minutes(script_file, filenames, org_lang=None,  
         translate_lang=None, length=None, do_transcribe="y",
         user_prompt=None):

    # Transcribe
    logger.info("\nTranscribing..." )
    transcript = str()
    if os.path.exists(script_file):
        # Do below in the shell script
        # do_transcribe = input(f"{script_file} exists. Are you sure to transcribe the audio file? [y/N] ")

        if do_transcribe == "y":
            transcript = transcribe_files(script_file, filenames, org_lang)
        else:
            logger.info("Reading from the existing text transcript.")
            with open(script_file, "r") as file:
                transcript = file.read()
    else:
        transcript = transcribe_files(script_file, filenames, org_lang)
        
    char_counted = len(transcript)
    logger.info(f"--- {char_counted} characters in the transcript from {script_file} ---")        
    # logger.debug(f"--- Entire script ---\n'{transcript}'" )
    
    # Count num tokens from entire transcript
    tokens, tokens_counted = tokenize(gpt_model ,transcript)
    #_, longest_prompt_token_counted = tokenize(
    #    gpt_model, summary_chunks_user_content)
    logger.info(f"--- Token counted: {tokens_counted} ---")
    
#    if (tokens_counted + longest_prompt_token_counted ) > max_token_length:
#        splitted_token_count = max_token_length - \
#            longest_prompt_token_counted - token_overhead
#        transcripts = split_transcript(
#            gpt_model, tokens, splitted_token_count
#            )
#    else:
#        transcripts = [transcript]

#    text_splitter = CharacterTextSplitter()
    text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator = " ", # \s
        # chunk_size is the number of tokens in a chunk. 
        # 3841 = 4097(maximum for gpt-3.5-turbo) - 256 (completion)
        chunk_size = 3841,
        chunk_overlap= 0
    )

    transcripts = text_splitter.split_text(transcript)
    logger.info(len(transcripts))
    # Summarize
    api_tokens = 0
    translate_api_tokens = 0
    translate_usages = []
    
    logger.info(f"\nSummarizing in the original language {org_lang}..." )
    #summary_content, api_tokens_summary, summary_usage = get_summarized_content(transcripts, org_lang, user_prompt)
    result, token_info = get_summarized_content_by_langchain(transcripts, org_lang)
    summary_content = result["output_text"]
    summary_usage = [{}]
    logger.info(summary_content)
    #api_tokens += api_tokens_summary
    

    logger.info("\n--- Minutes summary ---" )
    lang_summary = detect_lang_code(summary_content)
    if  lang_summary != org_lang:
        logger.info(f"OpenAI returned a summary in '{lang_summary}', not in original language '{org_lang}'. Translating it. ")
        s, t, u  = get_translated_content(summary_content, org_lang)
        summary_content = s
        api_tokens += t
        translate_api_tokens += t
        translate_usages.extend(u)
    logger.info(summary_content)
    
    t_name, _ = os.path.splitext(script_file)
    with open(f"{t_name}.md", "w") as file:
        file.write(summary_content)

    # Translate    
    if not ((translate_lang is None) or (translate_lang == "")):
        logger.info(f"\nTranslating summary to '{translate_lang}'..." )
        translate_content, api_tokens_translation, translate_usage  = \
            get_translated_content(summary_content, translate_lang)
        api_tokens += api_tokens_translation
        translate_api_tokens += api_tokens_translation
        translate_usages.extend(translate_usage)

        logger.info(f"\n--- Minutes summary translation in '{translate_lang}'---" )
        
        logger.info(translate_content)
        with open(f"{t_name}_{translate_lang}.md", "w") as file:
            file.write(translate_content)

    logger.info("\n--- Usage  -----------------")
    amount = 0
    whisper_amount = 0
    logger.info("\n--- Usage: Transcription ---")
    if not length is None: 
        whisper_amount = (length * whisper_pricing_per_min)        
        logger.info(f"For whisper, '{whisper_amount:.3f}' USD for '{length:.2f}' minutes * '{whisper_pricing_per_min}' USD/min")
    
    logger.info("\n--- Usage: Summary ---")
#    for u in summary_usage:
#        logger.info(serialize(u))

    if translate_usages != "" :
        logger.info("\n--- Usage: Translation ---")
        for u in translate_usages:
            logger.info(serialize(u))
        
    logger.info("\n--- Usage: Total ---")
    amount = api_tokens / 1000 * gpt_pricing_per_1k_token
    logger.info(f"For GPT, {amount:.3f} USD for {api_tokens} tokens in total * {gpt_pricing_per_1k_token} USD / 1k tokens")
    amount = amount + whisper_amount
    logger.info(f"In total, approximate amount for making minutes was {amount:.3f} USD.\n")

def main():
    is_run = False
    add_module_path()
        
    if os.environ.get(openai_api_key_name) is None:
        logger.info("Please export environment variable OPENAI_API_KEY on your client terminal")
        is_run = False
    else:
        logger.info("Checked OPENAI_API_KEY exists on environment")
        is_run = True

    if is_run:
        # set_key()

        args = get_arguments()

        do_transcribe = args.do_transcribe
        filenames = args.files
        script_file = args.script_file
        translate_lang = args.lang
        length = args.length
        user_prompt = args.user_prompt
        
        if do_transcribe == "y":
            # detect original language from the audio file
            org_lang = detect_lang_by_whisper()
                    
            # Check if the files exist
            for filename in filenames:
                if not os.path.isfile(filename):
                    logger.error(f"File '{filename}' does not exist.")
                    sys.exit(1)
        else:
            # detect original language from the existing transcript    
            org_lang = detect_lang_by_langdetect(script_file)
         
        try:
            make_minutes(script_file, filenames, org_lang, translate_lang, length, do_transcribe, user_prompt)
        except Exception as e:
            logger.error(traceback.print_exc())     
                
    else:
        logger.info("ERROR: Please check the configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
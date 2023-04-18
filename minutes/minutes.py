import json
import argparse
import os
import sys
from logging import config, getLogger

from util import detect_lang_by_whisper, detect_lang_by_langdetect, \
    tokenize, split_transcript, detect_lang_code
from constants import logging_conf, openai_api_key_name, gpt_model, \
    whisper_pricing_per_min, gpt_pricing_per_1k_token,  max_token_length, \
    token_overhead
from api import transcribe_files, summarize, translate, continue_prompt, \
    set_key, translate
from prompt import summary_chunks_user_content
# from sample import sample_text, sample_summary_str

config_dict = None
with open(logging_conf, 'r', encoding='utf-8') as f:
    config_dict = json.load(f)

config.dictConfig(config_dict)
logger = getLogger(__name__)

def add_module_path():
    # Add the "python_modules" directory to the Python path
    base_dir = os.path.dirname(__file__)
    # modules_dir = os.path.join(base_dir, "python_modules")
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

    args = parser.parse_args()
    return args
    
def main(script_file, filenames, org_lang=None,  
         translate_lang=None, length=None, do_transcribe="y"):

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
        
    logger.info(f"--- Entire script ---\n'{transcript}'" )
    
    # Count num tokens from entire transcript
    tokens, tokens_counted = tokenize(gpt_model ,transcript)
    _, longest_prompt_token_counted = tokenize(
        gpt_model, summary_chunks_user_content)
    logger.info(f"--- Token counted: {tokens_counted} ---")
    
    if (tokens_counted + longest_prompt_token_counted ) > max_token_length:
        splitted_token_count = max_token_length - \
            longest_prompt_token_counted - token_overhead
        transcripts = split_transcript(
            gpt_model, tokens, splitted_token_count
            )
    else:
        transcripts = [transcript]
    
    # Summarize
    api_tokens_counted = 0
    logger.info(f"\nSummarizing in the original language {org_lang}..." )
    summary, api_tokens_counted = summarize(transcripts, org_lang)
    
    logger.info("\n--- Minutes summary ---" )
    summary_response = str()
    
    for i, choice in enumerate(summary["choices"]):
        logger.info(f"--- choice: {i} ---")
        
        finish_reason = choice["finish_reason"]
        summary_response += choice["message"]["content"]
        if not isinstance(summary_response, str):
            logger.debug("String content was not responded")
            summary_response = str(summary_response)
        
        # Check finish_response
        logger.info(f"summary finish_reason: '{finish_reason}'")
        if finish_reason == "stop":
            pass
        else:
            logger.info("Continuing prompt...")
            while True:
                continue_choice = continue_prompt()["choice"][0]                
                summary_response += continue_choice["message"]["content"]
                if not isinstance(summary_response, str):
                    logger.debug("String content was not responded")
                    summary_response = str(summary_response)

                continue_usage = continue_prompt()["usage"]
                logger.info(continue_usage)
                api_tokens_counted += continue_usage["total_tokens"]
 
                finish_reason = continue_choice["finish_reason"]                               
                logger.info(f"Continued summary finish reason: '{finish_reason}'")
                if finish_reason=="stop":
                    break
    
    if detect_lang_code(summary_response) != org_lang:
        summary_response = translate(summary_response, org_lang)
                
    logger.info(summary_response)
    
    t_name, _ = os.path.splitext(script_file)
    with open(f"{t_name}.md", "w") as file:
        file.write(summary_response)

    # Translate    
    if not ((translate_lang is None) or (translate_lang == "")):
        logger.info(f"\nTranslating summary to '{translate_lang}'..." )
        translation = translate(summary_response, translate_lang)
        logger.info(f"\n--- Minutes summary translation in '{translate_lang}'---" )
        
        translate_response = str()
        api_tokens_counted += translation["usage"]["total_tokens"]

        for i, choice in enumerate(translation["choices"]):
            logger.info(f"--- choice: {i} ---")
        
            finish_reason = choice["finish_reason"]
            translate_response += choice["message"]["content"]
            
            # Check finish_response
            logger.info(f"translate finish_reason: '{finish_reason}'")
            if finish_reason == "stop":
                pass
            else:
                logger.info("Continuing prompt...")
                while True:                      
                    continue_choice = continue_prompt()["choice"][0]                
                    translate_response += continue_choice["message"]["content"]

                    continue_usage = continue_prompt()["usage"]
                    logger.info(continue_usage)
                    api_tokens_counted += continue_usage["total_tokens"]
    
                    finish_reason = continue_choice["finish_reason"]                               
                    logger.info(f"Continued summary finish reason: '{finish_reason}'")
                    if finish_reason=="stop":
                        break

        logger.info(translate_response)
        with open(f"{t_name}_{translate_lang}.md", "w") as file:
            file.write(translate_response)

    logger.info("\n--- Usage  -----------------")
    amount = 0
    whisper_amount = 0
    logger.info("\n--- Usage: Transcription ---")
    if not length is None: 
        whisper_amount = (length * whisper_pricing_per_min)        
        logger.info(f"For whisper, '{whisper_amount:.3f}' USD for '{length:.2f}' minutes * '{whisper_pricing_per_min}' USD/min")
    
    logger.info("\n--- Usage: Summary ---")
    logger.info(summary["usage"])

    if not ((translate_lang is None) or (translate_lang == "")):
        logger.info("\n--- Usage: Translation ---")
        logger.info(translation["usage"])
        
    logger.info("\n--- Usage: Total ---")
    amount = api_tokens_counted / 1000 * gpt_pricing_per_1k_token
    logger.info(f"For GPT, {amount:.3f} USD for {api_tokens_counted} tokens in total * {gpt_pricing_per_1k_token} USD / 1k tokens")
    amount = amount + whisper_amount
    logger.info(f"In total, approximate amount for making minutes was {amount:.3f} USD.\n")

if __name__ == "__main__":
    is_run = False
    add_module_path()
        
    if os.environ.get(openai_api_key_name) is None:
        logger.info("Please export environment variable OPENAI_API_KEY on your client terminal")
        is_run = False
    else:
        logger.info("Checked OPENAI_API_KEY exists on environment")
        is_run = True

    if is_run:
        set_key()

        args = get_arguments()

        do_transcribe = args.do_transcribe
        filenames = args.files
        script_file = args.script_file
        translate_lang = args.lang
        length = args.length
        
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
         
        main(script_file, filenames, org_lang, translate_lang, length, do_transcribe)
    else:
        logger.info("ERROR: Please check the configuration.")
        sys.exit(1)

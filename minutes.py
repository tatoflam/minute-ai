import argparse
import sys
import os
from util import detect_lang_by_whisper, detect_lang_by_langdetect
from constants import openai_api_key_name, whisper_pricing_per_min, \
    gpt_pricing_per_1k_token
from api import transcribe_files, summarize, translate, continue_prompt, \
    set_key
# from sample import sample_text, sample_summary_str

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
    print("\nTranscribing..." )
    transcripts = str()
    if os.path.exists(script_file):
        # Do below in the shell script
        # do_transcribe = input(f"{script_file} exists. Are you sure to transcribe the audio file? [y/N] ")

        if do_transcribe == "y":
            transcripts = transcribe_files(script_file, filenames, org_lang)
        else:
            print("Reading from the existing text transcripts.")
            with open(script_file, "r") as file:
                transcripts = file.read()
    else:
        transcripts = transcribe_files(script_file, filenames, org_lang)
        
    print(f"--- Entire script ---\n'{transcripts}'" )

    tokens = 0
        
    # Summarize
    print(f"\nSummarizing in the original language {org_lang}..." )
    summary = summarize(transcripts, org_lang)
    
    print("\n--- Minutes summary ---" )
    summary_response = str()
    tokens += summary["usage"]["total_tokens"]
    
    for i, choice in enumerate(summary["choices"]):
        print(f"--- choice: {i} ---")
        
        finish_reason = choice["finish_reason"]
        summary_response += choice["message"]["content"]

        # Check finish_response
        print(f"summary finish_reason: '{finish_reason}'")
        if finish_reason == "stop":
            pass
        else:
            print("Continuing prompt...")
            while True:
                continue_choice = continue_prompt()["choice"][0]                
                summary_response += continue_choice["message"]["content"]

                continue_usage = continue_prompt()["usage"]
                print(continue_usage)
                tokens += continue_usage["total_tokens"]
 
                finish_reason = continue_choice["finish_reason"]                               
                print(f"Continued summary finish reason: '{finish_reason}'")
                if finish_reason=="stop":
                    break
    print(summary_response)
    
    t_name, _ = os.path.splitext(script_file)
    with open(f"{t_name}.md", "w") as file:
        file.write(summary_response)

    # Translate    
    if not ((translate_lang is None) or (translate_lang == "")):
        print(f"\nTranslating summary to '{translate_lang}'..." )
        translation = translate(summary_response, translate_lang)
        print(f"\n--- Minutes summary translation in '{translate_lang}'---" )
        
        translate_response = str()
        tokens += translation["usage"]["total_tokens"]

        for i, choice in enumerate(translation["choices"]):
            print(f"--- choice: {i} ---")
        
            finish_reason = choice["finish_reason"]
            translate_response += choice["message"]["content"]
            
            # Check finish_response
            print(f"translate finish_reason: '{finish_reason}'")
            if finish_reason == "stop":
                pass
            else:
                print("Continuing prompt...")
                while True:                      
                    continue_choice = continue_prompt()["choice"][0]                
                    translate_response += continue_choice["message"]["content"]

                    continue_usage = continue_prompt()["usage"]
                    print(continue_usage)
                    tokens += continue_usage["total_tokens"]
    
                    finish_reason = continue_choice["finish_reason"]                               
                    print(f"Continued summary finish reason: '{finish_reason}'")
                    if finish_reason=="stop":
                        break

        print(translate_response)
        with open(f"{t_name}_{translate_lang}.md", "w") as file:
            file.write(translate_response)

    print("\n--- Usage  -----------------")
    amount = 0
    whisper_amount = 0
    print("\n--- Usage: Transcription ---")
    if not length is None: 
        whisper_amount = (length * whisper_pricing_per_min)        
        print(f"For whisper, '{whisper_amount:.3f}' USD for '{length:.2f}' minutes * '{whisper_pricing_per_min}' USD/min")
    
    print("\n--- Usage: Summary ---")
    print(summary["usage"])

    if not ((translate_lang is None) or (translate_lang == "")):
        print("\n--- Usage: Translation ---")
        print(translation["usage"])
        
    print("\n--- Usage: Total ---")
    amount = tokens / 1000 * gpt_pricing_per_1k_token
    print(f"For GPT, {amount:.3f} USD for {tokens} tokens in total * {gpt_pricing_per_1k_token} USD/min")
    amount = amount + whisper_amount
    print(f"In total, approximate amount for making minutes was {amount:.3f} USD.\n")

if __name__ == "__main__":
    is_run = False
        
    if os.environ.get(openai_api_key_name) is None:
        print("Please export environment variable OPENAI_API_KEY on your client terminal")
        is_run = False
    else:
        print("Checked OPENAI_API_KEY exists on environment")
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
                    print(f"File '{filename}' does not exist.")
                    sys.exit(1)
        else:
            # detect original language from the existing transcript    
            org_lang = detect_lang_by_langdetect(script_file)
         
        main(script_file, filenames, org_lang, translate_lang, length, do_transcribe)
    else:
        print("ERROR: Please check the configuration.")
        sys.exit(1)
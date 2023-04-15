import os
import openai

from prompt import summary_system_content, summary_user_content, \
    translation_system_content, translation_user_content, continue_content
from constants import gpt_model, whisper_model, openai_api_key_name

def set_key():
    openai.api_key = os.environ.get(openai_api_key_name)

def transcribe(filename, org_lang):
    print(f"Processing file: {filename}")
    audio_file= open(filename, "rb")
    transcribed = openai.Audio.transcribe(model=whisper_model, 
                                            file=audio_file,
                                            language=org_lang)
    
    transcript = transcribed["text"].encode('utf-8').decode('utf-8')
    return transcript

def transcribe_files(script_file, filenames, org_lang):
    transcripts = str()
    print("Transcribing from the audio file.")
    for filename in filenames:
        transcript = transcribe(filename, org_lang)
        transcripts += transcript + " "

    with open(script_file, "w") as file:
        file.write(transcripts)
        
    return transcripts
                
def summarize(transcript, org_lang=None):
    summary = openai.ChatCompletion.create(
        model=gpt_model,
        messages=[
            {"role": "system", "content": summary_system_content},
            {"role": "user", 
             "content": summary_user_content.format(
                 org_lang=org_lang, transcript=transcript
                 )
             }
            # {"role": "assistant", "content": ""}
        ]
    )
    return summary

def continue_prompt():
    response = openai.ChatCompletion.create(
        model=gpt_model,
        messages=[
            {"role": "system", "content": summary_system_content},
            {"role": "user", 
             "content": continue_content}
            # {"role": "assistant", "content": ""}
        ]
    )
    return response

def translate(summary, translate_lang):
    translation = openai.ChatCompletion.create(
        model=gpt_model,
        messages=[
            # Switching system content from the prior one does not work?
            # {role": "system", "content": summary_system_content},
            {"role": "system", "content": translation_system_content},
            {"role": "user", 
             "content": translation_user_content.format(
                 summary=summary, lang=translate_lang)}
            # {"role": "assistant", "content": ""}
        ]
    )
    return translation
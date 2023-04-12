import sys
import os
import openai

def transcribe(filename):
    print(f"Processing file: {filename}")
    audio_file= open(filename, "rb")
    transcript = openai.Audio.transcribe(model="whisper-1", 
                                            file=audio_file,
                                            language="en")
    print(transcript["text"].encode('utf-8').decode('utf-8'))

def main(filenames):
    for filename in filenames:
        transcribe(filename)

if __name__ == "__main__":
    is_run = False

    # Check if there are any arguments
    if len(sys.argv) < 2:
        print("Usage: python process_files.py <filename1> <filename2> ...")
        is_run = False
    else:
        is_run = True
        
    if not len(os.environ.get("OPENAI_API_KEY"))>0:
        print("Please export OPENAI_API_KEY on your client terminal")
        is_run = False
    else:
        print("Checked OPEN_API_KEY exists on environment")
        is_run = True

    if is_run:
        filenames = sys.argv[1:]
        openai.api_key = os.environ.get("OPENAI_API_KEY")
            
        # Check if the files exist
        for filename in filenames:
            if not os.path.isfile(filename):
                print(f"File '{filename}' does not exist.")
                sys.exit(1)

        main(filenames)
    else:
        print("ERROR: Please check the configuration.")
        sys.exit(1)
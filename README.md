# minutes-ai

- Transcribes audio spoken in any language
- Outputs a summary of that language and any translated language in markdown format.  

This tool does: 

- convert input file into `mp3` (as it's relatively smaller than the other formats) and splitting it into appropriate sized chunk to send to whisper API by `ffmpeg`
- detect original language spoken and make a transcript by whisper text-to-speech API (`whisper-1`)
- summarize the transcript into a meeting note in the markdown format and translate it into the other language provided by `gpt-3.5-turbo`

## Usage

### Preparation

- Get [OpenAI API Key](https://platform.openai.com/account/api-keys)
- Set [OpenAI Billing Usage Limits](https://platform.openai.com/account/billing/limits)
  - This configuration is required to call the whisper API. 
- Setup this tool
  - See [Install](#install)

### Export Open AI API Key

Export Open AI API Key with the name "OPENAI_API_KEY" to your environment

    ```
    export OPENAI_API_KEY="your Open AI API Key"
    ```

### Run it! 

run command `./minutes.sh -f "Audio file name" -l "language code"`

- -f: Input file (Audio or text file)
- -l: (Optional) Language to be translated (language code in [ISO-639-1](https://www.loc.gov/standards/iso639-2/php/code_list.php) format). 

For example, 

If you want to make transcript and summary, also include the translation in Japanese language, 

```
./minutes.sh -f ./data/audiofile.m4a -l ja
```

If you do not need the translation for the summary, 

```
./minutes.sh -f ./data/audiofile.m4a
```

If you already have a transcript in text format, you can just summarize and translate it by: 

```
./minutes.sh -f ./data/transcript.txt -l ja
```

After completion, you will find a transcript in `.txt` file, and summaries in the original language and its translation in `.md` files in the same directory of the input file. 

## Install

### Pre-requisite

- python3
- ffmpeg

Create python virtual environment and activate it.

```
python -m venv env
source env/bin/activate
```

Install requirements on the virtual environment.  

```
(env)pip install -r requirements.txt
```

## Security

For transcribing, summarizing or translation, this tool call OpenAI API and pass content to the platform.  

As per OpenAI [API data usage policies](https://openai.com/policies/api-data-usage-policies) updated on March 1 2023, 

- OpenAI will not use data submitted by customers via our API to train or improve our models, unless you explicitly decide to share your data with us for this purpose. You can opt-in to share data.
- Any data sent through the API will be retained for abuse and misuse monitoring purposes for a maximum of 30 days, after which it will be deleted (unless otherwise required by law). 

However, please be careful when using this tool with content that contains your personal or confidential information. 

## Environments (I confirmed)

- Mac OS 12.3
- python 3.10.0
- ffmpeg 5.1.2

## References

- [OpenAI | Speech to Text](https://platform.openai.com/docs/guides/speech-to-text)
- [OpenAI | Production Best Practice](https://platform.openai.com/docs/guides/production-best-practices/)

## What's next?

### TODO:

- Check audio file size and judge if it's necessary to convert format and splitting
- Experiment `gpt-4`

and more.
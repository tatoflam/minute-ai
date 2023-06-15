#!/bin/bash

start=$(date +%s) 
# Initialize variables
short_audio_file="./data/temp_short.mp3"
file=""
script_file=""
do_transcribe="y"
translate_lang=""
length=0
segmented_files=()

add_python_path() {
    # Get the absolute path of the directory containing this script
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Get the absolute path
    base_dir="$(dirname "$script_dir")"

    # Add the "minutes" directory to the Python path
    modules_dir="$script_dir/minutes"
    if [[ ! ":$PYTHONPATH:" == *":$modules_dir:"* ]]; then
        export PYTHONPATH="$modules_dir:$PYTHONPATH"
    fi
}

# Get 30 seconds audio file for the language detection
# Input and output filenames
make_short_audio() {
    input_audio_file="$1"
    duration=$2

    # Get the total duration of the audio file
    total_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$input_audio_file")
    total_duration=${total_duration%.*}

    # Calculate the start time for the 30-second segment
    start_time=$(( (total_duration / 2) - $duration / 2 ))

    # Extract the 30-second segment from the middle of the audio file
    ffmpeg -i "$input_audio_file" -ss "$start_time" -t  $duration -c:a copy "$short_audio_file"
}

# Audio length
get_audio_length(){
    local length=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$1" | awk '{print $1/60}')
    echo "$length"
}

# Function to convert audio files to MP3 format
convert_to_mp3() {
    input_file="$1"
    output_file="${input_file%.*}.mp3"

    if [ "$input_file" != "$output_file" ]; then
        ffmpeg -i "$input_file"  -ar 44100 -ab 128k "$output_file"
        echo "Converted '$input_file' to '$output_file'"
    else
        echo "File '$input_file' is already in MP3 format."
    fi

    # segment file into chunks in 25 minutes
    ffmpeg -i "$output_file" -f segment -segment_time 360 -c copy "${input_file%.*}_%03d.mp3"

    make_short_audio "${input_file%.*}_000.mp3" 180
}

remove_temporal_files(){
    if [ -f "$short_audio_file" ]; then
        rm "$short_audio_file"
        echo "Deleted $short_audio_file"
    fi
    for filename in "$@"
    do
        if [ -f "$filename" ]; then
            rm "$filename"
            echo "Deleted segmented files: $filename" 
        fi
    done
}

# Parse parameters
while getopts :f:l:p: opt
do
    case $opt in
        f)
            file="$OPTARG"
            echo "Option -f $file"
            ;;
        l)
            translate_lang="$OPTARG"
            echo "Option -l $translate_lang"
            ;;
        p)
            prompt="$OPTARG"
            echo "Option -p $prompt"
            ;;
        *)
            echo -e "Usage: $0 -f <audio file> -l <Optional: language to translate in ISO-693-1 code>\n $0 -f input.m4a -l ja"
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
    esac
done

if [ -n "$file" ]; then
    if [ ! -f "$file" ]; then
        echo "File '$file' does not exist."
        exit 1
    fi
else
    echo "Option -f <Audio file name> is required"
    exit 1
fi

script_file="${file%.*}.txt"
if [ -f "$script_file" ]; then
    read -p "File '$script_file' exists. Are you sure to transcribe Audio file? [y/N]" do_transcribe
fi

if [ "$do_transcribe" == "y" ]; then
    length=$(get_audio_length "$file")
    echo "audio length: " $length
    # Convert the file to MP3 format if needed
    convert_to_mp3 "$file"

    mp3_path=${file%.*}_*.mp3
    mp3_dir=$(dirname "$mp3_path")
    mp3_file=$(basename "$mp3_path") 

    while read segmented_file
    do
        echo $segmented_file
        segmented_files+=("${segmented_file}")
    done < <(find "$mp3_dir" -name "$mp3_file"|sort)
fi

add_python_path

if [ $(uname -s) == "Darwin" ]||[ $(uname -s) == "Linux" ]; then
    # Mac or Linux
    source env/bin/activate
else
    source env/Scripts/activate
fi

python minutes/minutes.py \
    --script_file "$script_file" \
    --lang "$translate_lang" \
    --files "${segmented_files[@]}" \
    --length "${length}" \
    --do_transcribe "$do_transcribe" \
    --user_prompt "$prompt"

deactivate

# Delete temporal files
remove_temporal_files "${segmented_files[@]}"

end=$(date +%s)

if [ $(uname -s) == "Darwin" ]||[ $(uname -s) == "Linux" ]; then
    duration=$(echo "($end - $start) / 60" | bc -l)
else
    duration=$(echo $((($end - $start)/60)))
fi

duration=$(printf "%.2f" $duration)
echo "minute.sh completed in $duration minutes!"
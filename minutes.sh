#!/bin/bash

# Initialize variables
short_audio_file="./data/temp_short.mp3"
file=""
script_file=""
translate_lang=""
length=0

# Get 30 seconds audio file for the language detection
# Input and output filenames
make_short_audio() {
    input_audio_file="$1"
    duration=$2

    # Get the total duration of the audio file
    total_duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$input_audio_file")
    total_duration=${total_duration%.*}
    echo "$total_duration"

    # Calculate the start time for the 30-second segment
    start_time=$(( (total_duration / 2) - $duration / 2 ))
    echo "$start_time"

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
    ffmpeg -i "$output_file" -f segment -segment_time 1500 -c copy "${input_file%.*}_%03d.mp3"

    make_short_audio "${input_file%.*}_000.mp3" 30 
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
while getopts :f:l: opt
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

    for segmented_file in $(ls -1 ${file%.*}_*.mp3)
    do
        echo $segmented_file
        # Add the MP3 file to the list of files to process
        segmented_files+=("$segmented_file")
    done
fi

source env/bin/activate

# Pass all MP3 filenames to the Python script
if [ "$translate_lang" != "" ]; then
    echo "translated_lang" "$translate_lang"
    python minutes.py \
        --script_file "$script_file" \
        --lang "$translate_lang" \
        --files "${segmented_files[@]}" \
        --length "${length}" \
        --do_transcribe "$do_transcribe" 
else
    python minutes.py \
        --script_file "$script_file" \
        --files "${segmented_files[@]}" \
        --length "${length}" \
        --do_transcribe "$do_transcribe" 
fi

# Delete temporal files
remove_temporal_files "${segmented_files[@]}"

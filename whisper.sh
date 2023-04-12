#!/bin/bash

# Check if there are any arguments
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <filename1> <filename2> ..."
    exit 1
fi

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
}

# Iterate over all filenames and check if they exist
mp3_files=()
for filename in "$@"
do
    if [ ! -f "$filename" ]; then
        echo "File '$filename' does not exist."
        exit 1
    fi

    # Convert the file to MP3 format if needed
    convert_to_mp3 "$filename"

    # Add the MP3 file to the list of files to process
    mp3_files+=("${filename%.*}.mp3")
done

# Pass all MP3 filenames to the Python script
source env/bin/activate
python3 whisper.py "${mp3_files[@]}"
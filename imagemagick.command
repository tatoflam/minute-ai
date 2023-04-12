
# convert f4a to mp3
# ffmpeg -i ./data/AJ_20230406.m4a ./data/AJ_20230406.mp3
ffmpeg -i ./data/AJ_20230406.m4a -ar 44100 -ab 128k ./data/AJ_20230406.mp3


# split file into files in 180 seconds
ffmpeg -i ./data/file.mp3 -f segment -segment_time 1500 -c copy ./data/file-%03d.mp3
ffmpeg -i ./data/AJ_20230406.mp3 -f segment -segment_time 180 -c copy ./data/AJ_20230406%03d.mp3

# split file into files based on the size of chunk
ffmpeg -i ./data/AJ_20230413_Efficacy_analysis.m4a -c copy -map 0 -f segment -segment_size 26214400 -reset_timestamps 1 output_segment_%03d.mp3
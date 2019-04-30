#!/usr/bin/env bash

# Extracts and saves video frames from a source video

if [ $# -eq 0 ]
  then
    echo "Supply at least the source video"
    echo "Usage: $0 video -fps 1.5 -frame_width 1080 -frame_type jpg -frame_prefix frame_ -frame_basedir frames -luminescence_threshold 70 -blackness_percent 95"
    echo
    echo "All parameters are optional except for the video (the video filename)"
    echo " -fps: The frames per second at which the video frames are sampled"
    echo " -frame_width: The width in pixels of the produced frames"
    echo " -frame_type: The output frame (image) type. Possible values: jpg, png"
    echo " -frame_prefix: The file name prefix of the files produced"
    echo " -frame_basedir: The base directory where frames are put"
    echo " -luminescence_threshold: Threshold [0-256] to evaluate whether a pixel is consider black"
    echo " -blackness_percent: Allowed percentage of blackness in frame. If more pixels than this percent are black the frame is skipped"
    echo
    exit 1
fi

video=$1
fps=1.0
frame_width=1080
frame_type=jpg
frame_prefix=frame_
luminescence_threshold=70
blackness_percent=95
frame_basedir=frames

shift
while (( "$#" )); do
  case "$1" in
    -fps|-frame_width|-frame_type|-frame_prefix|-frame_basedir|-luminescence_threshold|-blackness_percent)
      eval ${1##*-}=$2
      shift 2
      ;;
    -*|--*=) # unsupported flags
      echo "Error: Unsupported flag $1" >&2
      exit 1
      ;;
  esac
done

# Create results folder
results_folder=$frame_basedir/$(basename $video)
mkdir -p $results_folder
echo "Extracting frames into folder $results_folder ..."
frame_prefix=$results_folder/$frame_prefix

# First get rid of too dark frames. At least (100-blackness_percent)% of pixels should
# be above the luminescence_threshold
# Then sample fps frames per second.
# mpdecimate gets rid of repeated frames (the ones do not change too much)
# scale resizes the frames to frame_width while preserving aspect ratio
# showinfo gets the info to map frame number to frame time inside video
# Finally frame files are renamed to have their time in their name
ffmpeg -i $video -vsync 2 \
  -vf "blackframe=amount=0:threshold=$luminescence_threshold, \
    metadata=select:key='lavfi.blackframe.pblack':value=$blackness_percent:function=less, \
    fps=$fps, mpdecimate, scale=$frame_width:-1, showinfo" \
  $frame_prefix%d.$frame_type 2>&1 \
| grep "showinfo.*] n:" \
| sed -E 's/.*] n:[ ]*([^ ]*).*pts_time:([^ ]*).*/\1 \2/' \
| while read frame_number frame_time; do
    rename="mv $frame_prefix$((frame_number+1)).$frame_type $frame_prefix$frame_time.secs.$frame_type"
    echo $rename
    $rename
  done

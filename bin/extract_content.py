#!/usr/bin/env python
import sys
import json
import glob
import boto3
from concurrent import futures

# This script extracts the content from a series of images / frames
# Provide the image files as arguments. Valid arguments:
#    frame1.jpg
#    *.jpg
#    frame1.jpg frame2.jpg *.png
#    some/folder/*.jpg
#
# The output is sent to stdout as a json that has a list of content items
# found in the images/frames
#
# The script uses AWS rekognition to detect labels, text and celebrity faces


MIN_CONFIDENCE = 75
rekognition=boto3.client('rekognition')

def extract_video_content(imageFilename):
  "Extracts the video content of a specific image file"

  with open(imageFilename, 'rb') as imageFile:
    image = {'Bytes': imageFile.read()}

    return (
      get_labels(image, imageFilename) +
      get_texts(image, imageFilename) +
      get_celebrities(image, imageFilename)
    )

def get_labels(image, filename):
  labels = rekognition.detect_labels(
      Image=image, MinConfidence=MIN_CONFIDENCE)['Labels']

  return [
    build_record(
      label['Name'],
      'Label',
      filename,
      label['Confidence'],
      [
        instance['BoundingBox']
        for instance in label['Instances'] if instance['Confidence'] > MIN_CONFIDENCE
      ]
    )
    for label in labels if label['Confidence'] > MIN_CONFIDENCE
  ]

def get_texts(image, filename):
  texts = rekognition.detect_text(Image=image)['TextDetections']

  return [
    build_record(
      text['DetectedText'],
      'Text',
      filename,
      text['Confidence'],
      [
        text['Geometry']['BoundingBox']
      ]
    )
    for text in texts
      if text['Confidence'] > MIN_CONFIDENCE and text['Type'] == 'WORD'
  ]  

def get_celebrities(image, filename):
  celebrities = rekognition.recognize_celebrities(Image=image)['CelebrityFaces']

  return [
    build_record(
      celebrity['Name'],
      'Celebrity',
      filename,
      celebrity['MatchConfidence'],
      [
        celebrity['Face']['BoundingBox']
      ]
    )
    for celebrity in celebrities if celebrity['MatchConfidence'] > MIN_CONFIDENCE
  ]

def build_record(term=None, category=None, source=None, confidence=0, boundingBoxes=[]):
  return {
    'Term': term,
    'Category': category,
    'Source': source,
    'Confidence': confidence,
    'BoundingBoxes': boundingBoxes
  }

if __name__ == "__main__":
  if(len(sys.argv) < 2):
    print('Please pass the file(s) to be processed as arguments')
    sys.exit()

  content_list = []
  jobs = []

  # This submits jobs to extract video content in parallel.
  # Results are merged as the jobs complete
  with futures.ThreadPoolExecutor(max_workers=1000) as executor:
    for path in sys.argv[1:]:
      for filename in glob.glob(path):
        jobs.append(executor.submit(extract_video_content, filename))

    for job in futures.as_completed(jobs):
      content_list += job.result()

  content = {
    'VideoContent': content_list
  }

  print(json.dumps(content))

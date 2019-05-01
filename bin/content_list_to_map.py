#!/usr/bin/env python
import json, sys

def list_to_map(items):
  map = {}

  for item in items:
    term = item['Term']
    category = item['Category']

    if not term in map:
      map[term] = {}

    if not category in map[term]:
      map[term][category] = []

    map[term][category].append(item)

  return map


if __name__ == "__main__":
  content_list = json.load(sys.stdin)['VideoContent']

  print(json.dumps(list_to_map(content_list)))

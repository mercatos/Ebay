#!/usr/bin/env python
import fetch_item
import yaml


def test_fetch_item():
  item = fetch_item.fetch_item('v1|110198777511|410084241125')
  print('\033[32m'
        'test_fetch_item'
        '\033[33m')
  print(yaml.dump(item))
  print('\033[0m')


if __name__ == '__main__':
  test_fetch_item()

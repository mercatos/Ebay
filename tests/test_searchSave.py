#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, re, sys
import mock, unittest, mockfs, pickle

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import searchSave



class SearchSaveTestCase(unittest.TestCase):
  def setUp(self):
    folder = os.path.dirname(os.path.realpath(__file__))
    self.get_data = []
    with open(f'{folder}/data/data.post.credentials', 'rb') as f:
      self.get_data.append(pickle.load(f))

    for pos in range(7):
      with open(f'{folder}/data/data.get{pos}', 'rb') as f:
        self.get_data.append(pickle.load(f))

    file = open(f'{folder}/data/test.data.xml', mode='r')
    xml_input = file.read()
    file.close()
    file = open(f'{folder}/data/test.data.output.xml', mode='r')
    self.expected_output = file.read()
    file.close()

    self.mfs = mockfs.replace_builtins()
    self.mfs.add_entries({'/tmp/sample.file.xml': xml_input})

  def tearDown(self):
    mockfs.restore_builtins()

  @mock.patch('getCredentials.requests.post')
  @mock.patch('searchItem.requests.get')
  def test_searchSave(self, mock_getCredentials_requests, mock_searchItem_requests):
    file = open('/tmp/sample.file.xml', 'r+')
    mock_getCredentials_requests.side_effect = self.get_data
    mock_searchItem_requests.side_effect = self.get_data
    searchSave.processDatabase(file)

    file = open('/tmp/sample.file.output.xml', 'r')

    output = re.sub("\<FoundDate>.*", '', file.read().strip())
    expected_output = re.sub("\<FoundDate>.*", '', self.expected_output.strip())

    #Consider XML canonicalization in future
    output = re.sub("(\s|\u180B|\u200B|\u200C|\u200D|\u2060|\uFEFF)+", '', output)
    expected_output = re.sub("(\s|\u180B|\u200B|\u200C|\u200D|\u2060|\uFEFF)+", '', expected_output)

    self.assertEqual.__self__.maxDiff = None
    self.assertEqual(output, expected_output)


if __name__ == '__main__':
  unittest.main()

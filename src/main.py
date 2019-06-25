import os
import json
from HTMLParser import HTMLParser

class JsonReader(object):
    def __init__(self, json_path):
        self.json_path = json_path

    def get_json_data(self):
        data = dict()
        with open(self.json_path, 'r') as json_file:
            data = json.loads(json_file.read())
        return data


if __name__== "__main__":

    curr_path = os.path.dirname(os.path.realpath(__file__))

    #HTML TEMPLATE
    htmlFilePath = os.path.join(curr_path, 'sample.html')
    with open(htmlFilePath, 'r') as content_file:
        content = content_file.read()

    #JSON DATA
    json_reader = JsonReader(os.path.join(curr_path, 'sample.json'))   
    dbData = json_reader.get_json_data()

    outputHTML = HTMLParser(content,dbData).generateHTML()

    print(outputHTML)
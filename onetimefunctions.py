import re
import os
import xmltodict
import json
import feedparser
import requests
# import g4f
from bs4 import BeautifulSoup
import json
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from datetime import datetime
from main import get_feeds
from main import delete_entries_older_than_input_date

def replace_and_delete(file_path):
    with open(file_path, 'r+') as file:
        content = file.read()
        content = re.sub(
            r'<rss.*?>', '<rss xmlns:media="http://search.yahoo.com/mrss/" version="2.0">', content, flags=re.DOTALL)
        content = re.sub(r'<ns0.*?/>', '', content, flags=re.DOTALL)
        content = re.sub(r'<ns1.*?/>', '', content, flags=re.DOTALL)
        content = re.sub(r"</ai_summary>(.*?)</item>",
                         r'</ai_summary><media:thumbnail></media:thumbnail><media:content></media:content></item>', content, flags=re.DOTALL)
        file.seek(0)
        file.write(content)
        file.truncate()


def replace_and_delete_in_feeds():

    folder_path = 'feeds'  # Replace with the actual path to your folder

    for filename in os.listdir(folder_path):
        if filename.endswith('.xml'):  # Filter the files to process only XML files
            file_path = os.path.join(folder_path, filename)
            replace_and_delete(file_path)


def convert_xml_to_json(xml_file_path):

    # Check if the XML file exists
    if not os.path.isfile(xml_file_path):
        raise FileNotFoundError(f"XML file not found: {xml_file_path}")

    # Read the XML file
    with open(xml_file_path, "r") as xml_file:
        xml_data = xml_file.read()

    # Convert XML to dictionary
    data_dict = xmltodict.parse(xml_data)

    # Convert dictionary to JSON
    json_data = json.dumps(data_dict)

    # Create the JSON file path
    json_file_path = os.path.splitext(xml_file_path)[0] + ".json"

    # Write the JSON data to the file
    with open(json_file_path, "w") as json_file:
        json_file.write(json_data)

    print(f"JSON file created: {json_file_path}")


def convert_json_to_xml(json_file_path):
    # Check if the JSON file exists
    if not os.path.isfile(json_file_path):
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")

    # Read the JSON file
    with open(json_file_path, "r") as json_file:
        json_data = json_file.read()

    # Convert JSON to dictionary
    data_dict = json.loads(json_data)

    # Convert dictionary to XML
    xml_data = xmltodict.unparse(data_dict, pretty=True)

    # Create the XML file path
    xml_file_path = os.path.splitext(json_file_path)[0] + ".xml"

    # Write the XML data to the file
    with open(xml_file_path, "w") as xml_file:
        xml_file.write(xml_data)

    print(f"XML file created: {xml_file_path}")


def add_urls_to_item(json_data, link, thumbnail_url, content_url):
    for item in json_data['rss']['channel']['item']:
        if item['link'] == link:
            item["media:thumbnail"] = {"@url": thumbnail_url}
            item["media:content"] = {"@url": content_url, "@medium": "image"}
            break
    return json.dumps(json_data, indent=2)


# convert_xml_to_json("feeds/test.xml")
# convert_json_to_xml("feeds/Column_TH_1.json")


def convert_json_data_to_xml(json_file_path):
    # Check if the JSON file exists
    if not os.path.isfile(json_file_path):
        raise FileNotFoundError(f"JSON file not found: {json_file_path}")

    # Read the JSON file
    with open(json_file_path, "r") as json_file:
        json_data = json_file.read()

    # Convert JSON to dictionary
    data_dict = json.loads(json_data)

    # Convert dictionary to XML
    xml_data = xmltodict.unparse(data_dict, pretty=True)

    # Create the XML file path
    xml_file_path = os.path.splitext(json_file_path)[0] + ".xml"

    # Write the XML data to the file
    with open(xml_file_path, "w") as xml_file:
        xml_file.write(xml_data)

    print(f"XML file created: {xml_file_path}")


# replace_and_delete_in_feeds()


feeds = get_feeds()
for feed in feeds:
    delete_entries_older_than_input_date  (feed , '08/01/2024')
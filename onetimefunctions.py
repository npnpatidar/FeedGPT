import re
import os
import xmltodict
import json
import os

def replace_and_delete(file_path):
    with open(file_path, 'r+') as file:
        content = file.read()
        content = re.sub(r'<rss.*?>', '<rss xmlns:media="http://search.yahoo.com/mrss/" version="2.0">', content, flags=re.DOTALL)
        content = re.sub(r'<ns0.*?/>', '', content, flags=re.DOTALL)
        content = re.sub(r'<ns1.*?/>', '', content, flags=re.DOTALL)
        content = re.sub(r'</ai_summary>', r'</ai_summary><media:thumbnail></media:thumbnail><media:content></media:content>', content, flags=re.DOTALL)
        file.seek(0)
        file.write(content)
        file.truncate()

def replace_and_delete_in_feeds():

    folder_path = 'feeds'  # Replace with the actual path to your folder

    for filename in os.listdir(folder_path):
        if filename.endswith('.xml'):  # Filter the files to process only XML files
            file_path = os.path.join(folder_path, filename)
            replace_and_delete(file_path)

def update_media_url_in_all_feeds(feed):

    default_media_url = ''
    feed_url = feed['url']
    feed_file = feed['feed_filename']
    try:
        print(f"fetching {feed_url}")
        feed_response = feedparser.parse(feed_url)

        if feed_response['status'] != 200 and feed_response['status'] != 301:
            print(f"Check url : {feed_url}")
            return
        if 'entries' not in feed_response or len(feed_response['entries']) == 0:
            print(f"No entries found")
            return
        else:
            number_of_entries = len(feed_response['entries'])
            print(f"Found {number_of_entries} entries ")

    except Exception as e:
        print(f"Error fetching {feed_url}: {str(e)}")

    tree = ET.parse(feed_file)
    root = tree.getroot()
    items = root.findall(".//item")

    for entry in feed_response.entries:
      
        link = entry.link
       
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            media_url = entry.media_thumbnail[0]['url']
        elif hasattr(entry, "media_content") and entry.media_content:
            media_url = entry.media_content[0]['url']

        for item in items:
            item_link = item.find("link").text
            if item_link == link:

                media_thumbnail_element = item.find(
                    ".//media:thumbnail", namespaces={'media': 'http://search.yahoo.com/mrss/'})
             
                media_thumbnail_element.set("url", media_url)

                media_content_element = item.find(
                    ".//media:content", namespaces={'media': 'http://search.yahoo.com/mrss/'})
                media_content_element.set("url", media_url)
                media_content_element.set("medium", "image")

        # Save the updated XML
        tree.write(feed_file, encoding="utf-8")

    print("XML item updated or added successfully.")

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




convert_xml_to_json("feeds/alt.xml")
# convert_json_to_xml("feeds/Explained_IE_1.json")





import re
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

replace_and_delete_in_feeds()
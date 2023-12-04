import feedparser
import requests
import g4f
from bs4 import BeautifulSoup
import os
import json
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from datetime import datetime
import time
import xmltodict


def fetch_article_text(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # Customize this part based on the specific structure of the webpage
        article_text = ''
        # Example: Extracting text from <p> tags
        paragraphs = soup.find_all('p')
        for paragraph in paragraphs:
            article_text += paragraph.get_text() + '\n'
        return article_text
    except Exception as e:
        print(f"Couldn't fetch article text: {str(e)}")
        return None


def summarise(article_text):
    max_attempts = 1
    summary = ""
    # Define your conversation with the model
    conversation = [
        {
            "role":
            "system",
            "content":
            "You are a helpful assistant that summarizes articles. Now summarize this article:" + article_text
        },
    ]

    for _ in range(max_attempts):
        try:
            response = g4f.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=conversation,
                max_tokens=1000,
                stream=False,
            )

            for message in response:
                summary += message

            # Split the response into words and check if it has more than 5 words
            words = summary.split()
            if len(words) > 80:
                return summary

        except Exception as e:
            # Log the error (you can use a logging library for this)
            # print(f"Error while summarizing article text: {str(e)}")
            print(f"error in summarising  ")

    # If after 10 attempts there's no valid response, return an error message or handle as needed
    return None


def get_feeds():
    feeds = []

    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    opml_file = config.get("opml_file", "feeds.opml")
    markdown_dir = config.get("markdown_dir", "markdown_files")
    feed_dir = config.get("feed_dir", "feeds")

    if not os.path.exists(markdown_dir):
        os.makedirs(markdown_dir)

    if not os.path.exists(feed_dir):
        os.makedirs(feed_dir)

    with open(opml_file, 'r') as file:
        soup = BeautifulSoup(file, 'xml')
        outlines = soup.find_all('outline')

        for outline in outlines:
            if 'xmlUrl' in outline.attrs:
                feed_title = outline['title']
                feed_url = outline['xmlUrl']
                markdown_filename = os.path.join(
                    markdown_dir, feed_title.replace(' ', '_') + ".md")
                feed_filename = os.path.join(
                    feed_dir, feed_title.replace(' ', '_') + ".xml")

                feeds.append({'title': feed_title, 'url': feed_url,
                             'markdown_filename': markdown_filename, 'feed_filename': feed_filename})

    return feeds


def write_index_log_files(feeds):

    if feeds:
        with open(f"index.md", "w") as index_file:
            for feed in feeds:
                markdown_filename = feed['markdown_filename']
                feed_filename = feed['feed_filename']
                entry_in_index = f"- [{feed['title']}]({markdown_filename})\n"
                index_file.write(entry_in_index)

               # Create a separate Markdown file for each feed if it doesn't exist
                if not os.path.exists(markdown_filename):
                    open(markdown_filename, "w").close()
                    print(f"Markdown file created: {markdown_filename}")
                    log_details(f"Markdown file created: {markdown_filename}")

                if not os.path.exists(feed_filename):
                    # Create an RSS feed XML document
                    rss_xml = generate_base_xml(feed)
                    # Save the properly formatted RSS XML to the specified XML file
                    with open(feed_filename, 'w', encoding='utf-8') as rss_file:
                        rss_file.write(rss_xml)

                    print(f"Feed file created: {feed['feed_filename']}")
                    log_details(f"Feed file created: {feed['feed_filename']}")


def extract_feed_url():
    # Extract the repository name and feed directory and construct the URL
    with open('config.json', 'r') as config_file:
        config_json = json.load(config_file)
    github_repo = config_json.get("github_repo")
    feed_dir = config_json.get("feed_dir")

    if github_repo:
        repo_parts = github_repo.split('/')
        if len(repo_parts) == 2:
            user, repo_name = repo_parts
            feed_url = f"https://{user}.github.com/{repo_name}/{feed_dir}/"
            return feed_url
        else:
            return "Invalid repository format in config.json"
    else:
        return "The 'github_repo' key is not found in config.json"


def generate_base_xml(feed):
    # Create an RSS feed XML document
    rss_feed = ET.Element(
        "rss", attrib={"version": "2.0", "xmlns:media": "http://search.yahoo.com/mrss/"})
    # rss_feed = ET.Element("rss", version="2.0", xmlns={"media": "http://search.yahoo.com/mrss/"})
    channel = ET.SubElement(rss_feed, "channel")
    # Define RSS channel elements
    title = ET.SubElement(channel, "title")
    title.text = feed["title"]

    link = ET.SubElement(channel, "link")
    link.text = extract_feed_url() + \
        feed["title"].replace(' ', '_') + f".xml"

    description = ET.SubElement(channel, "description")
    description.text = feed["title"]

    # Create a string representation of the XML document without pretty formatting
    rss_xml = ET.tostring(rss_feed, encoding="utf-8").decode("utf-8")

    return rss_xml


def update_media_url_in_feed(feed):

    feed_url = feed['url']
    feed_file = feed['feed_filename']

    json_feed = get_json_data_from_xml(feed_file)

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

    for entry in feed_response.entries:
        link = entry.link
        media_url = None

        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            media_url = entry.media_thumbnail[0]['url']
        elif hasattr(entry, "media_content") and entry.media_content:
            media_url = entry.media_content[0]['url']
        try:
            items = json_feed['rss']['channel']['item']
        except:
            continue

        for i, item in enumerate(items):
            if item['link'] == link and media_url is not None:
                item["media:thumbnail"] = {"@url": media_url}
                item["media:content"] = {"@url": media_url, "@medium": "image"}
                break
    write_json_data_to_xml(json_feed, feed_file)


def get_json_data_from_xml(xml_file_path):
    if os.path.exists(xml_file_path):
        with open(xml_file_path, "r") as xml_file:
            xml_data = xml_file.read()

        data_dict = xmltodict.parse(xml_data)

        json_data = json.dumps(data_dict)
        json_feed = json.loads(json_data)

        return json_feed
    else:
        return None


def write_json_data_to_xml(json_data, xml_file_path):
    xml_data = xmltodict.unparse(json_data, pretty=True)

    with open(xml_file_path, "w") as xml_file:
        xml_file.write(xml_data)


def fetch_and_write_feed_to_markdown_using_json(feed):

    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    github_repo = config.get("github_repo")

    # Parse the feed
    feed_url = feed['url']
    feed_file = feed['feed_filename']
    json_data = get_json_data_from_xml(feed_file)

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

    existing_links = set()
    if 'item' in json_data['rss']['channel']:
        items = json_data['rss']['channel']['item']
        if isinstance(items, list):
            existing_links = set(item['link'] for item in items)

    new_entry = 0
    for entry in feed_response.entries:
        title = entry.title
        link = entry.link
        pub_date = entry.published
        description = entry.summary
        ai_summary = "False"
        media_url = ''
        got_summary = None
        summary = entry.summary

        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            media_url = entry.media_thumbnail[0]['url']
        elif hasattr(entry, "media_content") and entry.media_content:
            media_url = entry.media_content[0]['url']

        if link in existing_links:
            print(f"Already exist so Skipping")
            continue

        print(f"Fetching {title}")
        article_text = fetch_article_text(link)

        if article_text is None:
            print("No Article text")
            summary = "No Article text \n" + entry.summary
        else:
            print(f"Summarizing")
            got_summary = summarise(article_text)

            if got_summary is None:
                print("Got Article Text but No Summary ")
                summary = "Article found but Couldn't summarize \n" + entry.summary
            else:
                ai_summary = "True"
                summary = got_summary

        item_data = {
            "title": title,
            "link": link,
            "description": summary,
            "pubDate": pub_date,
            "ai_summary": ai_summary,
            "media:thumbnail": {
                "@url": media_url
            },
            "media:content": {
                "@url": media_url,
                "@medium": "image"
            }
        }
        new_entry += 1
        if 'item' in json_data['rss']['channel']:
            items = json_data['rss']['channel']['item']
            if isinstance(items, list):
                items.append(item_data)
            else:
                json_data['rss']['channel']['item'] = [item_data]
        else:
            json_data['rss']['channel']['item'] = [item_data]

        existing_links.add(link)
    write_json_data_to_xml(json_data, feed_file)
    print(f"{new_entry} Feed entries have been written to {feed_file}")
    if new_entry > 0:
        log_details(
            f"{new_entry} Feed entries have been written to {feed_file}")
    return new_entry


def update_summary_if_ai_summary_is_false(feed):

    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
    github_repo = config.get("github_repo")

    feed_url = feed['url']
    feed_file = feed['feed_filename']
    json_data = get_json_data_from_xml(feed_file)

    new_summary = 0

    for item in json_data['rss']['channel']['item']:
        if 'ai_summary' in item and item['ai_summary'].lower() == 'false':
            title = item['title']
            link = item['link']
            summary = item['description']

            print(f"Fetching {title}")
            article_text = fetch_article_text(link)
            got_summary = None

            if article_text is None:
                print("No Article text")
            else:
                print(f"Summarizing")
                got_summary = summarise(article_text)

                if got_summary is None:
                    print("Got Article Text but No Summary ")
                else:
                    new_summary += 1
                    summary = got_summary
                    item['ai_summary'] = 'True'
            item['description'] = summary

    write_json_data_to_xml(json_data, feed_file)
    print(f"{new_summary} summaries have been updated to {feed_file}")
    if new_summary > 0:
        log_details(
            f"{new_summary} summaries have been updated to {feed_file}")
    return new_summary


def sorting_xml_files_by_date_json(feed):
    feed_file = feed['feed_filename']
    json_data = get_json_data_from_xml(feed_file)

    items = json_data['rss']['channel']['item']
    sorted_items = sorted(
        items, key=lambda x: parse_date(x["pubDate"]), reverse=True)
    json_data["rss"]["channel"]["item"] = sorted_items

    write_json_data_to_xml(json_data, feed_file)


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        try:
            # Handle the alternative format if the first one fails
            return datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT")
        except ValueError:
            # If both formats fail, return the original string
            return date_str


def write_markdown_files_json(feed):
    feed_file = feed['feed_filename']
    json_data = get_json_data_from_xml(feed_file)
    markdown_file = feed['markdown_filename']

    items = json_data['rss']['channel']['item']
    with open(markdown_file, "w", encoding="utf-8") as md_file:
        for item in items:
            title = item['title']
            link = item['link']
            description = item['description']
            pubDate = item['pubDate']

            md_file.write(f"{pubDate}\n")
            md_file.write(f"### [{title}]({link})\n\n")
            md_file.write(f"{description}\n\n")
    print(f"Markdown file updated: {markdown_file}")


def delete_entries_older_than_input_date(feed, last_date):

    feed_file = feed['feed_filename']
    json_data = get_json_data_from_xml(feed_file)
    items = json_data['rss']['channel']['item']
    last_date = datetime.strptime(last_date, '%m/%d/%Y').replace(tzinfo=None)
    filtered_items = [item for item in items if datetime.strptime(
        item['pubDate'], "%a, %d %b %Y %H:%M:%S %z").replace(tzinfo=None) > last_date]
    json_data['rss']['channel']['item'] = filtered_items
    write_json_data_to_xml(json_data, feed_file)
    log_details(
        f"{len(items) - len(filtered_items)} entries have been deleted from {feed_file} \n")


# function to create log files and write input text into them
def log_details(details):

    if not os.path.exists('log.txt'):
        open('log.txt', 'w').close()

    with open('log.txt', 'a') as log_file:
        log_file.write(details + "\n")


def main():
    start_time = time.time()

    log_details("Started at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    feeds = get_feeds()

    write_index_log_files(feeds)

    new_entries_added = 0
    for feed in feeds:
        new = fetch_and_write_feed_to_markdown_using_json(feed)
        new_entries_added = new_entries_added + new

    log_details(f"{new_entries_added} new entries have been added")

    # new_entries_updated = 0
    # for feed in feeds:
    #     new_summary = update_summary_if_ai_summary_is_false(feed)
    #     new_entries_updated = new_entries_updated + new_summary

    # log_details(f"{new_entries_updated} summaries have been updated")

    for feed in feeds:
        sorting_xml_files_by_date_json(feed)
        write_markdown_files_json(feed)
        # update_media_url_in_feed(feed)
        # delete_entries_older_than_input_date(feed , '10/10/2022')
   

    end_time = time.time()

    total_time = end_time - start_time

    minutes , seconds = divmod(total_time, 60)

    log_details(f"Finished at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log_details(f"Total time taken: {total_time} seconds")

    log_details("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

    # write number of new entries and added and updated to index.md at bottom
    with open('index.md', 'a') as index_file:
        index_file.write(f"\n\n\n ************************************************* \n")
        index_file.write(f"Total number of new entries: {new_entries_added}\n")
        # index_file.write(
            # f"Total number of summaries updated: {new_entries_updated}\n")
        index_file.write(
            f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        index_file.write(f"Total time taken: {minutes} minutes {seconds} seconds\n")


if __name__ == "__main__":
    main()

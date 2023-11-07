import feedparser
import requests
import g4f
from bs4 import BeautifulSoup
import os
import json
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from datetime import datetime


def fetch_and_write_feed_to_markdown(feed):
    # Parse the feed
    markdown_file = feed['markdown_filename']
    # log_file = feed['log_filename']
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

    # Read existing entry IDs from the XML file
    existing_links = set()
    if os.path.exists(feed_file):
        tree = ET.parse(feed_file)
        root = tree.getroot()
        for item in root.findall(".//item"):
            existing_links.add(item.find("link").text)

    for entry in feed_response.entries:
        title = entry.title
        link = entry.link
        pub_date = entry.published
        description = entry.summary
        ai_summary = "False"
        # media_url = entry.media_thumbnail[0]['url']
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            media_url = entry.media_thumbnail[0]['url']
        else:
            media_url = "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"


        # Check if the entry's ID already exists in the set of existing IDs
        if link in existing_links:
            print(f"Already exist so Skipping {id}")
            # Skip processing this entry and continue with the next one
            continue

        print(f"Fetching {title}")
        article_text = fetch_article_text(link)
        if article_text is None:
            print("No article text so skipping")
            continue

        print(f"Summarizing")
        summary = summarise(article_text)

        if summary is None:
            print("No summary so skipping")
            title = "Not Summary - " + title
            
            # continue
        else:
            ai_summary = "True"
            with open(markdown_file, "a", encoding="utf-8") as md_file:
                md_file.write(f"### [{title}]({link})\n\n")
                md_file.write(f"{summary}\n\n")
            print(f"Feed entries have been written to {markdown_file}")
            # Add the new entry to the XML file
        add_rss_item_to_xml(feed['feed_filename'],
                            title, link, summary, pub_date, ai_summary , media_url) 

       

        existing_links.add(link)  # Add the new entry's ID to the set

    

# Define a function to fetch the article text


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

# Define a function to summarize the article


def summarise(article_text):
    max_attempts = 3
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
            print(f"Error while summarizing article text: {str(e)}")

    # If after 10 attempts there's no valid response, return an error message or handle as needed
    return None

# make index file, create log files


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

                if not os.path.exists(feed_filename):
                    # Create an RSS feed XML document
                    rss_xml = generate_base_xml(feed)
                    # Save the properly formatted RSS XML to the specified XML file
                    with open(feed_filename, 'w', encoding='utf-8') as rss_file:
                        rss_file.write(rss_xml)

                    print(f"Feed file created: {feed['feed_filename']}")


def sorting_and_writing_markdown_files(feed):
    try:
        # Parse the XML file
        tree = ET.parse(feed['feed_filename'])
        root = tree.getroot()

        # Get a list of item elements
        items = root.findall(".//item")

        # Define a function to convert date strings to a sortable format
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

        # Sort the item elements based on pubDate in reverse order (latest first)
        items.sort(key=lambda item: parse_date(
            item.find("pubDate").text), reverse=True)

        # Create a string representation of the XML document
        sorted_xml = parseString(ET.tostring(
            root, encoding="utf-8")).toprettyxml(indent="    ")

        # Write the sorted items to the markdown file
        with open(feed['markdown_filename'], "w", encoding="utf-8") as markdown_file:
            for item in items:
                title = item.find("title").text
                link = item.find("link").text
                description = item.find("description").text
                pubDate = item.find("pubDate").text

                markdown_file.write(f"{pubDate}\n")
                markdown_file.write(f"### [{title}]({link})\n\n")
                markdown_file.write(f"{description}\n\n")

        print(
            f"Items sorted by pulication date and written to {feed['markdown_filename']}.")

    except Exception as e:
        print(f"Error: {str(e)}")


def add_rss_item_to_xml(xml_file_path, title, link, description, pubDate, ai_summary , media_url):
    try:
        # Load the existing XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        if not any(attr.startswith("xmlns:media") for attr in root.attrib):
            root.set("xmlns:media", "http://search.yahoo.com/mrss/")


        # Create a new item element
        new_item = ET.Element("item")

        title_element = ET.SubElement(new_item, "title")
        title_element.text = title

        link_element = ET.SubElement(new_item, "link")
        link_element.text = link

        description_element = ET.SubElement(new_item, "description")
        description_element.text = description

        pubDate_element = ET.SubElement(new_item, "pubDate")
        pubDate_element.text = pubDate

        ai_summary_element = ET.SubElement(new_item, "ai_summary")
        ai_summary_element.text = ai_summary

        media_thumbnail_element = ET.SubElement(new_item,"media:thumbnail")
        media_thumbnail_element.set("url", media_url)

        media_content_element = ET.SubElement(new_item,"media:content")
        media_content_element.set("url", media_url)
        media_content_element.set("medium", "image")

        # Append the new item to the root channel element
        channel = root.find("channel")
        channel.append(new_item)

        with open(xml_file_path, "w", encoding="utf-8") as xml_file:
            xml_file.write(ET.tostring(root, encoding="utf-8").decode())

        print("New RSS item added successfully.")

    except Exception as e:
        print(f"Error adding RSS item: {str(e)}")


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
    rss_feed = ET.Element("rss", version="2.0")
    rss_feed.set("xmlns:media", "http://search.yahoo.com/mrss/")
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


def update_xml_item(xml_file_path, title, link, description, pubDate, ai_summary, media_url):
    try:
        # Load the existing XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        items = root.findall(".//item")

        # Check if an item with the same link already exists
        existing_item = None
        for item in items:
            item_link = item.find("link").text
            if item_link == link:
                existing_item = item
                break

        if existing_item is not None:
            # Update the existing item with the provided data
            title_element = existing_item.find("title")
            title_element.text = title

            description_element = existing_item.find("description")
            description_element.text = description

            pubDate_element = existing_item.find("pubDate")
            pubDate_element.text = pubDate

            ai_summary_element = existing_item.find("ai_summary")
            ai_summary_element.text = ai_summary

            # Update elements with namespaces
            media_thumbnail_element = existing_item.find(".//ns0:thumbnail", namespaces={'ns0': 'http://search.yahoo.com/mrss/'})
            media_thumbnail_element.set("url", media_url)

            media_content_element = existing_item.find(".//ns0:content", namespaces={'ns0': 'http://search.yahoo.com/mrss/'})
            media_content_element.set("url", media_url)
            media_content_element.set("medium", "image")

        else:
            # Create a new item element
            new_item = ET.Element("item")

            title_element = ET.SubElement(new_item, "title")
            title_element.text = title

            link_element = ET.SubElement(new_item, "link")
            link_element.text = link

            description_element = ET.SubElement(new_item, "description")
            description_element.text = description

            pubDate_element = ET.SubElement(new_item, "pubDate")
            pubDate_element.text = pubDate

            ai_summary_element = ET.SubElement(new_item, "ai_summary")
            ai_summary_element.text = ai_summary

            # Create elements with namespaces
            media_thumbnail_element = ET.SubElement(new_item, "{http://search.yahoo.com/mrss/}thumbnail")
            media_thumbnail_element.set("url", media_url)

            media_content_element = ET.SubElement(new_item, "{http://search.yahoo.com/mrss/}content")
            media_content_element.set("url", media_url)
            media_content_element.set("medium", "image")

            # Append the new item to the root channel element
            channel = root.find("channel")
            channel.append(new_item)

        # Save the updated XML
        tree.write(xml_file_path, encoding="utf-8")

        print("XML item updated or added successfully.")

    except Exception as e:
        print(f"Error updating or adding XML item: {str(e)}")


def update_summaries_in_items_where_ai_summary_is_false(feed):
    feed_url = feed['feed_filename']
    markdown_file = feed['markdown_filename']
    if os.path.exists(feed_url):
        tree = ET.parse(feed_url)
        root = tree.getroot()
        items = root.findall(".//item")
        # if not any(attr.startswith("xmlns:media") for attr in root.attrib):
        #     root.set("xmlns:media", "http://search.yahoo.com/mrss/")
        for item in items:
            ai_summary = item.find("ai_summary").text
            if ai_summary == 'False':
                # if 'ai_summary' in item.attrib and item.attrib['ai_summary'] == 'False':
                title = item.find("title").text
                link = item.find("link").text
                description = item.find("description").text
                pubDate = item.find("pubDate").text
                # ai_summary = item.find("ai_summary").text
                namespace = {'media': 'http://search.yahoo.com/mrss/'}
                media_thumbnail = item.find(".//media:thumbnail", namespaces=namespace)
                media_url = media_thumbnail.attrib['url']
                
                print(f"Fetching {title}")
                article_text = fetch_article_text(link)
                if article_text is None:
                    print("No article text so skipping")
                    continue

                print(f"Summarizing")
                summary = summarise(article_text)

                if summary is None:
                    print("No summary so skipping")
                    # title = "Not Summary -" + title
                    continue
                else:
                    ai_summary = "True"
                    with open(markdown_file, "a", encoding="utf-8") as md_file:
                        md_file.write(f"### [{title}]({link})\n\n")
                        md_file.write(f"{summary}\n\n")
                    print(f"Feed entries have been written to {markdown_file}")
                    # Add the new entry to the XML file
                    update_xml_item(feed_url, title, link, summary, pubDate, ai_summary, media_url)
    return feed


def main():

    feeds = get_feeds()

    write_index_log_files(feeds)

    for feed in feeds:
        fetch_and_write_feed_to_markdown(feed)
    for feed in feeds:
        update_summaries_in_items_where_ai_summary_is_false(feed)
        sorting_and_writing_markdown_files(feed)


if __name__ == "__main__":
    main()

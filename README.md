---
created: 2023-11-07T10:54:02+05:30
modified: 2023-11-07T11:27:30+05:30
---

# README

# FeedGPT: Summarize RSS Feeds with ChatGPT

**What is FeedGPT?**

FeedGPT is a tool designed to simplify your news consumption process. If you subscribe to RSS feeds from various sources and wish to receive summarized versions of lengthy articles via ChatGPT, then FeedGPT is the solution for you.

**Features:**

1. **Feed Input:** FeedGPT takes an OPML file with feed URLs as input.
2. **File Generation:** It generates separate XML and Markdown files for each feed URL.
3. **Article Fetching:** FeedGPT fetches articles from each feed, one by one.
4. **Summarization:** It leverages GPT4Free to provide concise summaries for fetched articles.
5. **Update Files:** The tool updates the summaries in the XML and Markdown files.

**Getting Started:**

1. **Fork the Repository:** Begin by forking this repository to your GitHub account.
2. **Create a Work Token:** Generate a Work Token for your forked repository.
3. **Configure Repository Secrets:** Add your name, email, and the Work Token you created to your repository secrets.
4. **Update Configuration:** Modify the configuration file according to your preferences.
5. **Feed URLs:** Update the OPML file with the RSS feed URLs you wish to subscribe to.
6. **Cron Job:** If needed, make changes to the `cron-job.yml` file to adjust the frequency of synchronization, etc.
7. **Subscribe to Feeds:** Use any feed reader of your choice to subscribe to your news feeds.
8. **Access Summaries:** Download the GitJournal app and subscribe to this repository to access the generated Markdown files as notes.

Enjoy a more efficient way to stay updated with your favorite news sources using FeedGPT!

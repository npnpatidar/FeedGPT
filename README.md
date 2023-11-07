---
created: 2023-11-07T10:54:02+05:30
modified: 2023-11-07T11:15:29+05:30
---

# README

## What is the purpose
If you subscribe to RSS feeds of various newspapers or journals or magazines and you want to get summary of those long articles by chatgpt then this is for you. 

## It does following
1. It takes opml file having feed url as input
2. It creates separate  xml and markdown file for each feed url
3. It fetches all articles in each feed one by one. 
4. It summarises those fetched articles using gpt4free
5. It updates the summary in xml and markdown files 

## How can you use it
1. Fork the repo
2. Create Work_Token for forked repository 
3. In repository secrets add name,  email and work token created
4. Update config file 
5. Update opml file with your feed urls
6. Change cron-job.yml file if you want to change frequency of sync etc
7. Subscribe to your news feeds using any feed reader
8. Download gitjournal app and subscribe to the repository to see markdown files as notes

# discord_scraper
Scrape the username, name and about me section of members of a Discord server


**This code is buggy. It is directionally correct for scraping users in a Discord server but struggles with large servers where lots of members of changing active/inactive status. I am uploading this in case others find it useful and want to use / edit it for their own purposes**

# Setup
Download the script locally

Create a .env file in the same folder with the following variables:
```
DISCORD_EMAIL='your-discord-email'
DISCORD_PASSWORD='your-discord-password'
GUILD_URL='the-url-of-the-guild-to-scrape'
```

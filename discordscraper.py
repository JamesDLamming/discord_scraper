import os
import csv
import ctypes
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from dotenv import load_dotenv
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException, NoSuchElementException

# Constants for preventing sleep
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

# Prevent the system from going to sleep
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
DISCORD_EMAIL = os.getenv('DISCORD_EMAIL')
DISCORD_PASSWORD = os.getenv('DISCORD_PASSWORD')
GUILD_URL = os.getenv('GUILD_URL')

if not all([DISCORD_EMAIL, DISCORD_PASSWORD, GUILD_URL]):
    raise ValueError("One or more environment variables are missing")

# Chrome options to disable pop-ups
chrome_options = webdriver.ChromeOptions()
prefs = {"profile.default_content_setting_values.notifications": 2}  # Disable notifications
chrome_options.add_experimental_option("prefs", prefs)

# Initialize the WebDriver (e.g., ChromeDriver)
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

def close_enter_done_popup():
    try:
        enter_done_popup = driver.find_elements(By.XPATH, '//*[contains(@class, "enterDone")]')
        if enter_done_popup:
            print("Closing enterDone popup")
            actions = ActionChains(driver)
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(2)  # Allow time for the popup to close
    except NoSuchElementException:
        pass  # If the popup is not found, continue

try:
    # Log in to Discord
    driver.get('https://discord.com/login')
    wait.until(EC.presence_of_element_located((By.NAME, 'email'))).send_keys(DISCORD_EMAIL)
    wait.until(EC.presence_of_element_located((By.NAME, 'password'))).send_keys(DISCORD_PASSWORD, Keys.RETURN)

    # Navigate to the server
    time.sleep(10)  # Adjust the sleep time as needed
    driver.get(GUILD_URL)
    time.sleep(10)

    # Click the div with aria-label="Show Member List"
    show_member_list_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[contains(@aria-label, "Show Member List")]')))
    show_member_list_button.click()

    # Wait for the members list to load
    time.sleep(10)  # Adjust the sleep time as needed

    # Initialize ActionChains
    actions = ActionChains(driver)

    # Get guild title
    guildName_element = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "headerContent")]/h2')))
    guildName = guildName_element.text.replace(' ', '_')

    # Find and scroll through all members
    members_data = []

    current_scroll_position = 0

    members_to_skip = 0
    
    processed_members = 0  # Counter for processed members

    while True:
        # Find all members
        members = driver.find_elements(By.XPATH, '//div[contains(@class, "member_") and contains(@class, "container_")]')
        
        # Get the height of a single member element
        if members:
            member_height = members[0].size['height']
            members_per_scroll = len(members)
            scroll_increment = member_height * members_per_scroll
        else:
            break

        for member in members:
            # Skip the first 5 members
            if processed_members < members_to_skip:
                processed_members += 1
                continue

            try:
                actions.move_to_element(member).perform()
                member.click()
                time.sleep(1.25)  # Adjust the sleep time as needed
                # Close any enterDone popups
                close_enter_done_popup()

                name = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "userTag")]'))).text
                userName = wait.until(EC.presence_of_element_located((By.XPATH, '//h1[contains(@class, "nickname_")]'))).text

                # Locate the "About Me" section
                about_me_text = ""
                short_wait = WebDriverWait(driver, 3)  # Set a shorter wait time

                try:
                    about_me_section = short_wait.until(EC.presence_of_element_located((By.XPATH, '//h2[text()="About Me"]/following-sibling::div')))
                    about_me_html = about_me_section.get_attribute('outerHTML')

                    # Parse the HTML with BeautifulSoup
                    soup = BeautifulSoup(about_me_html, 'html.parser')

                    # Extract text and handle emojis and links
                    about_me_text = ""
                    for element in soup.descendants:
                        if element.name == 'img' and element.get('aria-label'):
                            about_me_text += element['aria-label']
                        elif element.name == 'a' and element.get('href'):
                            about_me_text += element.get_text() + " (" + element['href'] + ")"
                        elif element.string:
                            about_me_text += element.string
                    about_me_text = about_me_text.strip()
                except TimeoutException:
                    # No "About Me" section found
                    pass

                members_data.append([name, userName, about_me_text])
                
                # Close the user profile modal
                actions.send_keys(Keys.ESCAPE).perform()
                time.sleep(1)  # Adjust the sleep time as needed

                processed_members += 1  # Increment the processed members counter

            except StaleElementReferenceException:
                print("Encountered a stale element, moving to the next member.")
                continue
        
        # Scroll down by the calculated increment
        current_scroll_position += scroll_increment
        driver.execute_script(f"document.querySelector('div.members__573eb').scrollTop = {current_scroll_position};")
        time.sleep(20)  # Wait for the members list to load

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.querySelector('div.members__573eb').scrollHeight")
        
        if new_height == current_scroll_position:
            break

except WebDriverException as e:
    print(f'An error occurred: {e}')
finally:
    # Export to CSV

    # Get the current date and time
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Create the filename with guild name, date, and time
    filename = f'{guildName}_members_data_{current_datetime}.csv'

    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "UserName", "About Me"])
        writer.writerows(members_data)

    print(f'Data has been written to {filename}')

    # Close the WebDriver
    driver.quit()

    # Allow the system to sleep again
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

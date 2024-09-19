from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# Create a new instance of the Firefox driver
driver = webdriver.Firefox()

# Navigate to google.com
driver.get("https://www.google.com")

# Find the search input element and enter random text
search_input = driver.find_element("name", "q")
search_input.send_keys("random text")

# Submit the search
search_input.send_keys(Keys.RETURN)

# Find the first search result link element and get its href attribute
search_results = driver.find_element('xpath','//div[@class="r"]/a')
first_result_link = search_results[0].get_attribute("href")
print(first_result_link)

# Close the browser
driver.quit()
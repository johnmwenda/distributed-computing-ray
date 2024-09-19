from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

#set chromodriver.exe path
driver = webdriver.Chrome(executable_path="C:\chromedriver.exe")
driver.implicitly_wait(0.5)
#launch URL
driver.get("https://the-internet.herokuapp.com/jqueryui/menu#")
#object of ActionChains
a = ActionChains(driver)
#identify element
m = driver.find_element(By.LINK_TEXT, "Enabled")
#hover over element
a.move_to_element(m).perform()
#identify sub menu element
n = driver.find_element(By.LINK_TEXT, "Back to JQuery UI")
# hover over element and click
a.move_to_element(n).click().perform()
print("Page title: " + driver.title)
#close browser
driver.close()
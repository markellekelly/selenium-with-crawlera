import pandas as pd
import time
from eventlet.timeout import Timeout
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException

def check_for_mult_pages(driver):
	# selenium gets stuck when element is not found, so set a timer
	timeout = Timeout(1, NoSuchElementException)
	next_ = None
	try:
		# check if there is a Next button on the page
		next_ = driver.find_element_by_xpath("//*[text()='Next >']")
	except NoSuchElementException:
		next_ = None
	finally:
		timeout.cancel()
	return next_

def main():
	# set up headless proxy
	headless_proxy = "127.0.0.1:3128"
	proxy = Proxy({
			'proxyType': ProxyType.MANUAL,
			'httpProxy': headless_proxy,
			'ftpProxy' : headless_proxy,
			'sslProxy' : headless_proxy,
			'noProxy'  : ''
	})

	chrome_options = webdriver.ChromeOptions()

	# disable images to speed up the page loading
	prefs = {"profile.managed_default_content_settings.images": 2}
	chrome_options.add_experimental_option("prefs", prefs)

	capabilities = dict(DesiredCapabilities.CHROME)
	proxy.add_to_capabilities(capabilities)

	url = 'https://dhp.virginiainteractive.org/Lookup/Index'

	driver = webdriver.Chrome(executable_path='/Users/markelle/Desktop/chromedriver')

	states = list(pd.read_csv("states.txt", header = None)[0])
	tables = []

	# repeat the full scrape for each state
	for state in states:
		driver.get(url)
		driver.implicitly_wait(10)

		# select the desired occupation and state from dropdowns
		driver.find_element_by_xpath("//select[@id='OccupationId']/option[text()='Licensed Massage Therapist']").click()
		driver.find_element_by_xpath("//select[@id='State']/option[text()='" + state + "']").click()
		driver.find_elements_by_name("submitBtn")[2].click()

		# handle the case when the result page is empty (selenium gets stuck)
		timeout = Timeout(2, NoSuchElementException)
		try:
			rows = [x for x in driver.find_elements_by_tag_name('tr')[2:]]
		except NoSuchElementException:
			rows = []
		finally:
			timeout.cancel()

		# extract the text from each row and add to table
		for row in rows:
			cells = [x.text for x in row.find_elements_by_tag_name('td')]
			tables.append(cells)

		next_ = check_for_mult_pages(driver)

		# continue scraping while there are more pages
		while next_ != None:
			next_.click()
			rows = [x for x in driver.find_elements_by_tag_name('tr')[2:]]
			for row in rows:
				cells = [x.text for x in row.find_elements_by_tag_name('td')]
				tables.append(cells)
			next_ = check_for_mult_pages(driver)

	# export to csv
	pd.DataFrame(tables).to_csv("FULL_data.csv")

if __name__ == "__main__":
	main()

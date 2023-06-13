import re
import os
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from bs4 import BeautifulSoup

requests.packages.urllib3.disable_warnings()

if not os.path.isdir("./data"):
	os.mkdir("./data")

chrome_options = Options()
chrome_options.add_argument("--headless")

def crawlJudge(target, page=10, num=100):
	global driver
	print(target)
	urls = []

	driver = webdriver.Chrome(options=chrome_options)
	driver.get('https://judgment.judicial.gov.tw/FJUD/default.aspx')
	driver.implicitly_wait(3) #隱式等待，最長等待10秒
	element = driver.find_element(By.ID, "txtKW")    
	element.send_keys(target)

	searchBtn = driver.find_element(By.ID, "btnSimpleQry")
	searchBtn.click()
	driver.switch_to.frame("iframe-data")

	for i in range(page):
		soup = BeautifulSoup(driver.page_source, 'lxml')
		results = soup.find("table").find_all("tr")[1:]
		for idx, result in enumerate(results):
			if idx % 2 == 0:
				urls += [result.find_all("td")[1].find("a").get("href")]
		try:
			nextBtn = driver.find_element(By.ID, "hlNext")
			nextBtn.click()
		except:
			break
	results = []
	for url in urls:
		try:
			result = crawlPage(f"https://judgment.judicial.gov.tw/FJUD/{url}", target)
			results += [result]
		except Exception as e:
			print(e)
			continue
		if len(results) >= num:
			return results
	driver.close()
	return results
		
def crawlPage(url, target):
	driver.get(url)
	soup = BeautifulSoup(driver.page_source, 'lxml')

	jud = soup.find(id="jud")
	driver.implicitly_wait(5)
	#WebDriverWait(browser, 10, 0.5).until(EC.presence_of_element_located(locator)) #最長等待10秒，每0.5秒檢查一次條件是否成立
	rows = jud.find_all("div", {"class": "row"})

	# Parser
	judId = rows[0].find("div", {"class": "col-td"}).getText().strip() # 裁判字號
	judDate = rows[1].find("div", {"class": "col-td"}).getText().strip() # 裁判日期
	judReason = rows[2].find("div", {"class": "col-td"}).getText().strip() # 裁判案由
	judMain = rows[3].getText().strip()

	# Related laws
	pkid = re.search(r'&id=(.+)&', driver.current_url).group(1)
	PKID = requests.utils.unquote(pkid)
	url = f"https://judgment.judicial.gov.tw/controls/GetJudRelatedLaw.ashx?pkid={pkid}"
	results = requests.get(url,verify=False).json()
	laws = []
	for result in results['list']:
		law = result['desc'].replace(" ", "").strip()
		law = re.match(r'([^（）\(\)]+)([（\(].+[）\)])?', law).group(1)
		if "、" in law:
			lawIds = re.search(r'([\d\.]+、)+([\d\.]+)', law).group(0)
			for lawId in lawIds.split("、"):
				laws += [law.replace(lawIds, lawId).replace("中華民國", "")]
		else:
			laws += [law]

	print(f"Finish | {judId}")
	# Output
	judDict = {"PKID":PKID, "裁判字號":judId, "裁判日期":judDate, "裁判案由":judReason, "主文":judMain, "相關法條":laws}
	with open(f"./data/{judId}.json", "w", encoding='utf-8') as f:
		json.dump(judDict, f, indent=4, ensure_ascii=False)
	return f"./data/{judId}.json"

if __name__ == '__main__':
	res = crawlJudge("公然侮辱", num=500, page=25)
	print(res)
	print(len(res))
	#res = crawlJudge("公然侮辱", num=10, page=1)
	#print(res)
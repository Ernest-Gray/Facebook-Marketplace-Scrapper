from selenium import webdriver
from time import sleep
from selenium.webdriver.common.by import By
from pymongo import MongoClient
import pandas as pd

class App:
    def __init__(self, email= "", password= "", keyword_search = "", resultLimit=10):
        self.email = email
        self.password = password
        self.keyword_search = keyword_search
        self.resultLimit = resultLimit
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.main_url = "https://www.facebook.com"
        self.client = MongoClient('mongodb://localhost:27017/')
        self.driver.get(self.main_url)
        self.log_in()
        self.used_item_links = []
        self.scrape_items()
        self.driver.quit()
        
    #Logs in
    def log_in(self):
        try:
            email_input = self.driver.find_element(By.ID, 'email')
            email_input.send_keys(self.email)
            sleep(0.5)
            password_input = self.driver.find_element(By.ID, "pass")
            password_input.send_keys(self.password)
            sleep(0.5)
            login_button = self.driver.find_element(By.XPATH, "//*[@type='submit']")
            login_button.click()
            sleep(4)
        except Exception as e:
            print('Some exception occurred while trying to find username or password field')
            
    #Scroll until the bottom of the page to list all the entries
    def ScrollThroughResults(self) -> list[str]:
        results = []
        for i in range(10):
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                sleep(1.25)
            except Exception as e:
                print(e)
                print("Exception scrolling through listings")
                pass
                
        print("Done scrolling down...")
        full_items_list = self.driver.find_element(By.XPATH, "//div[contains(@class, 'bq4')]")
        full_items_list = full_items_list.find_elements(By.XPATH, "//a[contains(@href, 'marketplace/item')]")
        for item in full_items_list:
            value = item.get_attribute('href')
            results.append(value)
        return results
                 
    #Scrapes the urls and scrapes their details
    def scrape_items(self):
        marketplace_button = self.driver.find_element(By.XPATH, '//a[contains(@href, "marketplace")]')
        marketplace_button.click()
        sleep(3)
        
        for keyword in self.keyword_search:
            self.driver.get("https://www.facebook.com/marketplace/107508902612200/search?daysSinceListed=1&deliveryMethod=local_pick_up&query=%s&exact=false" % (keyword))
            sleep(3)
            results = self.ScrollThroughResults()
            print("Found: %s entries..." % (len(results)))
            self.scrape_item_details(results, keyword)
            
    #Gets the details from each link in used_item_urls
    def scrape_item_details(self, used_item_urls, keyword):
        
        titles = []
        descriptions = []
        locations = []
        prices = []
        url_images = []
        postingTimes = []
        urls = []
        
        self.resultLimit = min(self.resultLimit, len(used_item_urls))
        
        for url in used_item_urls[:self.resultLimit]:
            images = []
            self.driver.get(url)
            sleep(1)
            
            url = url
            urls.append(url)
            #Get images
            try:
                image_elements = self.driver.find_elements(By.XPATH,'//img[contains(@class, "dat")]')
                images = [item.get_attribute('src') for item in image_elements]
            except:
                images = ""
                
            #Get Title
            try:
                title = self.driver.find_element(By.XPATH, '//span[contains(@class, "o0t2es00") and @dir="auto" and contains(text(), " ")]').text
                
            except:
                title = "N/A"
            
            #Get Listing Time AND Location
            try:
                timeAndLocation = self.driver.find_element(By.XPATH, '//span[contains(text(), "Listed")]').text
                split = timeAndLocation.split(" in ", 1)
                date_time = split[0]
                location = split[1]
            except:
                date_time = "N/A"
                location = "N/A"
                
            #Get Price
            try:
                price = self.driver.find_element(By.XPATH, '//span[contains(@class, "ekzkrbhg") and contains(@class, "a5q79mjw") and@dir="auto" and contains(text(), "$")]').text
            except:
                price = "N/A"
                
            #Get Description
            try:
                if self.driver.find_element(By.XPATH, "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div[2]/div/div/div/div/div/div[2]/div/div[2]/div/div[1]/div[1]/div[6]/div[2]/div/div[1]/div/span/div/span").is_displayed():
                    self.driver.find_element(By.XPATH, "/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div[2]/div/div/div/div/div/div[2]/div/div[2]/div/div[1]/div[1]/div[6]/div[2]/div/div[1]/div/span/div/span").click()
                description = self.driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/div/div[3]/div/div/div/div[1]/div[1]/div[2]/div/div/div/div/div/div[2]/div/div[2]/div/div[1]/div[1]/div[6]/div[2]/div/div[1]/div/span').text
            except:
                description = "N/A"
            
            print(title[:20], " Price " + price, date_time[:20], location)
            
            #Append the results
            titles.append(title)
            descriptions.append(description)
            prices.append(price)
            locations.append(location)
            url_images.append(images)
            postingTimes.append(date_time)
     
        #Create a pandas dataframe and use it to export a exel spreadsheet
        df = pd.DataFrame({"Title": titles, "URL": urls, "Description": descriptions, "Price":prices,"Location":locations, "Images":url_images, "Posted Time": postingTimes})
        df.to_excel('output\\%s.xlsx' % (keyword), sheet_name='sheet 1', index=True)

#Get config
import json
def read_json(filename: str):
    with open(filename) as f_in:
        return json.load(f_in)
    
if __name__ == '__main__':
    config = read_json("config.json")
    app = App(email=["email"], password=config["password"], resultLimit=25, keyword_search=["exmark mower", "chainsaw", "playstation 5"])
#--------------------------------------------

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import requests
import time

import random
import json

import torch

from model import NeuralNet
from DL import bag_of_words, tokenize

from bs4 import BeautifulSoup
import requests

import subprocess

from datetime import datetime

#--------------------------------------------

chrome_options = Options()

# IMPORTANT!
path_to_directory = '/path/to/directory/' # FILL IN PATH TO WhatsApp_Bot DIRECTORY
chrome_options.add_argument('--user-data-dir=path_to_cookies_directory') # FILL IN PATH TO COOKIES DIRECTORY, BE CAREFUL! USER INFORMATION IS STORED IN THIS DIRECTORY!
admin = 'contacts first name' # FILL IN NAME OF ADMIN USER! PLEASE USE A PASSWORD AS FIRST NAME, NO SECOND NAME, ADMIN PRIVILEGES WILL BE GIVEN!

# all arguments/options
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--headless")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.99 Safari/537.36")
chrome_options.add_argument("--mute-audio")

chromedriver = path_to_directory + 'chromedriver'

#--------------------------------------------

driver = webdriver.Remote("http://ip4:port/wd/hub", options=chrome_options) # USING REMOTE STANDALONE SELENIUM SERVER  

FILE = path_to_directory + 'data.pth'
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

#--------------------------------------------

# starting WhatsApp
driver.get('https://web.whatsapp.com')
print('-')
print('Whatsapp Web Starting..')

#--------------------------------------------

# restart message
def restart():
    messagebox = driver.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')
    messagebox.send_keys('*- Bot Restarting -*\n')
    print('Bot restarting.. Please wait.')
    time.sleep(1)
    driver.quit()
    subprocess.run(path_to_directory + 'restart.sh', shell=True)

# stop message
def stop():
    messagebox = driver.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')
    messagebox.send_keys('*- Bot Stopping -*\n')
    print('Bot received exit command.')
    time.sleep(1)
    driver.quit()
    subprocess.run(path_to_directory + 'stop.sh', shell=True)

#--------------------------------------------

# whatsapp bot
def bot():
    # Bot Started Message
    search_bot = driver.find_element_by_xpath('//span[@title="{}"]'.format('Bot'))

    search_bot.click()

    message_bot = driver.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')

    message_bot.send_keys('*- Bot Started -*\n')
    print('Bot Started')
    print('-')
    driver.find_element_by_xpath('//span[@title="{}"]'.format('Rest Group')).click()

    while True:
        try:
            unread = driver.find_element_by_class_name('ZKn2B')
            sentence = driver.find_element_by_xpath('//*[@id="pane-side"]/div[1]/div/div/div[1]/div/div/div/div[2]/div[2]/div[1]/span//span[@class="_3ko75 _5h6Y_ _3Whw5"]').text
            ac = webdriver.common.action_chains.ActionChains(driver)
            if unread:
                time.sleep(0.5)
                ac.move_to_element_with_offset(unread, 0, -20)
                ac.click().perform()
                ac.click().perform()

                with open(path_to_directory + 'intents.json', 'r') as json_data:
                    intents = json.load(json_data)

                sentence = tokenize(sentence)
                X = bag_of_words(sentence, all_words)
                X = X.reshape(1, X.shape[0])
                X = torch.from_numpy(X).to(device)

                output = model(X)
                _, predicted = torch.max(output, dim=1)
                    
                tag = tags[predicted.item()]

                probs = torch.softmax(output, dim=1)
                prob = probs[0][predicted.item()]
                contact = driver.find_element_by_xpath('//*[@id="pane-side"]/div[1]/div/div/div[1]/div/div/div/div[2]/div[2]/div[1]/span//span[@class="_5h6Y_ _3Whw5"]').text

                if prob.item() > 0.75:
                    for intent in intents['intents']:
                        if tag == intent["tag"]:

                            if tag == "herstart" and contact == admin:
                                print('-')
                                print('-')
                                print('WARNING! ' + contact + ' restarted the bot')
                                restart()
                                break

                            if tag == "stop" and contact == admin:
                                print('-')
                                print('-')
                                print('WARNING! ' + contact + ' stopped the bot')
                                stop()
                                break

                            if tag == "stop" or tag == "herstart" or tag == "kerktijd" and contact != admin:
                                print('-')
                                print('-')
                                print('WARNING! ' + contact + ' used admin commands! Please check!')
                                messagebox = driver.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')
                                messagebox.send_keys('*You are not an admin user.*\n')
                                driver.find_element_by_xpath('//span[@title="{}"]'.format('Rest Group')).click()

                            else:
                                messagebox = driver.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')
                                messagebox.send_keys(f"{random.choice(intent['responses'])}")
                                messagebox.send_keys(Keys.ENTER)
                                driver.find_element_by_xpath('//span[@title="{}"]'.format('Rest Group')).click()

                else:
                    messagebox = driver.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')
                    messagebox.send_keys('Sorry, I do not understand.\n')
                    driver.find_element_by_xpath('//span[@title="{}"]'.format('Rest Group')).click()
        except:
            False

#--------------------------------------------

# check if there is a session or not
while True:
    try: 
        qr = driver.find_element_by_xpath('//*[@id="app"]/div/div/div[2]/div[1]/div/div[2]/div')
        if qr.is_displayed():
            time.sleep(1)
            driver.save_screenshot(path_to_directory + 'QR_CODE.png')
            print('No session found. Please scan QR code screenshot in same directory as script.')
            while True:
                try:
                    interface = driver.find_element_by_xpath('//*[@id="side"]/header')
                    if interface.is_displayed():
                        bot()
                    else:
                        False
                except: 
                    False
    except NoSuchElementException:
        try:
            interface = driver.find_element_by_xpath('//*[@id="side"]/header')
            if interface.is_displayed():
                print('Session found. No need to scan QR code.')
                bot()
            else:
                False
        except NoSuchElementException:
            False

#--------------------------------------------

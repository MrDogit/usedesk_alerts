import time
import requests
from json import load as json_load
from threading import Thread
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
    

# OPTIONS #

url = 'https://secure.usedesk.ru/tickets'

f = open('secrets.json')
json = json_load(f)
f.close()
cookies = json['chrome']
telegram_api_token = json['telegram']['api_token']
telegram_chat_id = json['telegram']['chat_id']

options = Options()
options.add_argument('--ignore-certificate-errors') # try to fix handshake failed
options.add_argument('--ignore-ssl-errors')         # try to fix handshake failed
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--headless=new')

# START #

def telegram_bot_sendtext(bot_message):

   bot_token = telegram_api_token
   bot_chatID = telegram_chat_id
   send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message

   response = requests.get(send_text)

   return response.json()

def telegram_bot_sendtext_and_check(bot_message):
    response = telegram_bot_sendtext(bot_message)
    if not response['ok']:
        alarm('TG response not ok!')
    
driver = webdriver.Chrome(options = options)

driver.get(url)
cookies_driver = dict()
for cookie_name in cookies:
    cookies_driver['name'] = cookie_name
    cookies_driver['value'] = cookies[cookie_name]
    driver.add_cookie(cookies_driver)
driver.get(url)

def get_fresh_count_tickets():
        driver.refresh()
        time.sleep(10)
        try:
            tickets_names = driver.find_elements(By.CLASS_NAME, 'ticket_status')
            count = 0
            for ticket_name in tickets_names:
                if ticket_name.text in {'Новый', 'Открыт'}:
                    count+=1
            return count
        except:
            return None

def use_data(pre_count_tickets, count_tickets):
    if pre_count_tickets < count_tickets:
        string = f'Тикетов стало больше! Количество тикетов: {count_tickets}.'
        telegram_bot_sendtext_and_check(string)
        print(string)
    elif count_tickets == 0 and pre_count_tickets != 0:
        string = f'Можно немного почилить. Тикетов пока нет.'
        telegram_bot_sendtext_and_check(string)
        print(string)
    elif pre_count_tickets > count_tickets:
        string = f'Минус один! Количество тикетов: {count_tickets}.'
        telegram_bot_sendtext_and_check(string)
        print(string)
    elif pre_count_tickets == count_tickets:
        print(count_tickets)
    else:
        print('ERROR: use_data ifelse statements')

def alarm(count_nodata = None):
    print('ALARM!', count_nodata)
    
#search_box = driver.find_element('name', 'q')
#search_box.send_keys('ChromeDriver')
#search_box.submit()

count_tickets = 0
pre_count_tickets = 0
count_nodata = 0
while True:
    count_tickets = get_fresh_count_tickets()
    if count_tickets != None:
        # use_data(count_tickets)
        thread_use_data = Thread(target=use_data, args=(pre_count_tickets, count_tickets,))
        thread_use_data.start()
        count_nodata = 0
        pre_count_tickets = count_tickets
    else:
        count_nodata +=1
        print('NoData')
        if count_nodata > 3:
            alarm(count_nodata)
    
    
    time.sleep(10)
from browsermobproxy import Server
import json
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import os
from flask import Flask
from xvfbwrapper import Xvfb
app = Flask(__name__)
UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



def runner(selenium_file):
    print("reached inside runner")
    print(selenium_file)
    har_arr = {}
    server = Server("./browsermob-proxy-2.1.4/bin/browsermob-proxy")
    print("included proxy")
    server.start()
    proxy = server.create_proxy()
    profile = webdriver.FirefoxProfile()
    display = Xvfb()
    display.start()
    profile.set_proxy(proxy.selenium_proxy())
    driver = webdriver.Firefox(firefox_profile=profile, executable_path='./geckodriver')
    driver.set_page_load_timeout(20)
    print("reached downwards")
    selector_map = {
        "id": "id",
        "xpath": "xpath",
        "name": "name",
        "css": "css selector",
        "class": "class name",
        "tag": "tag name"
    }

    proxy.new_har("google", {"captureHeaders": True, "captureContent": True})
    # with open('test.side') as f:
    print(os.path.join(app.config['UPLOAD_FOLDER'], selenium_file))
    with open(os.path.join(app.config['UPLOAD_FOLDER'], selenium_file)) as f:
        data = json.load(f)
    # data = json.load(selenium_file)
    print("data")
    print(data)
    # directory = data['name']
    # if not os.path.exists(directory):
    #     os.makedirs(directory)
    driver.get(data['url'] + data['tests'][0]['commands'][0]['target'])
    har_data = proxy.har
    if len(har_data['log']['entries']) > 0:
        print(har_data)
        har_arr['launch'] = har_data
        # fo = open("./" + directory + "/launch.har", "w")
        # fo.write(json.dumps(har_data))
        # fo.close()
    for obj in data['tests'][0]['commands']:
        proxy.new_har("google", {"captureHeaders": True, "captureContent": True})
        if obj['command'] == 'click':
            print('click found')
            driver.find_element(selector_map[obj['target'].split('=')[0]], obj['target'].split('=')[1]).click()
            har_data = proxy.har
            if len(har_data['log']['entries']) > 0:
                har_arr[obj['target'].split('=')[1]] = har_data
                # fo = open("./" + directory + "/" + obj['target'].split('=')[1] + ".har", "w")
                # fo.write(json.dumps(har_data))
                # fo.close()
        if obj['command'] == 'type':
            print("type found")
            driver.find_element(selector_map[obj['target'].split('=')[0]],obj['target'].split('=')[1]).send_keys(obj['value'])
        if obj['command'] == 'select' or obj['command'] == 'addSelection':
            select = Select(driver.find_element(selector_map[obj['target'].split('=')[0]],obj['target'].split('=')[1]))
            select.select_by_visible_text(obj['value'].split('=')[1])

    server.stop()
    print("har files generated")
    driver.quit()
    display.stop()
    return har_arr

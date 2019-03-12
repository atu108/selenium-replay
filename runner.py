from browsermobproxy import Server
import json
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import os
import re
from flask import Flask
from collections import OrderedDict
# from xvfbwrapper import Xvfb
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def runner(selenium_file):
    print("reached inside runner")
    har_arr = OrderedDict()
    server = Server("./browsermob-proxy-2.1.4/bin/browsermob-proxy")
    print("included proxy")
    server.start()
    proxy = server.create_proxy()
    profile = webdriver.FirefoxProfile()
    # display = Xvfb()
    # display.start()
    profile.set_proxy(proxy.selenium_proxy())
    driver = webdriver.Firefox(firefox_profile=profile, executable_path='./geckodriver')
    # driver.set_page_load_timeout(20)
    print("reached downwards")
    selector_map = {
        "id": "id",
        "xpath": "xpath",
        "name": "name",
        "css": "css selector",
        "class": "class name",
        "tag": "tag name",
        "linkText": "link text"
    }
    # with open('test.side') as f:
    print(os.path.join(os.getcwd(),app.config['UPLOAD_FOLDER'], selenium_file))
    with open(os.path.join(os.getcwd(),app.config['UPLOAD_FOLDER'], selenium_file)) as f:
        data = json.load(f)
    # data = json.load(selenium_file)
    # directory = data['name']
    # if not os.path.exists(directory):
    #     os.makedirs(directory)
    proxy.new_har("google", {"captureHeaders": True, "captureContent": True})
    driver.get(data['url'] + data['tests'][0]['commands'][0]['target'])
    har_data = proxy.har
    if len(har_data['log']['entries']) > 0:
        har_arr['launch'] = har_data
        # fo = open("./" + directory + "/launch.har", "w")
        # fo.write(json.dumps(har_data))
        # fo.close()
    i = 0
    try:
        for obj in data['tests'][0]['commands']:
            i = i + 1
            print("commands executed  " + str(i))
            proxy.new_har("google", {"captureHeaders": True, "captureContent": True})
            if obj["command"] == 'mouseOver':
                try:
                    ele = driver.find_element(selector_map[obj['target'].split('=')[0]], obj['target'].split('=')[1])
                except NoSuchElementException:
                    ele = driver.find_element(selector_map[obj['targets'][-1][0].split('=')[0]], obj['targets'][-1][0].split('=')[1])
                hover = ActionChains(driver).move_to_element(ele)
                hover.perform()
            if obj['command'] == 'click':
                try:
                    element = driver.find_element(selector_map[obj['target'].split('=')[0]], obj['target'].split('=')[1])
                except NoSuchElementException:
                    print("first failed to click")
                    element = driver.find_element(selector_map[obj['targets'][-1][0].split('=')[0]], obj['targets'][-1][0].split('=')[1])
                file_name = element.get_attribute('innerHTML')
                if file_name == '' or not re.match(r'^\w+$', file_name.replace(" ", '_')):
                    file_name = 'Step_' + str(i)

                try:
                    element.click()
                except ElementClickInterceptedException:
                    driver.find_element(selector_map[obj['targets'][-1][0].split('=')[0]],
                                        obj['targets'][-1][0].split('=')[1]).click()
                har_data = proxy.har
                if len(har_data['log']['entries']) > 0:
                    har_arr[file_name] = har_data
                    # fo = open("./" + directory + "/" + obj['target'].split('=')[1] + ".har", "w")
                    # fo.write(json.dumps(har_data))
                    # fo.close()
            if obj['command'] == 'type':
                try:
                    driver.find_element(selector_map[obj['target'].split('=')[0]],obj['target'].split('=')[1]).send_keys(obj['value'])
                except NoSuchElementException:
                    driver.find_element(selector_map[obj['targets'][-1][0].split('=')[0]], obj['targets'][-1][0].split('=')[1]).send_keys(
                        obj['value'])
            if obj['command'] == 'select' or obj['command'] == 'addSelection':
                try:
                    select = Select(driver.find_element(selector_map[obj['target'].split('=')[0]],obj['target'].split('=')[1]))
                except NoSuchElementException:
                    select = Select(
                        driver.find_element(selector_map[obj['targets'][-1][0].split('=')[0]], obj['targets'][-1][0].split('=')[1]))
                select.select_by_visible_text(obj['value'].split('=')[1])
            if obj['command'] == 'sendKeys':
                try:
                    driver.find_element(selector_map[obj['target'].split('=')[0]],obj['target'].split('=')[1]).send_keys(Keys.ENTER)
                except NoSuchElementException:
                    driver.find_element(selector_map[obj['targets'][-1][0].split('=')[0]], obj['targets'][-1][0].split('=')[1]).send_keys(
                        Keys.ENTER)
    except Exception as e:
        server.stop()
        driver.quit()
        # display.stop()
        return {"status":"failed", "message": "Something Went wrong", "error": e}
    server.stop()
    print("har files generated")
    driver.quit()
    # display.stop()
    return {"status":"success", "hars": dict(har_arr)}

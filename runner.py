from browsermobproxy import Server
import json
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
from selenium.webdriver.common.keys import Keys
import re
from flask import Flask
from collections import OrderedDict
from bs4 import BeautifulSoup
import time

import tldextract
# from xvfbwrapper import Xvfb
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
excluded_url = [
    'mozilla',
    'googlesyndication.com'
]
selector_map = {
    "id": "id",
    "xpath": "xpath",
    "name": "name",
    "css": "css selector",
    "class": "class name",
    "tag": "tag name",
    "linkText": "link text"
}

form_elements = ["<input", "<select"]


def get_transaction_name(element):
    element_html = element.get_attribute("outerHTML")
    tag_name = element_html.split(" ",1)[0]
    print(tag_name)
    if tag_name in form_elements:
        if element.get_attribute("type") == 'submit':
            return element.get_attribute("value")
        else:
            return element.get_attribute("name")
    else:
        return element.text


def get_x_path_relative(targets):
    temp = ''
    for t in targets:
        if t[1] == "xpath:position":
            return t
        elif t[1] == "css:finder":
            temp = t
    return temp


def try_all_paths(targets, driver):
    if len(targets) == 0:
        return False
    wait = WebDriverWait(driver, 10, poll_frequency=1,
                         ignored_exceptions=[])
    try:
        element = wait.until(EC.element_to_be_clickable((selector_map[targets[-1][0].split('=')[0]],
                                                      targets[-1][0].split('=')[1])))
        print("targets", targets[-1][0].split('=')[1] )
        print("before return", )
        return {"element": element, "remlen": len(targets)}
    except Exception as e:
        print("targets length", len(targets), e)
        return try_all_paths(targets[:-1], driver)

mouseOverScript = "if(document.createEvent){var evObj = document.createEvent('MouseEvents');evObj.initEvent('mouseover',true, false); arguments[0].dispatchEvent(evObj);} else if(document.createEventObject) { arguments[0].fireEvent('onmouseover');}"
performance_data = "var performance = window.performance || window.webkitPerformance || window.mozPerformance || window.msPerformance || {};var timings = performance.timing || {};return timings;"


def runner(data, file, url, saveDropdown, savePerformanceMatrix):
    print("reached inside runner")
    har_arr = []
    performance_arr = OrderedDict()
    select_arr = []
    server = Server("./browsermob-proxy-2.1.4/bin/browsermob-proxy")
    print("included proxy")
    server.start()
    proxy = server.create_proxy()
    # profile = webdriver.FirefoxProfile()
    profile = webdriver.ChromeOptions()
    #profile.add_argument('--headless')
    profile.add_argument('--no-sandbox')
    profile.add_argument('--disable-dev-shm-usage')
    from pyvirtualdisplay import Display
    display = Display(visible=0, size=(1024, 768))
    display.start()
    # display = Xvfb()
    # display.start()
    # profile.set_proxy(proxy.selenium_proxy())
    profile.add_argument('--proxy-server={host}:{port}'.format(host='localhost', port=proxy.port))
    # driver = webdriver.Firefox(firefox_profile=profile, executable_path='./chromedriver')
    driver = webdriver.Chrome(executable_path="./chromedriver", chrome_options=profile)
    driver.maximize_window()
    # driver.set_page_load_timeout(20)
    print("reached downwards")
    # print("testing data", data)
    proxy.new_har("google", {"captureHeaders": True, "captureContent": True})
    driver.get(url)
    har_data = proxy.har
    prev_har_seq = 0
    if len(har_data['log']['entries']) > 0:
        # for entry in har_data['log']['entries']:
        #     test_urls = entry.request.url.split('?')[0]
        #     parsed_url = tldextract.extract('test_urls')
        #     if
        har_arr.append({
            "name": "launch",
            "har_data": har_data,
            "sequence": prev_har_seq + 1
        })
        prev_har_seq = prev_har_seq + 1
        performance_arr['launch'] = {
            "perf_data": driver.execute_script(performance_data),
            "sequence": prev_har_seq + 1
        }

    i = 0
    try:
        for obj in data:
            i = i + 1
            relativeOrPosXPath = get_x_path_relative(obj["targets"])
            proxy.new_har("google", {"captureHeaders": True, "captureContent": True})
            if obj["command"] == 'mouseOver':
                time.sleep(10)
                ele = try_all_paths(obj['targets'], driver)
                try:
                    driver.execute_script("arguments[0].scrollIntoView()", ele)
                    driver.execute_script(mouseOverScript, ele)
                except Exception as e:
                    continue
            if obj['command'] == 'click' or obj['command'] == 'mouseDown':
                time.sleep(10)
                elementDetails = try_all_paths(obj['targets'], driver)
                element = elementDetails['element']
                if element is None:
                    obj['targets'].pop(elementDetails['remlen'] - 1)
                    elementDetails = try_all_paths(obj['targets'], driver)
                    element = elementDetails['element']
                print("elelement", type(element))
                file_name = get_transaction_name(element)
                if file_name == '' or None or not re.match(r'^\w+$', file_name.replace(" ", '_')):
                    file_name = 'Step_' + str(i)
                # try:
                driver.execute_script("arguments[0].scrollIntoView()", element)
                print(driver.window_handles[0])
                driver.execute_script("arguments[0].click()", element)
                print("perfromance data ", driver.execute_script(performance_data))
                perf_data = driver.execute_script(performance_data)
                har_data = proxy.har
                print(har_data)
                har_arr.append({
                    "name": file_name,
                    "har_data": har_data,
                    "sequence": prev_har_seq + 1
                })
                performance_arr[file_name] = {
                    "perf_data" : perf_data,
                    "sequence": prev_har_seq + 1
                }
                prev_har_seq = prev_har_seq + 1
            if obj['command'] == 'runScript':
                # time.sleep(10)
                driver.execute_script(obj['target'])
            if obj['command'] == 'type':
                time.sleep(10)
                elementDetails = try_all_paths(obj['targets'], driver)
                ele = elementDetails['element']
                ele.clear()
                ele.send_keys(obj['value'])
            if obj['command'] == 'select' or obj['command'] == 'addSelection':
                try:
                    select = Select(
                        driver.find_element(selector_map[obj['target'].split('=')[0]], obj['target'].split('=')[1]))
                except NoSuchElementException:
                    print("inside no such element")
                    select = Select(
                        driver.find_element(selector_map[relativeOrPosXPath[0].split('=')[0]],
                                            relativeOrPosXPath[0].split('=')[1]))
                select.select_by_visible_text(obj['value'].split('=')[1])
                if saveDropdown:
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    options = soup.find('select', {obj['target'].split('=')[0]: obj['target'].split('=')[1]}).find_all(
                        'option')
                    temp_arr = []
                    for op in options:
                        temp_arr.append(op.text)
                        select_arr.append({
                            "options": temp_arr,
                            "selenium_step": obj["_id"]
                        })
            if obj['command'] == 'sendKeys':
                try:
                    driver.find_element(selector_map[obj['target'].split('=')[0]],
                                        obj['target'].split('=')[1]).send_keys(Keys.ENTER)
                except NoSuchElementException:
                    driver.find_element(selector_map[relativeOrPosXPath[0].split('=')[0]],
                                        relativeOrPosXPath[0].split('=')[1]).send_keys(
                        Keys.ENTER)
            if obj['command'] == "selectWindow":
                print("switched window", driver.window_handles[1])
                driver.switch_to.window(driver.window_handles[-1])
    except Exception as e:
        print(e)
        driver.get_screenshot_as_file('screenshots/error_' + file.split('.')[0] + '_step_' + str(i) + '.png')
        server.stop()
        driver.quit()
        # display.stop()
        return {"status": "failed", "message": "Something Went wrong"}
    server.stop()
    print("har files generated")
    driver.quit()
    # display.stop()
    if savePerformanceMatrix:
        return {"success": True, "hars": har_arr, "select": select_arr, "performance": dict(performance_arr)}
    else:
        return {"success": True, "hars": har_arr, "select": select_arr, "performance": {}}

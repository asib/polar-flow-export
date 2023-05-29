from selenium import webdriver
import requests
import re
import time
import sys
import os

FLOW_URL = "https://flow.polar.com"

def login(driver, username, password):
    driver.get("%s/login" % FLOW_URL)
    driver.find_element_by_name("email").send_keys(username)
    driver.find_element_by_name("password").send_keys(password)
    driver.find_element_by_id("login").click()

def get_exercise_ids(driver, year, month):
    driver.get("%s/diary/%s/month/%s" % (FLOW_URL, year, month))
    time.sleep(2)
    ids = map(
        # The subscript removes the prefix
        lambda e: e.get_attribute("href")[len("https://flow.polar.com/training/analysis/"):],
        driver.find_elements_by_xpath("//div[@class='event event-month exercise']/a")
    )
    return ids

def export_exercise(driver, exercise_id, output_dir):
    def _load_cookies(session, cookies):
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])

    s = requests.Session()
    _load_cookies(s, driver.get_cookies())

    def _get_filename(r):
        regex = r"filename=\"([\w._-]+)\""
        return re.search(regex, r.headers['Content-Disposition']).group(1)

    r = s.get("%s/api/export/training/tcx/%s" % (FLOW_URL, exercise_id))
    tcx_data = r.text
    filename = _get_filename(r)

    outfile = open(os.path.join(output_dir, filename), 'w')
    outfile.write(tcx_data)
    outfile.close()
    print("Wrote file %s" % filename)

def run(driver, username, password, month, year, output_dir):
    login(driver, username, password)
    time.sleep(5)
    exercise_ids = get_exercise_ids(driver, year, month)
    for ex_id in exercise_ids:
        export_exercise(driver, ex_id, output_dir)

if __name__ == "__main__":
    try:
        (username, password, month, year, output_dir) = sys.argv[1:]
    except ValueError:
        sys.stderr.write(("Usage: %s <username> <password> <month> <year> <output_dir>\n") % sys.argv[0])
        sys.exit(1)

    driver = webdriver.Chrome()
    try:
        run(driver, username, password, month, year, output_dir)
    finally:
        driver.quit()

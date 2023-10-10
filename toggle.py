#!/usr/bin/env python

import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ChromeOptions
import argparse
from time import sleep

load_dotenv()

IMPLICIT_WAIT = 6  # seconds wait for finding elements
EXPLICIT_HACKY_CRAPPY_WAIT = 2

ROUTER_IP = os.getenv("ROUTER_IP")
ROUTER_USERNAME = os.getenv("ROUTER_USERNAME")
ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD")
EXTENSION_IP = os.getenv("EXTENSION_IP")
EXTENSION_PASSWORD = os.getenv("EXTENSION_PASSWORD")
CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER_PATH")

parser = argparse.ArgumentParser(
    prog="wifi_toggle", description="Toggles wifi between router and extension."
)

parser.add_argument(
    "-cdp",
    "--chrome_driver_path",
    default=CHROME_DRIVER_PATH,
    help="Path to the chrome web driver",
    type=str,
)
parser.add_argument(
    "-ri", "--router_ip", default=ROUTER_IP, help="Router's IP address.", type=str
)
parser.add_argument(
    "-ru",
    "--router_username",
    default=ROUTER_USERNAME,
    help="Login username for the router",
    type=str,
)
parser.add_argument(
    "-rp",
    "--router_password",
    default=ROUTER_PASSWORD,
    help="Login password for the router",
    type=str,
)
parser.add_argument(
    "-ei",
    "--extension_ip",
    default=EXTENSION_IP,
    help="Extension's IP address.",
    type=str,
)
parser.add_argument(
    "-ep",
    "--extension_password",
    default=EXTENSION_PASSWORD,
    help="Login password for the extension",
    type=str,
)
parser.add_argument(
    "-c",
    "--check",
    help="Only check the status and report. Do not toggle.",
    action="store_true",
)
parser.add_argument(
    "-hf",
    "--headful",
    help="Do not run the chrome driver in headless mode.",
    action="store_true",
)
parser.add_argument(
    "-w",
    "--wait",
    help="Wait for confirmation before exiting.",
    action="store_true",
)


class WifiToggle:
    _driver = None
    _router_handle = None
    _extension_handle = None
    _implicit_wait = IMPLICIT_WAIT

    def __init__(
        self,
        chrome_driver_path,
        headful,
        router_ip,
        router_username,
        router_password,
        extension_ip,
        extension_password,
    ):
        self.chrome_driver_path = chrome_driver_path
        self.headful = headful
        self.router_username = router_username
        self.router_password = router_password
        self.extension_password = extension_password

        self.router_page = RouterPage(url=f"http://{router_ip}")
        self.extension_page = ExtensionPage(url=f"http://{extension_ip}")

    def _init_driver(self):
        options = ChromeOptions()
        if not self.headful:
            options.add_argument("--headless=new")
        chrome_driver_service = Service(self.chrome_driver_path)
        self._driver = webdriver.Chrome(service=chrome_driver_service, options=options)
        self._driver.implicitly_wait(self._implicit_wait)
        self._router_handle = self._driver.current_window_handle
        self._driver.switch_to.new_window("tab")
        self._extension_handle = self._driver.current_window_handle

    def check(self):
        try:
            self._init_driver()
            self._check_status()
        except Exception as e:
            print("Error: ", e)
        finally:
            self._driver.quit()

    def _check_status(self):
        print("Logging into router...")
        # Login to the router's interface
        self._driver.switch_to.window(self._router_handle)
        self._driver.get(self.router_page.url)
        self.router_page.login(self._driver, self.router_username, self.router_password)
        router_status = self.router_page.wifi_on(self._driver)

        print("Logging into extension...")
        # Login to the extension's interface
        self._driver.switch_to.window(self._extension_handle)
        self._driver.get(self.extension_page.url)
        self.extension_page.login(self._driver, self.extension_password)
        extension_status = self.extension_page.wifi_on(self._driver)

        print(
            "Currently: router wifi is {router_status}; extension wifi is {extension_status}".format(
                router_status="on" if router_status else "off",
                extension_status="on" if extension_status else "off",
            )
        )

        return router_status, extension_status

    def toggle(self):
        try:
            self._init_driver()
            self._toggle()
        except Exception as e:
            print("Error: ", e)
        finally:
            self._driver.quit()

    def _toggle(self):
        print("Toggling wifi...")

        router_status, extension_status = self._check_status()

        if router_status and not extension_status:
            print("Turning extension wifi on...")
            self._driver.switch_to.window(self._extension_handle)
            self.extension_page.turn_wifi_on(self._driver)

            # TODO: Hop to the extension's network, so we don't get downtime

            print("Turning router wifi off...")
            self._driver.switch_to.window(self._router_handle)
            self.router_page.turn_wifi_off(self._driver)
        elif not router_status and extension_status:
            print("Turning router wifi on...")
            self._driver.switch_to.window(self._router_handle)
            self.router_page.turn_wifi_on(self._driver)

            # TODO: Hop to the router's network, so we don't get downtime

            print("Turning extension wifi off...")
            self._driver.switch_to.window(self._extension_handle)
            self.extension_page.turn_wifi_off(self._driver)


class RouterPage:
    def __init__(
        self,
        url,
        login_id="Frm_Username",
        pass_id="Frm_Password",
        login_b_id="LoginId",
        wifi_settings_xpath="//div[@id='home_category_setting']/a",
        radio_wifi_on_id="RadioStatus0_1",
        radio_wifi_off_id="RadioStatus1_1",
        apply_b_id="Btn_apply_WlanBasicAdConf",
        success_msg_xpath="//div[@class='succHint']",
    ) -> None:
        self.url = url
        self.login_id = login_id
        self.pass_id = pass_id
        self.login_b_id = login_b_id
        self.wifi_settings_xpath = wifi_settings_xpath
        self.radio_wifi_on_id = radio_wifi_on_id
        self.radio_wifi_off_id = radio_wifi_off_id
        self.apply_b_id = apply_b_id
        self.success_msg_xpath = success_msg_xpath

    def login(self, driver, uname, password):
        router_uname_el = driver.find_element(By.ID, self.login_id)
        router_uname_el.clear()
        router_uname_el.send_keys(uname)

        router_pass_el = driver.find_element(By.ID, self.pass_id)
        router_pass_el.clear()
        router_pass_el.send_keys(password)

        driver.find_element(By.ID, self.login_b_id).click()

    def wifi_on(self, driver):
        driver.find_element(By.XPATH, self.wifi_settings_xpath).click()
        return driver.find_element(By.ID, self.radio_wifi_on_id).is_selected()

    def turn_wifi_on(self, driver):
        driver.find_element(By.ID, self.radio_wifi_on_id).click()
        driver.find_element(By.ID, self.apply_b_id).click()
        wait = WebDriverWait(driver, IMPLICIT_WAIT)
        wait.until(EC.visibility_of_element_located((By.XPATH, self.success_msg_xpath)))

    def turn_wifi_off(self, driver):
        driver.find_element(By.ID, self.radio_wifi_off_id).click()
        driver.find_element(By.ID, self.apply_b_id).click()
        wait = WebDriverWait(driver, IMPLICIT_WAIT)
        wait.until(EC.visibility_of_element_located((By.XPATH, self.success_msg_xpath)))


class ExtensionPage:
    def __init__(
        self,
        url,
        pass_id="login-password",
        login_b_id="submit",
        wifi_settings_xpath="//ul/li/a[@href='#wireless']",
        wifi_frame_div_id="iframe-content",
        wifi_settings_iframe_id="main_iframe",
        wifi_toggle_id="wifiEn",
        wifi_toggle_on_class="wifiOn",
        wifi_toggle_off_class="wifiOff",
        confirm_b_id="submit",
    ) -> None:
        self.url = url
        self.pass_id = pass_id
        self.login_b_id = login_b_id
        self.wifi_settings_xpath = wifi_settings_xpath
        self.wifi_frame_div_id = wifi_frame_div_id
        self.wifi_settings_iframe_id = wifi_settings_iframe_id
        self.wifi_toggle_id = wifi_toggle_id
        self.wifi_toggle_on_class = wifi_toggle_on_class
        self.wifi_toggle_off_class = wifi_toggle_off_class
        self.confirm_b_id = confirm_b_id

    def login(self, driver, password):
        extension_pass_el = driver.find_element(By.ID, self.pass_id)
        extension_pass_el.clear()
        extension_pass_el.send_keys(password)

        driver.find_element(By.ID, self.login_b_id).click()

    def wifi_on(self, driver):
        self._navigate_to_wifi_settings(driver)
        wifi_toggle_el = driver.find_element(By.ID, self.wifi_toggle_id)
        wifi_toggle_class = wifi_toggle_el.get_attribute("class")
        # switch back to the default content
        driver.switch_to.default_content()

        return wifi_toggle_class == self.wifi_toggle_on_class

    def turn_wifi_on(self, driver):
        if not self.wifi_on(driver):
            self._toggle_wifi(driver)
            # only wait in the ON method, since the OFF method will close the connection
            # before updating the status
            wait = WebDriverWait(driver, 10)
            wait.until(EC.text_to_be_present_in_element((By.ID, "ajax-massage"), "OK"))

    def turn_wifi_off(self, driver):
        if self.wifi_on(driver):
            self._toggle_wifi(driver)

    def _toggle_wifi(self, driver):
        self._navigate_to_wifi_settings(driver)
        wifi_toggle_el = driver.find_element(By.ID, self.wifi_toggle_id)
        wifi_toggle_el.click()
        # switch back to the default content
        driver.switch_to.default_content()

        # apply the change and report the status
        driver.find_element(By.ID, self.confirm_b_id).click()

    def _navigate_to_wifi_settings(self, driver):
        """Makes sure to return to the default content after calling this
        method by calling driver.switch_to.default_content()"""

        driver.find_element(By.XPATH, self.wifi_settings_xpath).click()

        # wait for the wifi frame to refresh
        wait = WebDriverWait(driver, IMPLICIT_WAIT)
        wait.until(EC.visibility_of_element_located((By.ID, self.wifi_frame_div_id)))
        # the wifi toggle is in an iframe
        wait = WebDriverWait(driver, IMPLICIT_WAIT)
        wait.until(
            EC.frame_to_be_available_and_switch_to_it(
                (By.ID, self.wifi_settings_iframe_id)
            )
        )
        # there is a weird behavior in the extension web page where the settings page
        # first loads with the wifi toggle on, then it refreshes with the correct
        sleep(EXPLICIT_HACKY_CRAPPY_WAIT)


if __name__ == "__main__":
    args = parser.parse_args()

    print(
        "Router IP: {router_ip}. Extension IP: {extension_ip}".format(
            router_ip=args.router_ip, extension_ip=args.extension_ip
        )
    )

    wifi_toggle = WifiToggle(
        chrome_driver_path=args.chrome_driver_path,
        headful=args.headful,
        router_ip=args.router_ip,
        router_username=args.router_username,
        router_password=args.router_password,
        extension_ip=args.extension_ip,
        extension_password=args.extension_password,
    )

    if args.check:
        print("Checking wifi status...")
        wifi_toggle.check()
    else:
        wifi_toggle.toggle()

    if args.wait:
        input("Press Enter to continue...")

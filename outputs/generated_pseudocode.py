```python
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile

class TestSauceDemoWorkflow:
    def setup_method(self):
        options = webdriver.ChromeOptions()
        self.temp_profile = tempfile.TemporaryDirectory()
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False
        }
        options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 60)

    def teardown_method(self):
        self.driver.quit()
        self.temp_profile.cleanup()

    def wait_for_element_visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def enter_text(self, locator, text):
        element = self.wait_for_element_visible(locator)
        element.clear()
        element.send_keys(text)

    def click_element(self, locator):
        element = self.wait.until(EC.element_to_be_clickable(locator))
        element.click()

    def validate_title_contains(self, text):
        assert text in self.driver.title, f"Title does not contain '{text}'"

    def step_navigate_to_login_page(self):
        self.driver.get("https://www.saucedemo.com")

    def step_enter_username(self):
        self.enter_text((By.ID, "user-name"), "standard_user")

    def step_enter_password(self):
        self.enter_text((By.ID, "password"), "secret_sauce")

    def step_click_login(self):
        self.click_element((By.ID, "login-button"))

    def step_validate_dashboard(self):
        self.validate_title_contains("Swag Labs")

    def step_click_inventory_tab(self):
        self.click_element((By.XPATH, "//div[@class='app_logo']"))

    def step_validate_inventory_page(self):
        self.validate_title_contains("Swag Labs")

    def step_click_add_to_cart_backpack(self):
        self.click_element((By.XPATH, "//button[contains(text(), 'Add to cart') and contains(@data-test, 'add-to-cart-sauce-labs-backpack')]"))

    def step_click_add_to_cart_onesie(self):
        self.click_element((By.XPATH, "//button[contains(text(), 'Add to cart') and contains(@data-test, 'add-to-cart-sauce-labs-onesie')]"))

    def step_click_shopping_cart_icon(self):
        self.click_element((By.XPATH, "//a[@class='shopping_cart_link']"))

    def step_validate_cart_title(self):
        cart_title = self.wait_for_element_visible((By.XPATH, "//span[@class='title' and contains(text(), 'Your Cart')]"))
        assert cart_title.is_displayed(), "Your Cart title is not displayed"

    def step_validate_cart_items(self):
        backpack_item = self.wait_for_element_visible((By.XPATH, "//div[@class='cart_item' and contains(., 'Sauce Labs Backpack')]"))
        onesie_item = self.wait_for_element_visible((By.XPATH, "//div[@class='cart_item' and contains(., 'Sauce Labs Onesie')]"))
        assert backpack_item.is_displayed(), "Sauce Labs Backpack not found in cart"
        assert onesie_item.is_displayed(), "Sauce Labs Onesie not found in cart"

    def step_click_remove_onesie(self):
        self.click_element((By.XPATH, "//button[contains(@data-test, 'remove-sauce-labs-onesie')]"))

    def step_validate_onesie_removed(self):
        onesie_item = self.driver.find_elements(By.XPATH, "//div[@class='cart_item' and contains(., 'Sauce Labs Onesie')]")
        assert len(onesie_item) == 0, "Sauce Labs Onesie still present in cart"

    def step_click_checkout_button(self):
        self.click_element((By.XPATH, "//button[@data-test='checkout']"))

    def test_workflow(self):
        self.step_navigate_to_login_page()
        self.step_enter_username()
        self.step_enter_password()
        self.step_click_login()
        self.step_validate_dashboard()
        self.step_click_inventory_tab()
        self.step_validate_inventory_page()
        self.step_click_add_to_cart_backpack()
        self.step_click_add_to_cart_onesie()
        self.step_click_shopping_cart_icon()
        self.step_validate_cart_title()
        self.step_validate_cart_items()
        self.step_click_remove_onesie()
        self.step_validate_onesie_removed()
        self.step_click_checkout_button()
```
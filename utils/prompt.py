from utils.ui import get_ui_entry_url, load_ui_context,extract_locators

SYSTEM_PROMPT = f"""
You are a Senior QA Automation Engineer with expertise in Python, Selenium,
and test automation.

Your task is to convert manual test cases from uploaded documents
(Excel, PDF, DOCX, CSV, TXT) into production-quality Selenium Python automation scripts.

Important:
- Use the provided UI context as the source of truth for screens, forms, buttons, tabs, and fields.
- Generate pseudocode that is specific to the UI files provided.
- Do not invent pages, actions, or flows that are not present in the UI context.

Instructions:

1. Carefully read the entire document before generating code.
2. Understand every test case individually.
3. Preserve the order of execution exactly as written.
4. Identify:
   - Test Case ID
   - Test Case Name
   - Preconditions
   - Expected Result
   
5. Infer the user actions from the manual steps.
6. Generate clean, executable Python Selenium code.
7. Use meaningful variable and function names.
8. Add comments for every major step.
9. Include appropriate waits (WebDriverWait) instead of time.sleep().
10. Use explicit waits wherever possible.
11. Add assertions based on the Expected Result.
12. Generate one automation function for each test case.
13. If multiple test cases exist in the uploaded document, generate code for all of them.
14. It should able to write the Valid Xpaths.If element locators are not provided, insert descriptive TODO comments such as:
    # TODO: Replace with actual locator
15. Do not invent URLs or locators. Use placeholders where necessary.
16. Return only Python in pytest and Selenium code without explanations or markdown.
17. Ensure the generated code is ready to run in a Selenium environment.
18. If the document contains multiple test cases, It should generate code for each testcases using selenium and python both.
19. Don't stop generating code until all test cases or TC steps are covered.
20. don't include any markdown or code block formatting in the output.
21. Add pytest markers for all testcases or methods.
"""

UI_PROMPT = f"""
UI-AWARE PSEUDOCODE RULES:
- Only use locators, element names, page names, and interactions that are explicitly present in the UI files below.
- Do not invent new locators, IDs, classes, or element names from general knowledge.
- If a required element does not appear in the provided UI files, use a TODO placeholder such as '# TODO: Replace with actual locator'.
- Base every generated step on the exact UI screens, buttons, forms, tabs, and modal flows visible in the UI files below.
- Match the pseudocode to the UI folder you provided, not to any other application or generic web layout.
- If no URL is provided in the UI files, do not invent one.
- Derive the entry URL from the UI folder itself and use the local index page as the source URL context.
- If a local entry URL can be resolved from the UI folder, prefer that derived URL over any invented or generic URL.
- Derived entry URL: {get_ui_entry_url() or 'No local entry URL available.'}

UI CONTEXT (ONLY THIS UI FOLDER):
{load_ui_context()}
{extract_locators()}
"""

def build_prompt(test_case):
    return f"""
The following content was extracted from a manual testing document.
The source may be Excel, PDF, Word, CSV, or TXT.

Generate Selenium Python automation code using a pytest-compatible class-based approach.

IMPORTANT

- UI_CONTEXT is the single source of truth.
- Never create locators that are not present in UI_CONTEXT.
- Never infer locators from test steps.
- Never infer locators from expected results.
- Never infer locators from visible text.
- Never infer locators from page names.
- Never infer locators from button names.
- Never infer locators from modal names.
- A TODO placeholder is ALWAYS preferred over an invented locator.
- Accuracy is more important than completeness.


BROWSER INITIALIZATION RULES

- Always create the browser using ChromeOptions.
- Never initialize Chrome as webdriver.Chrome() without options.
- Generate ChromeOptions before creating the driver.

Example:

options = webdriver.ChromeOptions()
self.driver = webdriver.Chrome(options=options)

- Any required browser arguments should be added through options.add_argument().
- Always pass the options object when creating the Chrome driver.
- Always import tempfile in generated code.

IMPORTANT:
Whenever generating Selenium Python automation code, always create a temporary Chrome profile immediately after creating the ChromeOptions object. Configure Chrome to disable password manager popups and credential services. In the teardown process, always call self.temp_profile.cleanup() to remove the temporary profile directory. Do not generate any Selenium framework or test script that omits these requirements.
And a prefs dictionary should be created with the following keys and values:
"credentials_enable_service": False,
"profile.password_manager_enabled": False,
"profile.password_manager_leak_detection": False
And it should first create the options object, then create the prefs dictionary, and finally add it to the ChromeOptions object using options.add_experimental_option("prefs", prefs) before maximize it.


CLASS STRUCTURE RULES

- Generate exactly one class.
- Use self.driver and self.wait throughout the class.
- Do not generate __init__().
- Initialize browser in setup_method().
- Close browser in teardown_method().

Example:

def setup_method(self):
    self.driver = webdriver.Chrome()
    self.driver.maximize_window()
    self.wait = WebDriverWait(self.driver, 60)

def teardown_method(self):
    self.driver.quit()

WORKFLOW RULES

1. Generate exactly ONE workflow test method named `test_workflow()`.
2. Treat all manual test steps as a single continuous business workflow.
3. Never generate separate test methods such as:
   - test_tc_001_*
   - test_tc_002_*
   - test_tc_003_*
   - etc.
4. Preserve the exact execution order of the source test case.
5. Preserve application state across all steps.
6. Execute the workflow from start to finish in the same browser session.
7. Use `driver.get()` only once at the beginning of the workflow.
8. Never navigate back to the login page unless explicitly specified.
9. Never repeat login steps unless explicitly documented in the test case.
10. Do not reset, restart, or recreate the browser during workflow execution.
11. Generate one dedicated step method for every manual test step.
12. Never combine multiple manual steps into a single step method.
13. Each step method must perform only one business action or validation.
14. The workflow test method must contain only step method calls.
15. All Selenium actions and assertions must be implemented inside the corresponding step methods.
16. Step methods must be executed sequentially by `test_workflow()`.
17. Data created in earlier steps must be available to later steps.
18. Do not create independent tests for intermediate screens, tabs, popups, or validations.
19. Consider all steps dependent and part of a single end-to-end scenario.
20. Generate output in the following structure:

    - setup_method()
    - teardown_method()
    - utility methods
    - step_xxx() methods
    - test_workflow()

21. The generated code must follow this pattern:

    def test_workflow(self):
        self.step_navigate_to_login_page()
        self.step_enter_username()
        self.step_enter_password()
        self.step_click_login()
        self.step_validate_dashboard()
        self.step_click_ticket_tab()
        self.step_validate_ticket_page()
        self.step_click_add_button()
        self.step_validate_add_popup()
        self.step_enter_tenant_name()
        self.step_enter_tenant_age()
        self.step_enter_tenant_id()
        self.step_click_save()
        self.step_validate_record_added()

22. Never generate multiple pytest test methods for individual steps.
23. Never create test cases that depend on execution order between separate test methods.
24. Always produce a single executable end-to-end workflow test.
25. The final output must resemble:

    class TestWorkflow:
        ...
        def step_xxx(self):
            ...

        def step_xxx(self):
            ...

        def test_workflow(self):
            self.step_xxx()
            self.step_xxx()
            self.step_xxx()

Result:
✓ One browser session
✓ One login
✓ One workflow test
✓ State preserved across all steps
✓ No test_tc_001/test_tc_002/test_tc_003 style test splitting
✓ End-to-end execution only

SELENIUM RULES

- Use Explicit Waits only.
- Use WebDriverWait(self.driver, 60).
- Do not use implicit waits.
- Do not use time.sleep().
- Use visibility_of_element_located for text entry.
- Use visibility_of_element_located for validations.
- Use element_to_be_clickable for clicks.

HELPER METHODS

Generate reusable methods:

- wait_for_element_visible()
- enter_text()
- click_element()
- validate_title_contains()

CRITICAL LOCATOR RULE

Before generating ANY locator perform this validation:

STEP 1:
Check whether the exact element exists in UI_CONTEXT.

STEP 2:
Check whether the exact attribute exists in UI_CONTEXT.

STEP 3:
If the element or attribute cannot be verified:

    # TODO: Locator not found in UI_CONTEXT

DO NOT generate a locator.

FORBIDDEN LOCATOR BEHAVIOR

Never generate locators from:

- contains(text())
- visible text
- button labels
- modal headings
- page names
- expected result statements
- test step descriptions
- dashboard names
- tab names

The following are forbidden unless explicitly present in UI_CONTEXT:

(By.CLASS_NAME, "title")
(By.CLASS_NAME, "page-title")
(By.CLASS_NAME, "header-title")
(By.ID, "dashboardPage")
(By.ID, "ticketPage")

LOCATOR PRIORITY

CSS selectors are preferred over XPath.

CSS SELECTORS > XPATH > ID > CLASS_NAME > NAME > TAG_NAME

Never use XPath based on text content.
Never use:

contains(text())
text()='value'
normalize-space()
contains(.,'value')

Example of FORBIDDEN locator:

//button[contains(@class,'cart_button') and contains(text(),'Checkout')]

If a valid attribute-based locator cannot be found in UI_CONTEXT, generate:

# TODO: Locator not found in UI_CONTEXT

instead of generating a text-based XPath.

XPATH RULES

Generate XPath ONLY IF:

- The exact XPath can be derived directly from UI_CONTEXT.
- Every attribute used in the XPath exists in UI_CONTEXT.

Otherwise generate:

    # TODO: Locator not found in UI_CONTEXT

DOM RULES

Example:

<div class="header">
    <b>S&amp;S RajaMouli</b>
</div>

Correct:

(By.XPATH, "//div[@class='header']//b")

Incorrect:

(By.XPATH, "//div[contains(text(),'S&S RajaMouli')]")

VALIDATION RULES

Generate validations ONLY when the validation target exists in UI_CONTEXT.

Allowed validations:

- Title validation
- URL validation
- Existing tabs
- Existing buttons
- Existing controls
- Existing modal dialogs
- Existing dashboard elements

If validation target cannot be verified:

    # TODO: Validation element not found in UI_CONTEXT

Do not invent validation locators.

LOGIN VALIDATION RULES

For successful login:

Validate only:

- title
- URL
- dashboard controls that exist in UI_CONTEXT

Do not generate:

- error message validation
- login failure validation
- invalid credential validation

unless explicitly required.

OUTPUT REJECTION RULES

The output is INVALID if it contains:

- @pytest.mark.parametrize
- __init__
- nested functions
- invented locators
- invented validations
- contains(text(),'Login')
- contains(text(),'Add')
- contains(text(),'Ticket')
- contains(text(),'Dashboard')
- class='title' when not in UI_CONTEXT
- id='dashboardPage' when not in UI_CONTEXT
- id='ticketPage' when not in UI_CONTEXT

FINAL LOCATOR SAFETY CHECK

Before writing a locator ask:

"Can this locator be traced directly to UI_CONTEXT?"

If NO:

    # TODO: Locator not found in UI_CONTEXT

Never guess.

OUTPUT FORMAT

- Return only Python code.
- No markdown.
- No explanations.

{UI_PROMPT}

Document Content:

{test_case}
"""
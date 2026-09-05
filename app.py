from pathlib import Path
import pandas as pd
import streamlit as st
from utils.extractor import extract_test_case_text_from_file_path
from utils.generator import generate_complete_automation
from utils.locator_agent import LocatorAgent

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
UI_DIR = BASE_DIR / "ui"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
UI_DIR.mkdir(exist_ok=True)


def is_structured_test_case_output(text: str) -> bool:
    markers = [
        "## **Test Case",
        "### **Test Objective",
        "### **Preconditions",
        "| Step | Action | Expected Result |",
        "Expected Results",
        "Test Steps",
        "Test Case ID",
    ]
    return any(marker in text for marker in markers)


def load_spreadsheet_preview(file_path: str):
    suffix = Path(file_path).suffix.lower()
    if suffix == ".csv":
        try:
            df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
        except Exception:
            df = pd.read_csv(
                file_path, encoding="latin-1", dtype=str, keep_default_na=False
            )
        return [("CSV", df)]

    if suffix in {".xls", ".xlsx"}:
        try:
            excel_file = pd.ExcelFile(file_path)
            preview_tables = []
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(
                    file_path,
                    sheet_name=sheet_name,
                    dtype=str,
                    header=0,
                    keep_default_na=False,
                )
                preview_tables.append((sheet_name, df))
            return preview_tables
        except Exception:
            return None

    return None


def extract_html_content_from_ui_dir():
    """
    Read all HTML files from the UI directory and extract their content
    """
    ui_dir = UI_DIR
    
    if not ui_dir.exists():
        return ""
    
    html_files = list(ui_dir.glob("*.html")) + list(ui_dir.glob("*.htm"))
    
    if not html_files:
        return ""
    
    combined_content = []
    
    for html_file in sorted(html_files):
        try:
            content = html_file.read_text(encoding='utf-8', errors='ignore')
            
            file_info = f"\n\n{'='*80}\n"
            file_info += f"FILE: {html_file.name}\n"
            file_info += f"{'='*80}\n"
            file_info += content[:5000]
            
            combined_content.append(file_info)
            
        except Exception as ex:
            st.warning(f"Could not read {html_file.name}: {ex}")
    
    return "\n".join(combined_content)


def extract_locators_from_html_files():
    """
    Parse HTML files and extract common locators (ids, names, classes, etc.)
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        st.error("BeautifulSoup4 not installed. Run: pip install beautifulsoup4")
        return {}
    
    ui_dir = UI_DIR
    
    if not ui_dir.exists():
        return {}
    
    html_files = list(ui_dir.glob("*.html")) + list(ui_dir.glob("*.htm"))
    
    if not html_files:
        return {}
    
    locators = {
        "ids": set(),
        "names": set(),
        "classes": set(),
        "buttons": [],
        "inputs": [],
        "links": []
    }
    
    for html_file in html_files:
        try:
            content = html_file.read_text(encoding='utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract IDs
            for element in soup.find_all(id=True):
                locators["ids"].add(element.get('id'))
            
            # Extract names
            for element in soup.find_all(attrs={"name": True}):
                locators["names"].add(element.get('name'))
            
            # Extract classes
            for element in soup.find_all(class_=True):
                classes = element.get('class')
                if isinstance(classes, list):
                    locators["classes"].update(classes)
            
            # Extract buttons
            for button in soup.find_all(['button', 'input']):
                if button.name == 'input' and button.get('type') in ['button', 'submit']:
                    locators["buttons"].append({
                        'text': button.get('value', ''),
                        'id': button.get('id', ''),
                        'name': button.get('name', ''),
                        'class': ' '.join(button.get('class', []))
                    })
                elif button.name == 'button':
                    locators["buttons"].append({
                        'text': button.get_text(strip=True),
                        'id': button.get('id', ''),
                        'name': button.get('name', ''),
                        'class': ' '.join(button.get('class', []))
                    })
            
            # Extract inputs
            for input_elem in soup.find_all('input'):
                locators["inputs"].append({
                    'type': input_elem.get('type', 'text'),
                    'id': input_elem.get('id', ''),
                    'name': input_elem.get('name', ''),
                    'placeholder': input_elem.get('placeholder', '')
                })
            
            # Extract links
            for link in soup.find_all('a', href=True):
                locators["links"].append({
                    'text': link.get_text(strip=True),
                    'href': link.get('href'),
                    'id': link.get('id', ''),
                    'class': ' '.join(link.get('class', []))
                })
                
        except Exception as ex:
            st.warning(f"Could not parse {html_file.name}: {ex}")
    
    # Convert sets to lists
    locators["ids"] = list(locators["ids"])
    locators["names"] = list(locators["names"])
    locators["classes"] = list(locators["classes"])
    
    return locators


def format_locators_for_generation(locators):
    """
    Format extracted locators into a structured text format for pseudocode generation
    """
    if not locators:
        return ""
    
    formatted = "\n\n" + "="*80 + "\n"
    formatted += "EXTRACTED LOCATORS FROM SCRAPED PAGES\n"
    formatted += "="*80 + "\n\n"
    
    if locators.get("ids"):
        formatted += "**Available IDs:**\n"
        for id_val in locators["ids"][:20]:
            formatted += f"  - {id_val}\n"
        formatted += "\n"
    
    if locators.get("names"):
        formatted += "**Available Names:**\n"
        for name_val in locators["names"][:20]:
            formatted += f"  - {name_val}\n"
        formatted += "\n"
    
    if locators.get("buttons"):
        formatted += "**Available Buttons:**\n"
        for btn in locators["buttons"][:15]:
            formatted += f"  - Text: '{btn['text']}', ID: '{btn['id']}', Name: '{btn['name']}'\n"
        formatted += "\n"
    
    if locators.get("inputs"):
        formatted += "**Available Input Fields:**\n"
        for inp in locators["inputs"][:15]:
            formatted += f"  - Type: {inp['type']}, ID: '{inp['id']}', Name: '{inp['name']}', Placeholder: '{inp['placeholder']}'\n"
        formatted += "\n"
    
    if locators.get("links"):
        formatted += "**Available Links:**\n"
        for link in locators["links"][:15]:
            formatted += f"  - Text: '{link['text']}', Href: '{link['href']}', ID: '{link['id']}'\n"
        formatted += "\n"
    
    formatted += "="*80 + "\n"
    formatted += "USE THESE EXACT LOCATORS IN THE GENERATED TEST AUTOMATION CODE.\n"
    formatted += "PRIORITY: Use IDs first, then Names, then CSS classes.\n"
    formatted += "="*80 + "\n\n"
    
    return formatted


def run_locator_agent(url: str, max_pages: int = 100, username: str = None, password: str = None):
    """
    Run LocatorAgent to scrape the website and generate UI files
    """
    try:
        agent = LocatorAgent()
        
        with st.spinner(f"🔍 Scanning website: {url}..."):
            pages = agent.run(
                url=url,
                max_pages=max_pages,
                username=username,
                password=password
            )
        
        return {
            "success": True,
            "pages": pages,
            "count": len(pages),
            "message": f"Successfully scraped {len(pages)} pages"
        }
    except Exception as ex:
        return {
            "success": False,
            "error": str(ex),
            "message": f"Failed to scrape website: {ex}"
        }


st.set_page_config(page_title="Testcase Converter", layout="wide")

st.title("🖋️Testwriter")
st.write(
    "Upload a manual test case file or provide a URL to scrape. "
    "The app will generate pseudocode based on that input."
)

with st.sidebar:
    st.header("Settings")
    framework = st.selectbox("Framework", ["selenium"], index=0)
    language = st.selectbox("Language", ["python"], index=0)
    show_source = st.checkbox("Show extracted source text", value=True)
    show_locators = st.checkbox("Show extracted locators", value=True)
    
    st.header("🌐 Website Scraping")
    enable_scraping = st.checkbox("Enable website scraping", value=False)
    
    if enable_scraping:
        scrape_url = st.text_input("Website URL", placeholder="https://example.com")
        max_pages = st.number_input("Max pages to scrape", min_value=1, max_value=500, value=50)
        
        with st.expander("Login Credentials (Optional)"):
            scrape_username = st.text_input("Username", value="")
            scrape_password = st.text_input("Password", type="password", value="")

tab1, tab2 = st.tabs(["📄 Upload File", "🌐 Scrape Website"])

with tab1:
    uploaded_file = st.file_uploader(
        "Upload manual test case document",
        type=["pdf", "docx", "txt", "csv", "xlsx", "xls"],
    )

with tab2:
    st.info("Enable 'Website Scraping' in the sidebar to use this feature")
    if enable_scraping:
        st.text_input("Target URL", key="url_input", value=scrape_url if enable_scraping else "")

if st.button("🚀 Generate Pseudocode", type="primary"):
    
    source_text = ""
    spreadsheet_preview = None
    extracted_locators = {}
    
    # STEP 1: Check if website scraping is enabled
    if enable_scraping and scrape_url:
        st.info(f"Starting website scan for: {scrape_url}")
        
        scrape_result = run_locator_agent(
            url=scrape_url,
            max_pages=max_pages,
            username=scrape_username if scrape_username else None,
            password=scrape_password if scrape_password else None
        )
        
        if not scrape_result["success"]:
            st.error(scrape_result["message"])
        else:
            st.success(scrape_result["message"])
            
            with st.expander(f"📊 Scraped Pages ({scrape_result['count']})"):
                for idx, page in enumerate(scrape_result["pages"]):
                    st.write(f"{idx + 1}. {page['title']} - {page['url']}")
            
            st.info("📍 Extracting locators from freshly scraped HTML files...")
            
            html_content = extract_html_content_from_ui_dir()
            extracted_locators = extract_locators_from_html_files()
            
            locator_context = format_locators_for_generation(extracted_locators)
            
            source_text = f"""
SCRAPED WEBSITE: {scrape_url}
Total Pages: {scrape_result['count']}

{locator_context}

PAGE STRUCTURE:
"""
            
            for idx, page in enumerate(scrape_result["pages"]):
                source_text += f"\nPage {idx + 1}: {page['title']}\nURL: {page['url']}\n"
            
            source_text += f"\n\nHTML CONTENT SAMPLE:\n{html_content[:3000]}"
            
            if show_locators and extracted_locators:
                with st.expander("🎯 Extracted Locators (Fresh from HTML)"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**IDs:**")
                        st.write(extracted_locators.get("ids", [])[:10])
                        st.write("**Names:**")
                        st.write(extracted_locators.get("names", [])[:10])
                    
                    with col2:
                        st.write("**Buttons:**")
                        for btn in extracted_locators.get("buttons", [])[:5]:
                            st.write(f"- {btn['text']} (id: {btn['id']})")
                        st.write("**Inputs:**")
                        for inp in extracted_locators.get("inputs", [])[:5]:
                            st.write(f"- {inp['type']} (id: {inp['id']})")
    
    # STEP 2: If file is uploaded, use that instead
    elif uploaded_file:
        source_file_path = UPLOAD_DIR / uploaded_file.name

        with open(source_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"File uploaded: {uploaded_file.name}")
        
        try:
            source_text = extract_test_case_text_from_file_path(str(source_file_path))
            spreadsheet_preview = load_spreadsheet_preview(str(source_file_path))
        except Exception as exc:
            st.error(f"Unable to extract text from uploaded file: {exc}")
            source_text = ""
    
    else:
        st.error("⚠️ Please either upload a file OR enable website scraping with a valid URL.")
    
    # STEP 3: Generate pseudocode if source text is available
    if source_text:
        with st.spinner("🔄 Generating pseudocode with fresh locators..."):
            result = generate_complete_automation(
                source_text, 
                framework=framework, 
                language=language
            )

        if not result.get("success"):
            st.error(f"Generation failed: {result.get('error')}")
        else:
            pseudocode = result.get("pseudocode", "")

            if pseudocode:
                pseudo_file = OUTPUT_DIR / "generated_pseudocode.py"
                pseudo_file.write_text(pseudocode, encoding="utf-8")

                st.success("✅ Generation complete. Review the output below.")

                st.subheader("📝 Generated Pseudocode")
                st.code(pseudocode, language="python")

                # ✅ Download button with .py file
                if pseudocode:
                    st.download_button(
                        label="⬇️ Download Pseudocode (.py)",
                        data=pseudocode,
                        file_name="generated_test_automation.py",  # ✅ .py extension
                        mime="text/x-python",
                        key="download_pseudocode"
                    )

                # ✅ Show source text if enabled
                if show_source:
                    st.subheader("📄 Source Text")
                    if spreadsheet_preview:
                        for sheet_name, df in spreadsheet_preview:
                            st.markdown(f"**{sheet_name}**")
                            st.dataframe(df)
                    else:
                        with st.expander("View extracted or pasted source text"):
                            st.code(source_text, language="text")
                
                # ✅ Show HTML files generated by LocatorAgent
                if enable_scraping and UI_DIR.exists():
                    html_files = list(UI_DIR.glob("*.html")) + list(UI_DIR.glob("*.htm"))
                    if html_files:
                        with st.expander(f"📂 Generated HTML Files ({len(html_files)})"):
                            for html_file in sorted(html_files):
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.text(html_file.name)
                                with col2:
                                    # ✅ Allow downloading individual HTML files
                                    st.download_button(
                                        label="📥",
                                        data=html_file.read_bytes(),
                                        file_name=html_file.name,
                                        mime="text/html",
                                        key=f"download_{html_file.name}"
                                    )
    else:
        st.warning("⚠️ No source text available for pseudocode generation.")
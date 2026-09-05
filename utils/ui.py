import os
from pathlib import Path


def load_ui_context(ui_dir=None):
    """Read HTML/CSS/JS files from the ui folder and return them as prompt context."""
    ui_dir = ui_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")

    if not os.path.isdir(ui_dir):
        return ""

    sections = []
    for root, _, files in os.walk(ui_dir):
        for filename in sorted(files):
            if not filename.endswith((".html", ".css", ".js", ".json", ".txt")):
                continue

            file_path = os.path.join(root, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    content = handle.read().strip()
            except Exception:
                continue

            if not content:
                continue

            rel_path = os.path.relpath(file_path, ui_dir).replace("\\", "/")
            sections.append(f"===== UI FILE: {rel_path} =====\n{content}")

    return "\n\n".join(sections)


def get_ui_entry_url(ui_dir=None):
    """Return a file:// URL for the ui folder's index.html when available."""
    ui_dir = ui_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")

    if not os.path.isdir(ui_dir):
        return ""

    index_path = os.path.join(ui_dir, "index.html")
    if not os.path.isfile(index_path):
        return ""

    return Path(index_path).resolve().as_uri()


def extract_locators(ui_dir=None):
    """Extract simple locator suggestions from HTML files in the UI folder.

    Returns a human-readable table of element descriptors and suggested CSS/XPath
    selectors to help the prompt pick reliable locators.
    """
    try:
        from bs4 import BeautifulSoup
    except Exception:
        return "BeautifulSoup not installed. Install beautifulsoup4 to enable locator extraction."

    ui_dir = ui_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui")

    if not os.path.isdir(ui_dir):
        return ""

    entries = []
    for root, _, files in os.walk(ui_dir):
        for filename in sorted(files):
            if not filename.endswith(".html"):
                continue

            file_path = os.path.join(root, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    soup = BeautifulSoup(handle, "html.parser")
            except Exception:
                continue

            rel_path = os.path.relpath(file_path, ui_dir).replace("\\", "/")

            for el in soup.find_all(True):
                attrs = el.attrs or {}
                id_ = attrs.get("id")
                name = attrs.get("name")
                classes = " ".join(attrs.get("class", [])) if attrs.get("class") else ""
                data_test = attrs.get("data-test") or attrs.get("data-testid") or attrs.get("data-qa")
                text = (el.get_text(strip=True) or "")[:60]

                # Only include elements that have some identifying attribute or text
                if not (id_ or name or classes or data_test or text):
                    continue

                tag = el.name
                # Suggested CSS
                if id_:
                    css = f"#{id_}"
                elif classes:
                    css = ".".join(classes.split())
                elif name:
                    css = f"[name=\"{name}\"]"
                elif data_test:
                    css = f"[data-test=\"{data_test}\"]"
                else:
                    css = f"{tag}"

                # Suggested XPath
                if id_:
                    xpath = f"//{tag}[@id='{id_}']"
                elif name:
                    xpath = f"//{tag}[@name='{name}']"
                elif data_test:
                    xpath = f"//{tag}[@data-test='{data_test}']"
                elif text:
                    xpath = f"//{tag}[normalize-space(text())='{text}']"
                else:
                    xpath = f"//{tag}"

                entries.append({
                    "file": rel_path,
                    "tag": tag,
                    "id": id_,
                    "name": name,
                    "classes": classes,
                    "data_test": data_test,
                    "text": text,
                    "css": css,
                    "xpath": xpath,
                })

    if not entries:
        return "No locators found in UI HTML files."

    parts = []
    for e in entries:
        parts.append(
            f"FILE: {e['file']}\nTAG: {e['tag']}\nID: {e['id'] or ''}\nNAME: {e['name'] or ''}\nCLASS: {e['classes'] or ''}\nDATA-TEST: {e['data_test'] or ''}\nTEXT: {e['text'] or ''}\nSUGGESTED_CSS: {e['css']}\nSUGGESTED_XPATH: {e['xpath']}\n-----"
        )

    return "\n".join(parts)
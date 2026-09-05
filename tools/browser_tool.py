import re
from pathlib import Path
from urllib.parse import unquote, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def normalize_target(target):
	target = (target or "").strip()
	parsed = urlparse(target)

	if parsed.scheme in {"http", "https"}:
		return target

	if parsed.scheme == "file":
		path = unquote(parsed.path)

		if len(path) >= 3 and path[0] == "/" and path[2] == ":":
			path = path[1:]

		return Path(path).resolve().as_uri()

	if not parsed.scheme and re.fullmatch(r"(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/.*)?", target):
		return "https://" + target

	return Path(target).resolve().as_uri()


def get_driver(headless=True):
	options = Options()

	if headless:
		options.add_argument("--headless=new")

	return webdriver.Chrome(
		service=Service(ChromeDriverManager().install()),
		options=options
	)

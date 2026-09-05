import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urldefrag, urlparse

import requests

from tools.browser_tool import (
    get_driver,
    normalize_target,
)


class LocatorAgent:

    @staticmethod
    def url_key(url):
        parsed = urlparse(url)

        return (
            parsed.scheme,
            (parsed.hostname or "").lower(),
            parsed.path.rstrip("/") or "/",
            parsed.query,
        )

    @staticmethod
    def is_same_site(root, target):

        root_parts = urlparse(root)
        target_parts = urlparse(target)

        if root_parts.scheme == "file":
            return target_parts.scheme == "file"

        if root_parts.scheme in {"http", "https"}:

            root_host = (
                root_parts.hostname or ""
            ).replace("www.", "")

            target_host = (
                target_parts.hostname or ""
            ).replace("www.", "")

            return (
                target_parts.scheme
                in {"http", "https"}
                and root_host == target_host
            )

        return False

    @staticmethod
    def detect_login_fields(driver):

        username_input = None
        password_input = None
        submit_button = None

        elements = driver.find_elements(
            "css selector",
            "input, button",
        )

        for element in elements:

            try:
                tag = (
                    element.tag_name or ""
                ).lower()

                field_type = (
                    element.get_attribute("type")
                    or ""
                ).lower()

                field_id = (
                    element.get_attribute("id")
                    or ""
                ).lower()

                field_name = (
                    element.get_attribute("name")
                    or ""
                ).lower()

                if (
                    tag == "input"
                    and field_type == "password"
                ):
                    password_input = element

                if (
                    tag == "input"
                    and field_type in {"text", "email"}
                    and (
                        "user" in field_id
                        or "user" in field_name
                        or "email" in field_id
                        or "email" in field_name
                    )
                ):
                    username_input = element

                if (
                    tag == "button"
                    and "login" in
                    (element.text or "").lower()
                ):
                    submit_button = element

            except Exception:
                pass

        return (
            username_input,
            password_input,
            submit_button,
        )

    @staticmethod
    def login_if_needed(
        driver,
        username=None,
        password=None,
    ):
        try:

            (
                username_input,
                password_input,
                submit_button,
            ) = LocatorAgent.detect_login_fields(
                driver
            )

            if (
                not username_input
                or not password_input
                or not submit_button
            ):
                return False

            if (
                username is None
                and password is None
                and "saucedemo"
                in driver.current_url.lower()
            ):
                username = "standard_user"
                password = "secret_sauce"

            if not username or not password:
                return False

            username_input.clear()
            password_input.clear()

            username_input.send_keys(username)
            password_input.send_keys(password)

            submit_button.click()

            time.sleep(2)

            return True

        except Exception:
            return False

    @staticmethod
    def discover_urls(driver, current_url):

        urls = set()

        targets = [
            ("a", "href"),
            ("form", "action"),
            ("iframe", "src"),
            ("link", "href"),
            ("script", "src"),
        ]

        for tag, attribute in targets:

            try:
                elements = driver.find_elements(
                    "css selector",
                    tag,
                )

                for element in elements:

                    value = element.get_attribute(
                        attribute
                    )

                    if not value:
                        continue

                    if value.startswith(
                        (
                            "#",
                            "javascript:",
                            "mailto:",
                            "tel:",
                        )
                    ):
                        continue

                    target = urldefrag(
                        urljoin(
                            current_url,
                            value,
                        )
                    )[0]

                    urls.add(target)

            except Exception:
                pass

        html = driver.page_source or ""

        matches = re.findall(
            r'[\w\-./]+(?:\.html|\.htm|\.php|\.aspx|\.jsp|\.json|\.xml)',
            html,
            flags=re.IGNORECASE,
        )

        for match in matches:

            try:
                target = urldefrag(
                    urljoin(
                        current_url,
                        match,
                    )
                )[0]

                urls.add(target)

            except Exception:
                pass

        return sorted(urls)

    @staticmethod
    def page_filename(
        index,
        url,
        content_type="",
    ):

        parsed = urlparse(url)

        name = parsed.path.rsplit("/", 1)[-1]

        if not name:

            if "json" in content_type:
                name = "index.json"

            elif "xml" in content_type:
                name = "index.xml"

            elif "pdf" in content_type:
                name = "index.pdf"

            else:
                name = "index.html"

        name = re.sub(
            r'[<>:"/\\|?*]',
            "_",
            name,
        )

        return f"{index:03d}_{name}"

    def export_pages(self, pages):

        output_dir = Path(__file__).parent.parent.parent / "ui"

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # sitemap = []

        for index, page in enumerate(pages):

            filename = self.page_filename(
                index,
                page["url"],
                page.get(
                    "content_type",
                    "",
                ),
            )

            file_path = (
                output_dir / filename
            )

            file_path.write_bytes(
                page["content"]
            )

            # sitemap.append(
            #     {
            #         "url": page["url"],
            #         "file": filename,
            #         "content_type": page.get(
            #             "content_type",
            #             "",
            #         ),
            #     }
            # )

        # with open(
        #     "ui/sitemap.json",
        #     "w",
        #     encoding="utf-8",
        # ) as fp:

        #     json.dump(
        #         sitemap,
        #         fp,
        #         indent=4,
        #     )

        print(
            f"pages exported to {output_dir}"
        )

    def run(
        self,
        url,
        max_pages=100,
        username=None,
        password=None,
    ):

        driver = get_driver(
            headless=True
        )

        pending = [
            normalize_target(url)
        ]

        visited = set()
        pages = []

        root = pending[0]

        try:

            driver.get(root)

            self.login_if_needed(
                driver,
                username,
                password,
            )

            while (
                pending
                and len(pages)
                < max_pages
            ):

                current_url = pending.pop(
                    0
                )

                current_url = urldefrag(
                    current_url
                )[0]

                key = self.url_key(
                    current_url
                )

                if key in visited:
                    continue

                visited.add(key)

                print(
                    f"VISITING: {current_url}"
                )

                try:
                    driver.get(
                        current_url
                    )

                    time.sleep(2)

                except Exception as ex:

                    print(
                        f"FAILED: {current_url} -> {ex}"
                    )

                    continue

                links = self.discover_urls(
                    driver,
                    current_url,
                )

                print(
                    f"Found {len(links)} URLs"
                )

                content = b""
                content_type = ""

                try:

                    parsed = urlparse(
                        current_url
                    )

                    if parsed.scheme in {
                        "http",
                        "https",
                    }:

                        response = requests.get(
                            current_url,
                            timeout=30,
                            verify=False,
                        )

                        content = (
                            response.content
                        )

                        content_type = (
                            response.headers.get(
                                "Content-Type",
                                "",
                            )
                        )

                    else:

                        content = (
                            driver.page_source
                            or ""
                        ).encode("utf-8")

                        content_type = (
                            "text/html"
                        )

                except Exception:

                    content = (
                        driver.page_source
                        or ""
                    ).encode("utf-8")

                    content_type = (
                        "text/html"
                    )

                pages.append(
                    {
                        "url": current_url,
                        "title": driver.title,
                        "content": content,
                        "content_type": content_type,
                    }
                )

                for link in links:

                    if not self.is_same_site(
                        root,
                        link,
                    ):
                        continue

                    link_key = self.url_key(
                        link
                    )

                    if (
                        link_key
                        not in visited
                        and link
                        not in pending
                    ):
                        pending.append(
                            link
                        )

        finally:
            driver.quit()

        self.export_pages(
            pages
        )

        return pages
from __future__ import annotations

import base64
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Annotated, Tuple, List, Optional, Dict, Any
from enum import Enum
from urllib.parse import urlparse, parse_qs

import pandas as pd
import pytest_check as soft_assert
import requests

import pytest
import yaml

from bs4 import BeautifulSoup
from bs4.element import Comment

from src.main.utilities.helper.helper_common import HelperInterface

from playwright.sync_api import sync_playwright, Page
from core_agentic import run_configs

page:Page = None

class BrowserAction(Enum):
    CLICK = "CLICK"
    SCROLL = "SCROLL"
    REFRESH = "REFRESH"
    OPEN = "OPEN"

class HelperBrowser(HelperInterface):
    def __init__(self, pageObj:Page):
        global page
        page = pageObj
    ############# Browser specific implementations of helper functions #############

    _ga_events : List[Dict] = []  # shared across all instances

    def mock_api(self, api_key: str, mock_file: str):
        if run_configs.dryRun:
            return

        # Load URL pattern from YAML
        import os
        import yaml

        project_root = run_configs.get_project_root()

        yaml_path = os.path.join(project_root, "src", "resources", "mocking", "api_endpoints.yaml")

        try:
            with open(yaml_path, 'r') as f:
                api_config = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            error_msg = f"❌ API endpoints config not found: {yaml_path}"
            print(error_msg)
            raise

        if api_key not in api_config:
            error_msg = (
                f"❌ INVALID API KEY\n"
                f"Key '{api_key}' not found in api_endpoints.yaml.\n"
                f"Available keys: {', '.join(api_config.keys())}\n"
            )
            print(error_msg)
            raise KeyError(error_msg)

        url_pattern = api_config[api_key]
        mock_data = self.extract_mock_response_data(mock_file)

        def route_handler(route, request):
            # Only this specific API is intercepted, no need for conditional check
            display_url = request.url if len(request.url) <= 100 else request.url[:97] + "..."
            print(f"\n🎭 API MOCKED: {request.method} {display_url}")
            print(f"   Mock File: {mock_file} | Status: {mock_data.response_code}\n")

            body_to_send = mock_data.response_body if mock_data.response_body else "{}"

            route.fulfill(
                status=mock_data.response_code,
                headers=mock_data.response_headers,
                body=body_to_send
            )

        # ✅ INDUSTRY STANDARD: Only intercept the specific API pattern
        # This allows other APIs (autocomplete, analytics, etc.) to work normally
        specific_pattern = f"**/*{url_pattern}*"
        run_configs.page.route(specific_pattern, route_handler)
        print(f"✅ Mock installed: {api_key} API → {mock_file}")
        print(f"   Pattern: {specific_pattern}\n")

    def wait_until_page_load_complete(self) -> bool:
        for _ in range(30):
            time.sleep(1)
            try:
                ready_state = page.evaluate("() => document.readyState")
                if ready_state and ready_state.lower() == "complete":
                    try:
                        count = page.locator("//*[contains(@class,'indeterminate_spinner_')]").count()
                        if count == 0:
                            return True
                    except Exception as e:
                        return True
            except Exception:
                pass
        print(f"Page did not finish loading within {30} seconds")
        return False

    def navigateBack(self):
        if run_configs.dryRun == False:
            page.go_back()
            time.sleep(2)

    def fetch_response(self, api_name: str, locator: Optional[str], action: BrowserAction) -> Optional[str]:
        """
        Fetches response from network tab based on API name after performing an action.
        
        Args:
            api_name (str): API name to filter responses (checks if URL contains this)
            locator (Optional[str]): Element locator to interact with (required for CLICK and some SCROLL actions)
            action (BrowserAction): Action to perform (CLICK, SCROLL, REFRESH, OPEN)
            
        Returns:
            Optional[str]: Response text if found, None otherwise
        """
        if run_configs.dryRun:
            return None
            
        response_data = [None]  # Using list to capture response in closure
        
        def handle_response(response):
            try:
                if api_name in response.url:
                    response_data[0] = response.text()
            except Exception as e:
                print(f"Error capturing response: {e}")
                response_data[0] = "NO BODY"
        
        # Set up response listener
        page.on("response", handle_response)
        
        try:
            # Perform the action based on the enum
            if action == BrowserAction.CLICK:
                if locator:
                    self.click(locator)
                else:
                    raise ValueError("Locator is required for CLICK action")
                    
            elif action == BrowserAction.SCROLL:
                if locator:
                    self.scrollToElement(locator)
                else:
                    self.scroll_page_height()
                    
            elif action == BrowserAction.REFRESH:
                self.refreshPage()
                
            elif action == BrowserAction.OPEN:
                if locator:
                    self.open_url(locator)
                else:
                    raise ValueError("URL is required for OPEN action")
            
            # Wait for page load to complete
            self.wait_until_page_load_complete()
            
            # Wait for response to be captured with timeout
            self.wait_for_response_to_be_captured(response_data)
            
            return response_data[0]
            
        finally:
            # Remove the response listener
            try:
                page.remove_listener("response", handle_response)
            except Exception:
                pass  # Ignore errors when removing listener

    def getTextPure(self, locator):
        return page.locator(locator).inner_text()

    def scrollToElement(self, element):
        if run_configs.dryRun == False:
            page.set_default_timeout(1000)
            try:
                self.scrollUsingJS(element)
                # page.locator(element).scroll_into_view_if_needed()
            finally:
                page.set_default_timeout(15000)

    def scrollUsingJS(self, xpath: str):
        page.evaluate(
            """(xpath) => {
                const el = document.evaluate(
                    xpath,
                    document,
                    null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                    null
                ).singleNodeValue;
                if (el) {
                    el.scrollIntoView({ behavior: "smooth", block: "center" });
                }
            }""",
            xpath
        )

    def click(self, element: Annotated[str, "WebElement"]):
        # print(f"Element passed to click(): {element!r}")
        if run_configs.dryRun == False:
            try:
                if run_configs.channel == "mweb":
                    page.tap(element)
                else:
                    page.click(element)
            except Exception as e:
                page.eval_on_selector(element, "el => el.click()")
                # page.click(element, force=True)
                print(f"Element {str(element)} is Unstable, js click performed")
                # if "intercepts pointer events" in str(e) or "element is not stable" in str(e):
                #     page.click(element, force=True)
                #     print(f"Element {str(element)} is Unstable, forced click performed")
                # else:
                #     raise
            self.wait_until_page_load_complete()

    def type(self, element, text):
        # print(f"Element passed to type(): {element!r}")
        if run_configs.dryRun == False:
            if page.locator(element).is_disabled() == True:
                print(f"Element {element} is disabled, skipping type")
            else:
                time.sleep(1)
                if text is None:
                    print("No text provided to type in element: " + element + ", skipping type")
                else:
                    page.type(element, text)
                time.sleep(3)

    def set_cookie(self, name: str, value: str, domain: str):
        if run_configs.dryRun == False:
            page.context.add_cookies([{
                "name": name,
                "value": value,
                "domain": domain,
                "path": "/"
            }])
            time.sleep(2)
            self.refreshPage()


    def refreshPage(self):
        if run_configs.dryRun == False:
            page.reload()

    def scroll_page_height(self):
        """Scroll to the full height of the page."""
        if run_configs.dryRun == False:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            print("Scrolled to page height")

    def open_url(self, url: str):
        """Navigate to a specific URL."""
        if run_configs.dryRun == False:
            page.goto(url)
            self.wait_until_page_load_complete()
            print(f"Navigated to URL: {url}")

    def wait_for_response_to_be_captured(self, response_data: List, timeout: int = 10):
        """Wait for response to be captured with timeout."""
        if run_configs.dryRun == False:
            start_time = time.time()
            while response_data[0] is None and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if response_data[0] is None:
                print(f"Response not captured within {timeout} seconds")
            else:
                print("Response captured successfully")


    def verifyBrokenLink(self, locator):
        if run_configs.dryRun == False:
            elements = page.locator(locator)
            count = elements.count()
            print(f"Found {count} links")
            brokenCheck = False
            for i in range(count):
                href = elements.nth(i).get_attribute("href")
                print(href)
                if self.is_broken_link(href):
                    brokenCheck = True
                    print(f"❌ Broken link: {href}")
                else:
                    print(f"✅ Valid link: {href}")
            if brokenCheck:
                soft_assert.equal("false", "true", f"Soft Assertion Failed: Broken links found")
                # raise AssertionError(f"Broken links found")


    def is_broken_link(self, url: str) -> bool:
        CUSTOM_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        try:
            headers = {"User-Agent": CUSTOM_USER_AGENT}
            response = requests.get(url, headers=headers, timeout=15)
            print(f"URL: {url}, Status Code: {response.status_code}")
            return response.status_code >= 400
        except requests.RequestException:
            return True


    def getAllTexts(self, locator) -> list[str]:
        if run_configs.dryRun == False:
            return page.locator(locator).all_inner_texts()


    def getCount(self, locator) -> int:
        if run_configs.dryRun == False:
            return page.locator(locator).count()


    def scroll_the_element_to_top(self, element):
        page.locator(element).scroll_into_view_if_needed()
        page.evaluate(f"""
                   const el = document.evaluate("{element}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                   if (el) {{
                       el.scrollIntoView({{ block: 'start', behavior: 'smooth' }});
                   }}
               """)
        print(f"Scrolled to element: {element}")


    def scroll_to_bottom_of_page(self):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        print("Scrolled to bottom of the page")


    def run_accessibility_audit(self, html_report=None, with_screenshots=True):
        # Inject axe-core
        axe_source_url = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"
        try:
            page.add_script_tag(url=axe_source_url)
            page.wait_for_timeout(1000)  # Ensure axe-core is loaded
        except Exception as e:
            print(f"Error injecting axe-core: {e}")
            return

        # ✅ Keep rules exactly as you provided (True/False preserved)
        rules = {
            'accesskeys': {'enabled': True},
            'area-alt': {'enabled': False},
            'aria-allowed-role': {'enabled': True},
            'aria-braille-equivalent': {'enabled': False},
            'aria-conditional-attr': {'enabled': True},
            'aria-deprecated-role': {'enabled': True},
            'aria-dialog-name': {'enabled': True},
            'aria-prohibited-attr': {'enabled': True},
            'aria-roledescription': {'enabled': False},
            'aria-treeitem-name': {'enabled': True},
            'aria-text': {'enabled': True},
            'audio-caption': {'enabled': False},
            'blink': {'enabled': False},
            'duplicate-id': {'enabled': False},
            'empty-heading': {'enabled': True},
            'frame-focusable-content': {'enabled': False},
            'frame-title-unique': {'enabled': False},
            'heading-order': {'enabled': True},
            'html-xml-lang-mismatch': {'enabled': True},
            'identical-links-same-purpose': {'enabled': True},
            'image-redundant-alt': {'enabled': True},
            'input-button-name': {'enabled': True},
            'label-content-name-mismatch': {'enabled': True},
            'landmark-one-main': {'enabled': True},
            'link-in-text-block': {'enabled': True},
            'marquee': {'enabled': False},
            'meta-viewport': {'enabled': True},
            'nested-interactive': {'enabled': False},
            'no-autoplay-audio': {'enabled': False},
            'role-img-alt': {'enabled': False},
            'scrollable-region-focusable': {'enabled': False},
            'select-name': {'enabled': True},
            'server-side-image-map': {'enabled': False},
            'skip-link': {'enabled': True},
            'svg-img-alt': {'enabled': False},
            'tabindex': {'enabled': True},
            'table-duplicate-name': {'enabled': True},
            'table-fake-caption': {'enabled': True},
            'target-size': {'enabled': True},
            'td-has-header': {'enabled': True}
        }

        # Run axe-core with additional configs similar to Lighthouse
        try:
            results = page.evaluate(f"""
                   async () => {{
                       if (typeof axe === 'undefined') {{
                           throw new Error('axe-core not loaded');
                       }}
                       // Validate rules before running
                       const availableRules = axe.getRules().map(rule => rule.ruleId);
                       const configuredRules = {json.dumps(list(rules.keys()))};
                       const invalidRules = configuredRules.filter(rule => !availableRules.includes(rule));
                       if (invalidRules.length > 0) {{
                           throw new Error('Invalid rules detected: ' + invalidRules.join(', '));
                       }}
                       const results = await axe.run(document, {{
                           reporter: 'v2',
                           elementRef: true,
                           runOnly: {{
                               type: 'tag',
                               values: ['wcag2a', 'wcag2aa']
                           }},
                           resultTypes: ['violations', 'inapplicable'],
                           rules: {json.dumps(rules)}
                       }});
                       document.documentElement.scrollTop = 0;
                       return results;
                   }}
               """)
        except Exception as e:
            print(f"Error running axe-core audit: {e}")
            return

        violations = results.get("violations", [])

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        timestamp_display = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- Auto-generate filenames based on page title if not provided ---
        page_title = page.title() or "page"
        safe_title = re.sub(r"[^A-Za-z0-9_-]+", "_", page_title)

        if not html_report:
            html_report = f"a11y_{safe_title}_{timestamp}.html"

        # --- Console summary ---
        if not violations:
            print(f"✅ No accessibility violations found!")
        else:
            print(f"⚠️ Found {len(violations)} accessibility violations:")
            by_impact = {}
            for v in violations:
                by_impact.setdefault(v["impact"], []).append(v)
            for impact, items in by_impact.items():
                print(f"  {impact.upper()}: {len(items)} issues")

        # --- HTML Report ---
        rows = []
        for v in violations:
            nodes_html = []
            for i, node in enumerate(v.get("nodes", [])):
                targets = ", ".join(
                    [" ".join(t) if isinstance(t, list) else str(t) for t in node.get("target", [])]
                )
                summary = (node.get("failureSummary") or "").replace("\n", " ")

                screenshot_html = ""
                if with_screenshots and targets:
                    try:
                        element_handle = page.query_selector(targets)
                        if element_handle:
                            screenshot_bytes = element_handle.screenshot()
                            b64_img = base64.b64encode(screenshot_bytes).decode("utf-8")
                            screenshot_html = f'<br><img src="data:image/png;base64,{b64_img}" style="max-width:400px;border:1px solid #ccc;">'
                    except Exception as e:
                        screenshot_html = f"<br><em>Screenshot failed: {e}</em>"

                node_block = f"<div><strong>{targets}</strong><br>{summary}{screenshot_html}</div>"
                nodes_html.append(node_block)

            rows.append(
                f"<tr><td>{v['impact']}</td><td>{v['id']}</td><td><a href='{v['helpUrl']}' target='_blank'>{v['help']}</a></td><td>{''.join(nodes_html)}</td></tr>"
            )

        if not violations:
            html_body = "<p>No accessibility violations found.</p>"
        else:
            rows_html = "".join(rows)
            html_body = (
                "<table border='1' cellspacing='0' cellpadding='5'>"
                "<thead><tr><th>Impact</th><th>Rule</th><th>Help</th><th>Affected Nodes</th></tr></thead>"
                f"<tbody>{rows_html}</tbody>"
                "</table>"
            )

        full_html = f"""
           <html>
           <head>
               <meta charset='utf-8'>
               <title>Accessibility Report - {page_title}</title>
               <style>
                   body {{ font-family: Arial, sans-serif; padding: 20px; }}
                   table {{ border-collapse: collapse; width: 100%; }}
                   th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
                   th {{ background: #f2f2f2; }}
               </style>
           </head>
           <body>
               <h1>Accessibility Report</h1>
               <div class="timestamp">Report generated: {timestamp_display}</div>
               <h2>{page_title}</h2>
               {html_body}
           </body>
           </html>
           """

        try:
            with open(html_report, "w", encoding="utf-8") as hf:
                hf.write(full_html)
            print(f"📄 HTML report saved: {html_report} [generated at {timestamp_display}]")
        except Exception as e:
            print(f"Error saving HTML report: {e}")


    def get_performance_metrics(self):
        """
        Extracts performance metrics (FCP, LCP, CLS) from the given page.
        """
        metrics = {}

        # First Contentful Paint (FCP)
        metrics['FCP'] = page.evaluate('''() => {
                       const paintEntries = performance.getEntriesByType('paint');
                       const fcpEntry = paintEntries.find(e => e.name === 'first-contentful-paint');
                       return fcpEntry ? fcpEntry.startTime : null;
                   }''')

        # Largest Contentful Paint (LCP)
        metrics['LCP'] = page.evaluate('''() => {
                       const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                       return lcpEntries.length > 0 ? lcpEntries[lcpEntries.length - 1].startTime : null;
                   }''')

        # Cumulative Layout Shift (CLS)
        metrics['CLS'] = page.evaluate('''() => {
                       const shiftEntries = performance.getEntriesByType('layout-shift');
                       return shiftEntries.reduce((acc, entry) => {
                           if (!entry.hadRecentInput) {
                               acc += entry.value;
                           }
                           return acc;
                       }, 0);
                   }''')

        return metrics


    def compare_performance_metrics(self, prod_metrics, pp_metrics, tolerance):

        pages = ['Home Page', 'Search Result Page']

        for page in pages:
            for metric in ['FCP', 'LCP', 'CLS']:
                prod_value = prod_metrics.get(page, {}).get(metric)
                pp_value = pp_metrics.get(page, {}).get(metric)

                if prod_value is None or pp_value is None:
                    pytest.fail(f"Missing value for {page} - {metric}")

                # Assert: pp should not be more than 10% worse than prod
                assert pp_value <= prod_value * (1 + tolerance), (
                    f"{page} - {metric} degraded beyond tolerance: "
                    f"pp={pp_value:.2f}, prod={prod_value:.2f}, max_allowed={prod_value * (1 + tolerance):.2f}"
                )


    def is_locator_present(self, element):
        count = page.locator(element).count()
        return count > 0


    def validate_ga_event(self, stExpected: list, dyExpected: dict, eventLog: str):
        if run_configs.dryRun == False:
            url = ""
            body = {}
            body["stExpected"] = stExpected
            body["dyExpected"] = dyExpected
            body["eventLog"] = eventLog
            print(f"Validating GA event with body: {body}")
            response = self.trigger_api_request(url, method="POST", json_data=body)
            return response


    def convert_ga_json_to_log_format(self, ga_event_json: str):
        if run_configs.dryRun == False:
            try:
                event_data = json.loads(ga_event_json)
                from datetime import datetime
                timestamp = datetime.now().strftime("%m-%d %H:%M:%S.%f")[:-3]
                event_name = event_data.get("event", "UNKNOWN_EVENT")
                bundle_items = []
                for key, value in event_data.items():
                    if key != "event":
                        bundle_items.append(f"{key}={value}")
                bundle_str = ", ".join(bundle_items)
                log_format = f"{timestamp}  3299  3299 I ANALYTICS EVENT - GOOGLE ANALYTICS: GA -> {event_name} : Bundle[{{{bundle_str}}}]"
                return log_format
            except json.JSONDecodeError:
                return f"Error: Invalid JSON format - {ga_event_json}"
            except Exception as e:
                return f"Error: Failed to convert JSON to log format - {str(e)}"


    def validateEvents(self, capturedGAEvents, stExpected: list, dyExpected: dict):
        if run_configs.dryRun == False:
            if not capturedGAEvents:
                print("No GA events captured.")
                return
            stExpected = stExpected
            dyExpected = {
                "userType": dyExpected
            }
            for event in capturedGAEvents:
                log_format_event = self.convert_ga_json_to_log_format(event)
                print(f"Log format: {log_format_event}")
                response = self.validate_ga_event(stExpected, dyExpected, event)
                if response:
                    print(f"Validation response: {response}")
                    assert response.get("status") == "success", f"Validation failed for event: {event}"
                    response_data = response.get("data", {})
                    assert len(response_data[
                                        'ErrorMessageList']) == 0, f"Validation errors found: {response_data['ErrorMessageList']}"


    def clickAndVerifyGAEvent(self, locators: str, stExpected: list, dyExpected: dict):
        if run_configs.dryRun == False:
            if run_configs.eventValidation is False:
                self.click(locators)
                time.sleep(2)
            else:
                capturedGAEventsAfterClick = self.fetch_ga_events_console_data_layer(page)
                self.click(locators)
                time.sleep(2)
                print(f"Total GA events captured after click: {len(capturedGAEventsAfterClick)}")
                print("GA Events: ", capturedGAEventsAfterClick)
                print("#######################################################")
                print("Sample List: ", run_configs.sampleList)
                if len(capturedGAEventsAfterClick) == 0:
                    print("No GA events captured after click.")
                    return
                for event in capturedGAEventsAfterClick:
                    print(f"Event: {event}")
                self.validateEvents(capturedGAEventsAfterClick, stExpected, dyExpected)


    def fetch_ga_events_console_data_layer(self):
        if run_configs.dryRun == False:
            capturedGAEvents = []
            self.wait_until_page_load_complete()

            def handle_console_msg(msg):
                if msg.text.startswith("GA_EVENT:"):
                    ga_event_json = msg.text[len("GA_EVENT:"):]
                    if ga_event_json.strip().startswith(
                            "{") and '"event"' in ga_event_json and not "Error stringifying event" in ga_event_json:
                        if not re.search(r'"event"\s*:\s*"gtm[^"\\}]*"', ga_event_json):
                            capturedGAEvents.append(ga_event_json)
                            run_configs.sampleList.append(ga_event_json)

            page.on("console", handle_console_msg)
            page.evaluate("""() => {
               // For standard Google Analytics (ga.js)
               window.dataLayer = window.dataLayer || [];
               const originalPush = window.dataLayer.push;
               window.dataLayer.push = function(event) {
                   try {
                       console.log("GA_EVENT:" + JSON.stringify(event));
                   } catch (e) {
                       console.log("GA_EVENT: Error stringifying event", e);
                   }
                   return originalPush.apply(this, arguments);
               };
               window.gtag = window.gtag || function() {
                   console.log("GA_EVENT:" + JSON.stringify(arguments));
                   if (Array.isArray(window.dataLayer)) {
                       window.dataLayer.push(arguments);
                   }
               };
               if (typeof window.google_tag_manager !== 'undefined') {
                   console.log("GA_EVENT: Google Tag Manager detected");
               }
               console.log("GA_EVENT: Tracking override installed");
           }""")
            return capturedGAEvents

    def clearText(self, element: Annotated[str, "Locator of the WebElement"]):
        if run_configs.dryRun == False:
            try:
                self.scrollToElement(element)
                page.locator(element).fill("")
                print(f"Cleared text in element: {element}")
            except Exception as e:
                print(f"Error clearing text in element {element}: {e}")


    def _inject_data_layer_hook(self):
        """
        Inject JavaScript before any page loads to capture GA events.
        """
        page.context.add_init_script("""
            window.dataLayer = window.dataLayer || [];
            const originalPush = window.dataLayer.push;
            window.dataLayer.push = function() {
                const args = Array.from(arguments);
                window.sendGaEventToPython(args);
                return originalPush.apply(window.dataLayer, args);
            };

            if (window.dataLayer.length > 0) {
                window.dataLayer.forEach(function(event) {
                    window.sendGaEventToPython(event);
                });
            }
        """)


    def _expose_event_handler(self):
        """
        Expose a Python function to handle GA events.
        """
        def handle_ga_event(event_list):
            for event in event_list:
                # Skip if any key starts with "gtm"
                if any(key.startswith("gtm") for key in event):
                    continue

                # Skip if 'event' value contains "gtm"
                if "event" in event and isinstance(event["event"], str) and "gtm" in event["event"].lower():
                    continue

                # Store only meaningful events
                # print("Meaningful GA Event captured:", event)
                self._ga_events.append(event)

        page.context.expose_function("sendGaEventToPython", handle_ga_event)


    @classmethod
    def _add_event(cls, event: Dict):
        """
        Internal helper to safely append events to the shared event store.
        """
        cls._ga_events.append(event)


    @classmethod
    def get_all_events(cls) -> List[Dict]:
        """
        Retrieve all captured GA events.
        """
        return cls._ga_events.copy()


    @classmethod
    def clear_events(cls):
        """
        Clear all stored GA events.
        """
        cls._ga_events.clear()


    def _setup_listener(self):
        """
        Set up the listener by exposing the handler and injecting JS.
        """
        self._expose_event_handler()
        self._inject_data_layer_hook()

    def build_ga_validation_prompt(self , expected_yaml_path: str, actual_events: list, page_name="home_page", user_type="guest_user"):
        """
        Build an LLM prompt to validate GA events against YAML config.

        Args:
            expected_yaml_path (str): Path to YAML file containing expected GA events.
            actual_events (list): List of GA events captured during test execution.
            page_name (str): Page name key in YAML (default = 'home_page').
            user_type (str): User type key in YAML (default = 'guest_user').

        Returns:
            str: The formatted prompt to send to the LLM.
        """

        # Load expected GA config from YAML
        with open(expected_yaml_path, "r") as f:
            expected_data = yaml.safe_load(f)

        # Navigate to the correct nested section
        try:
            expected_section = expected_data[page_name][user_type]
        except KeyError:
            raise ValueError(f"Invalid YAML structure. Expected keys: {page_name} -> {user_type}")

        # Extract the event names that actually got triggered (unique)
        triggered_event_names = {event.get("event") for event in actual_events if "event" in event}

        # Filter YAML to include only those events that got triggered
        filtered_expected = {
            event_name: event_list
            for event_name, event_list in expected_section.items()
            if event_name in triggered_event_names
        }

        # Convert YAML and actual data to clean JSON for the LLM prompt
        expected_json = json.dumps(filtered_expected, indent=2, ensure_ascii=False)
        actual_json = json.dumps(actual_events, indent=2, ensure_ascii=False)

        # Construct the validation prompt
        prompt = f"""
            You are an expert QA automation validator for Google Analytics (GA) events.
        
            ### Input Data
            You are given two datasets:
            1. **Expected GA Config (from YAML)** — a full set of all possible GA events for the Home Page Guest User.
            2. **Actual GA Events (from runtime)** — a list of GA events captured during the current test.
        
            ### Your Task
            - Match and validate each event in the "actual" list using the `event` field.
            - Only compare events that appear in both datasets (ignore extra YAML entries).
            - For each matched event:
              - Compare key-value pairs of each actual event against each expected entry (list of possible expected variants).
              - Mark ✅ if the actual event fully matches one of the expected entries.
              - Mark ⚠️ if some values differ (show expected vs actual).
              - Mark ❌ if a key is missing in actual.
            - Treat the following equivalences:
              - `null` in YAML == `None` in Python
              - `<any_valid_location>` in YAML == any real-world location string (like "(Mumbai,MH)" or "(Delhi,DL)")
            - Return a structured JSON-like report with:
              - event_name
              - match_found (True/False)
              - matched_variant_index (if matched)
              - mismatched_keys (with expected vs actual)
              - summary (total validated, passed, failed)
        
            ---
        
            ### Expected GA Config (Filtered from YAML)
            {expected_json}
        
            ### Actual GA Events (Captured from runtime)
            {actual_json}
        
            Now validate and generate a detailed JSON validation report.
            """
        return prompt

    _request_payloads: List[str] = []

    def fetch_request_payloads(self, api_name: str, locator: str = None, action: str = None, wait_timeout: int = 5000) -> list:
        """
        Fetch all request payloads for requests whose URL contains `api_name`.
        Supports GET and POST requests. Performs browser action if provided
        and waits for network and page load to complete.
        """
        self._request_payloads.clear()

        # Listener for all requests
        def on_request(request):
            if api_name in request.url:
                payload = None
                # Try JSON payload first (for fetch/XHR)
                try:
                    payload = request.post_data_json
                except Exception:
                    payload = None
                # Fallback to raw post_data
                if payload is None and request.post_data:
                    payload = request.post_data
                # For GET requests, parse query params
                elif request.method.upper() == "GET" and "?" in request.url:
                    parsed_url = urlparse(request.url)
                    payload = dict(parse_qs(parsed_url.query))

                self._request_payloads.append(payload)
                print(f"Captured request to {request.url} with payload: {payload}")

        page.on("request", on_request)

        # Perform the browser action
        if action == BrowserAction.CLICK and locator:
            page.locator(locator).click()
        elif action == BrowserAction.SCROLL and locator:
            page.locator(locator).scroll_into_view_if_needed()
        elif action == BrowserAction.REFRESH:
            page.reload()

        # Wait for the page to load completely
        try:
            page.wait_for_load_state("load", timeout=wait_timeout)
            page.wait_for_load_state("networkidle", timeout=wait_timeout)
        except TimeoutError:
            # Even if page/network does not idle, continue
            print("Timeout waiting for page/network to load completely.")

        # Extra buffer to ensure late network requests are captured
        page.wait_for_timeout(1500)

        return self._request_payloads

    def extract_mock_response_data(self, mock_file_name: str) -> MockResponseToSend:
        import os

        project_root = run_configs.get_project_root()

        lob = run_configs.lob
        # Get LOB from run_configs
        lob = run_configs.lob  # e.g., "rails", "ferry", etc.

        # Construct full path to mock file in resources folder
        # Path: src/resources/mocking/lob/{lob}/{filename}
        mock_file_path = os.path.join(
            project_root,
            "src", "resources", "mocking", "lob", lob,
            mock_file_name
        )

        try:
            with open(mock_file_path, 'r') as f:
                mock_response = json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Mock file not found: {mock_file_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"⚠️ Invalid JSON in mock file: {mock_file_path}")
            print(f"Error: {e}")
            raise

        mock_response_to_send = MockResponseToSend()

        response_code = mock_response.get("statusCode")
        if response_code is not None:
            try:
                mock_response_to_send.response_code = int(response_code)
            except (ValueError, TypeError):
                print("⚠️ Status code format invalid in mockResponse! Using default: 200")

        if isinstance(mock_response.get("headers"), dict):
            mock_response_to_send.response_headers = mock_response["headers"]

        body = mock_response.get("body")
        if body is not None:
            try:
                if isinstance(body, (dict, list)):
                    mock_response_to_send.response_body = json.dumps(body)
                else:
                    mock_response_to_send.response_body = str(body)
            except Exception as e:
                print(f"⚠️ Unable to parse mock body: {e}")
                mock_response_to_send.response_body = "{}"

        return mock_response_to_send

    def take_screenshot_as_base64(self) -> str:
        time.sleep(2)
        screenshot_bytes = page.screenshot(full_page=False)
        val = base64.b64encode(screenshot_bytes).decode('utf-8')
        return val

    def get_relative_xpath(self, locator_description: str, sanitized_html: str) -> str:
        system_prompt = """
        You are an expert XPath engineer. Your task is to generate relative XPath expressions that uniquely and reliably identify target elements in HTML content. Follow all rules exactly—no exceptions.

        CRITICAL RULES

        Rule 1 – Relative XPath Only
        - XPath must always start with // (double slash).
        - Never start with / (single slash).
        - Never use absolute paths.

        Rule 2 – Tag Name Must Be *
        - Always use * as the tag name in all parts of the XPath.
        - Never use specific HTML tags like div, span, li, img, p, etc.
        - Never leave the tag name empty after //.
        - This applies to:
          - Main selectors: //*[…] ✅, //div[…] ❌, //[…] ❌
          - Ancestor/descendant selectors: ancestor::*[…] ✅, ancestor::div[…] ❌
          - Child selectors: /*[…] ✅, /div[…] ❌

        Examples:
        ❌ //div[contains(@class,'tupleWrapper')]
        ✅ //*[contains(@class,'tupleWrapper')]

        ❌ ancestor::li[contains(@class,'item')]
        ✅ ancestor::*[contains(@class,'item')]

        Rule 3 – Class Attribute Handling
        - When referencing @class, identify the FIRST class name in the class attribute value.
        - From that FIRST class name, use only the portion up to (and including) the first underscore _.
        - If the first class name has no underscore, use the complete first class name.
        - Always use contains()—never exact matches (=).
        Examples:
        ❌ //*[@class='listItem___f7c71e lineLength1___b14900']
        ❌ //*[contains(@class,'lineLength1_')]
        ✅ //*[contains(@class,'listItem_')]

        Rule 4 – Indexing Syntax [EXTREMELY IMPORTANT]
        - Always apply indexing when an XPath could potentially match multiple elements.
        - MANDATORY: Enclose the COMPLETE XPath expression in parentheses before applying ANY index.
        - The format must ALWAYS be: (complete_xpath_expression)[index]
        - Never apply an index directly to any part of the XPath without wrapping the entire expression.
        - This applies to ALL XPath expressions, regardless of complexity or length.

        Examples:
        ❌ //*[contains(@class,'srcDestWrapper_')][2]
        ✅ (//*[contains(@class,'srcDestWrapper_')])[2]

        Rule 5 – Text Content Handling
        - Always use normalize-space(.) instead of normalize-space(text()).
        - Never use direct value, always use contains for normalize-space(.).

        Examples:
        ❌ //*[normalize-space(text())='Search']
        ✅ //*[contains(normalize-space(.),'Search')]

        ATTRIBUTE PREFERENCE FOR LOCATOR CONSTRUCTION
        1. @data-autoid
        2. @class (following Rule 3)
        3. @id (when available and meaningful)
        4. Text-based locators (following Rule 5)

        Rule 6 – No Forced Construction
        - If it is not possible to construct a valid XPath following all rules above for the given HTML, return None.
        - Do not make assumptions or force-create an XPath if the required attributes or text are unavailable.

        Rule 7 – Parameter Placeholder Integrity [ABSOLUTE PROHIBITION]
            - Dynamic locators can accept parameters for:
              - Index values (e.g., [{str(position)}])
              - Inner text values following Rule 5 (e.g., contains(normalize-space(.),'{text}'))
            - ABSOLUTE PROHIBITION: 
              - Parameter substitution into ANY attribute is strictly forbidden.
              - This includes ALL attributes: @class, @id, @data-, @aria-, @style, @href, @src, etc.
              - No exceptions regardless of how unique or reliable the attribute appears.
              - Attribute values are static strings set by developers - never substitute into them.
            - Parameter placeholders must remain EXACTLY as provided in the function signature.
            - NEVER modify, wrap, or alter parameter names with additional characters like parentheses, quotes, or any other symbols.
            - Index parameter handling: '{position}' → becomes '{str(position)}'
            - Text parameter handling: '{text}' → remains as '{text}'
            - FORBIDDEN modifications: 
              ❌ '({name})' → wrapping with parentheses is FORBIDDEN 
              ❌ '"{name}"' → wrapping with quotes is FORBIDDEN 
              ❌ '{name}_suffix' → modifying parameter name is FORBIDDEN
            - CRITICAL ENFORCEMENT:
              - If the only way to uniquely identify an element is through attribute substitution, return None.
              - Never compromise this rule for convenience or perceived reliability.
              - Always use text-based locators with normalize-space(.) and contains() for dynamic content.
            - VIOLATION EXAMPLES (NEVER DO THIS): 
              ❌ f"//[@attribute='{abc_xyz}']" 
              ❌ f"//[@attribute='abc_{text}']" 
              ❌ f"//*[contains(@class,'{class_name}')]"
            - CORRECT ALTERNATIVES: 
              ✅ f"(//[contains(@class,'abc_') and contains(normalize-space(.),'{text}')])[{str(position)}]" 
              ✅ f"//[contains(normalize-space(.),'{text}')]"
            **This rule has zero tolerance for violations - attribute substitution is absolutely forbidden.**
            - UNIVERSAL VIOLATION PATTERN RECOGNITION:
                - Any pattern containing: @[attribute_name]='{parameter}' or @[attribute_name]='{anything_with_parameter}'
                - Any pattern containing: contains(@[attribute], '{parameter}')  
                - Any pattern containing parameters within square brackets alongside @ symbols
                - Any mathematical operations or string manipulations on parameters
            - ENFORCEMENT: If you recognize any of these patterns during construction, immediately return None.

        Rule 8 – Comprehensive Attribute Parameter Prohibition
            - Parameter substitution is ABSOLUTELY FORBIDDEN in any attribute predicate.
            - This prohibition applies to ALL attributes without exception, including but not limited to any attribute starting with @.
            - If any part of your XPath construction process involves placing a parameter inside square brackets with an @ symbol, immediately stop and return None.
            - No workarounds, no exceptions, no "special cases" - attribute substitution is never allowed.

        Rule 9 – Parameter Integrity
            - Parameters must be used in their exact original form without any modifications.
            - No mathematical operations, string concatenations, or transformations on parameters.
            - The only allowed transformation is str() wrapper for non-string parameters in f-string formatting.
            - If the locator logic requires parameter modification to work, return None instead.

        TECHNICAL REQUIREMENTS
        - XPath must be syntactically correct.
        - Use only allowed patterns from the rules above.
        - Ensure reliability even if HTML structure changes.
        - Output must be:
          - Plain text only (no markdown, quotes, or backticks).
          - In Python f-string format for dynamic locators.
          - Parameters must remain placeholders (e.g., {parameter_name}).
          - Convert non-string parameters to str() in substitution.

        Dynamic Locator(Locator which intakes parameters) Formatting
        - String parameters → insert directly.
        - Non-string parameters → wrap with str().

        Example – Dynamic:
        def filter_chip_by_text(text: str, position: int = 1):
            '''Filter options for ferry types like Economy, Standard, etc.'''
        Output:
        f"(//*[contains(@class,'filterChip_') and normalize-space(.)='{text}'])[{str(position)}]"

        Static Locator(Locators which do not intake parameters) Formatting
        - Should point to one specific targetted element ONLY
        - Mandatorily follow Rule 4 and apply indexing to achieve the same

        Example – Static:
        def search_ferries_button(self):
            '''Primary red button to initiate ferry search'''
        Output:
        "//*[contains(@class,'searchBtn_')]"

        MANDATORY VIOLATION DETECTION - STOP AND RETURN None IF ANY DETECTED:
            - Parameter appears anywhere inside square brackets with @ symbol
            - Any mathematical operation on parameters  
            - Any attribute contains a parameter in any form
            - XPath construction requires parameter modification to be unique
            - Multiple violation patterns combined in single expression

        VALIDATION CHECKLIST FOR VALID XPATH:
            - Starts with // ✅
            - All tags are * ✅  
            - Parameters only in: text content with normalize-space() OR indexing position ✅
            - No @ symbols near parameters ✅
            - Indexing format: (complete_xpath)[index] ✅

        MOST CRITICAL RULES: 
        - For static locators, avoid text-based locator construction whenever possible as they are flaky.


        Do not explain. Do not output anything except the XPath expression in the correct format or None if construction is not possible.
        """
        user_prompt = f"\nLocator Description: {locator_description}\nHTML Content: {sanitized_html}"
        # print("System prompt: " + system_prompt)
        print("User prompt: " + user_prompt)
        locator_from_ai = self.setupLLM(systemPrompt=system_prompt, userPrompt=user_prompt)
        print("Raw locator from AI: " + locator_from_ai)
        locator_from_ai = locator_from_ai.strip()
        locator_from_ai = locator_from_ai.replace("/[", "/*[")  # Fix any potential syntax issues
        locator_from_ai = locator_from_ai.replace("::[", "::*[")  # Fix any potential syntax issues
        if locator_from_ai.startswith("\""):
            locator_from_ai = locator_from_ai[1:-1]
        if locator_from_ai.startswith("f"):
            locator_from_ai = locator_from_ai[2:-1]  # Remove f-string formatting
        print("Locator from AI after formatting: " + locator_from_ai)
        return locator_from_ai

    def get_section_outer_html(self, xpath_list: list) -> str:
        global page
        result = ""
        for xpath in xpath_list:
            elements = page.query_selector_all(xpath)
            for element in elements:
                outer_html = element.evaluate("el => el.outerHTML")
                result += outer_html + "\n"
        return result.strip()

    def locatorCount(self, element:str):
        return page.locator(element).count()

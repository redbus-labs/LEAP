import os
from abc import abstractmethod

import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Annotated, Any

import pandas as pd
import pytest
import pytest_check as soft_assert
from bs4 import BeautifulSoup, Comment

from core_agentic import run_configs

from botocore.config import Config
from jsonpath_ng import parse

import requests
import json

import re

from core_agentic.run_configs import LLM_MODEL
from src.main.utilities.helper.helper_description import HelperAgent

import inspect

llmResponseTime = []
llmTokens = []

class BrowserAction(Enum):
    CLICK = "CLICK"
    SCROLL = "SCROLL"
    REFRESH = "REFRESH"
    OPEN = "OPEN"


class HelperInterface(HelperAgent):
    ############# Browser specific implementations of helper functions #############

    _ga_events: List[Dict] = []  # shared across all instances

    @abstractmethod
    def mock_api(self, api_key: str, mock_file: str):
        pass

    def convert_intellij_json_path_to_right_format(self, custom_path: str) -> str:
        if custom_path.startswith("/"):
            path_components = custom_path.split("/")
            correct_json_path = "$"
            for component in path_components:
                if component != "":
                    try:
                        # Check if the component is an integer
                        int(component)
                        correct_json_path += f"[{component}]"
                    except ValueError:
                        # Handle components starting with '*'
                        if component.startswith("*"):
                            component = component[1:]
                        correct_json_path += f".{component}"
            return correct_json_path
        else:
            return custom_path

    def extractJsonValueBasedOnPath(self, json_data: str, json_path: str) -> str:
        json_path = self.convert_intellij_json_path_to_right_format(json_path)
        jsonpath_expr = parse(json_path)
        response_json = None
        try:
            response_json = json.loads(json_data)
        except Exception as e:
            print(f"Error parsing JSON data: {e}")
            print("JSON Data: \n", json_data)
        matches = [match.value for match in jsonpath_expr.find(response_json)]
        # setupLLM(model="openai", )
        return matches[0] if matches else None

    def calculate_total_token_count(self, val, tokenPathList):
        total = 0
        for totalTokenPath in tokenPathList:
            token_str = self.extractJsonValueBasedOnPath(val, self.convert_intellij_json_path_to_right_format(totalTokenPath))
            if token_str is not None:
                try:
                    total += int(token_str)
                except ValueError:
                    print(f"Could not convert '{token_str}' to integer.")
        return total

    def split_on_last(self, s: str, sep: str):
        if sep not in s:
            return [s]  # if separator not found, return the string as is
        return s.rsplit(sep, 1)

    def visualValidation(self, base64Image: str, userPrompt: str="") -> str:
        systemPrompt = """
        You are a helpful assistant. Respond with true/false. Then use a `|` symbol and provide detailed reasoning why you said true/false. You should exactly follow this format and do not output anything else. You should only provide one output post completing your reasoning

        CRITICAL DATE VALIDATION RULE (Applicable only for date related validations):
            VALIDATE ONLY: Date number + Month (any format) IGNORE: Year, date format, time (unless user explicitly requests)
            - POSITIVE ASSERTION (True) IF:
                - Correct date number visible
                - Correct month visible (abbreviated/full/numeric - any format OK)
            - NEGATIVE ASSERTION (False) ONLY IF:
                - Wrong date number OR wrong month OR missing date/month
            FORBIDDEN: Failing assertions due to year differences or format variations
            Example:
                Expected "7 August 2025" → Display "07 Aug" = ✅ POSITIVE,
                Expected "07 Sept 2025" → Display "7 September" = ✅ POSITIVE

        Rules for Position-Based Validation:
        * Direct Relationship Required
            - When validating relative position (e.g., verify if X is below Y), the result is True only if X is directly below Y.
            - If X is below some other element (e.g., Z) that happens to be in the same section as Y, the result is False.
            - Always validate strictly against the specified reference element.
        * Above/Below Validity
            - When the user has explicitly specified an above or below validation, the condition is valid as long as the element is vertically above or vertically below the reference element.
            - In this case, horizontal alignment (left, center, right) is irrelevant and should be ignored.        

        """ + "\nToday's date for your reference: " + datetime.now().strftime("%d-%B-%Y") + ".\n\n"
        # global llm
        # temp = llm
        # llm = "openai"
        # print(systemPrompt)
        # print(userPrompt)
        # print("Base64 Image: ", base64Image)
        val = self.setupLLM(systemPrompt=systemPrompt, userPrompt=userPrompt, image=base64Image)
        # llm = temp
        return val

    def wait_pause(self, seconds: Annotated[int, "Number of seconds to pause/wait (default 5)"]):
        time.sleep(seconds)

    def assertionVisual(self, element, assertion):
        time.sleep(3)
        if run_configs.dryRun == False:
            if element is not None:
                try:
                    self.scrollToElement(element)
                except Exception as e:
                    for xpath in run_configs.SECTION_AUTO_ID:
                        try:
                            self.scrollToElement(xpath)
                        except Exception as e:
                            pass
                    # print(f"Error scrolling to element {element}: {e}, continuing with assertion")
            else:
                for xpath in run_configs.SECTION_AUTO_ID:
                    try:
                        self.scrollToElement(xpath)
                    except Exception as e:
                        pass
                        # print(f"Error scrolling to element {xpath}: {e}, continuing with assertion")
            check = self.visualValidation(self.take_screenshot_as_base64(), assertion)
            print("x-x-x-x-x-x-x-x-x-x-x-x-x-x-x")
            print("Assertion: " + assertion)
            print(check)
            print("x-x-x-x-x-x-x-x-x-x-x-x-x-x-x")
            actualAssertion: str = check.split("|")[0].strip().lower()
            soft_assert.equal(actualAssertion, "true", f"Soft Assertion Failed: {assertion}")

    def askLLMAboutImage(self, base64Image: str) -> str:
        systemPrompt = "You are given a screenshot of a web application. Describe the image in detail"
        return self.setupLLM(systemPrompt=systemPrompt, userPrompt="", image=base64Image)

    def setupLLM(self,
                 provider: run_configs.LLM_Provider = run_configs.llm_provider,
                 model: run_configs.LLM_MODEL = run_configs.llm_model.value,
                 systemPrompt:str="",
                 userPrompt:str ="",
                 image:str="",
                 thinking=True,
                 temperature: int=0,
                 ) -> str:
        import json
        obj = {}
        project_root = run_configs.get_project_root()
        file_path = os.path.join(
            project_root,
            "credentials.json"
        )
        
        # Priority 1: Load from environment variables (most secure for open source)
        # Priority 2: Fall back to credentials.json file (for backward compatibility)
        
        # Try to load from JSON file if it exists
        if os.path.exists(file_path):
            try:
                with open(file_path) as f:
                    obj = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Warning: Could not read credentials.json: {e}")
                obj = {}
        
        # Override with environment variables if they exist (environment variables take precedence)
        # This allows users to use env vars without needing the JSON file
        if "GEMINI_API_KEY" in os.environ:
            if "gemini" not in obj:
                obj["gemini"] = {}
            obj["gemini"]["key"] = os.environ["GEMINI_API_KEY"]
        
        if "GPT_INTERNAL_USERNAME" in os.environ:
            if "gpt_internal" not in obj:
                obj["gpt_internal"] = {}
            obj["gpt_internal"]["username"] = os.environ["GPT_INTERNAL_USERNAME"]
        
        if "GPT_INTERNAL_PASSWORD" in os.environ:
            if "gpt_internal" not in obj:
                obj["gpt_internal"] = {}
            obj["gpt_internal"]["password"] = os.environ["GPT_INTERNAL_PASSWORD"]
        
        # AWS Bedrock credentials from environment variables
        if "AWS_BEDROCK_SERVICE_NAME" in os.environ:
            if "aws_bedrock" not in obj:
                obj["aws_bedrock"] = {}
            obj["aws_bedrock"]["service_name"] = os.environ["AWS_BEDROCK_SERVICE_NAME"]
        
        if "AWS_BEDROCK_REGION" in os.environ:
            if "aws_bedrock" not in obj:
                obj["aws_bedrock"] = {}
            obj["aws_bedrock"]["region_name"] = os.environ["AWS_BEDROCK_REGION"]
        
        if "AWS_ACCESS_KEY_ID" in os.environ:
            if "aws_bedrock" not in obj:
                obj["aws_bedrock"] = {}
            obj["aws_bedrock"]["aws_access_key_id"] = os.environ["AWS_ACCESS_KEY_ID"]
        
        if "AWS_SECRET_ACCESS_KEY" in os.environ:
            if "aws_bedrock" not in obj:
                obj["aws_bedrock"] = {}
            obj["aws_bedrock"]["aws_secret_access_key"] = os.environ["AWS_SECRET_ACCESS_KEY"]
        
        if "AWS_SESSION_TOKEN" in os.environ:
            if "aws_bedrock" not in obj:
                obj["aws_bedrock"] = {}
            obj["aws_bedrock"]["aws_session_token"] = os.environ["AWS_SESSION_TOKEN"]
        userPrompt = systemPrompt + "\n\n" + userPrompt
        systemPrompt = ""
        startTime = time.time()
        properResponse = None
        responsePath = ""
        totalTokenPath = ""
        url = ""
        headers = ""
        payload = ""
        if provider == run_configs.LLM_Provider.GEMINI:
            # Validate credentials
            if "gemini" not in obj or "key" not in obj.get("gemini", {}):
                raise ValueError(
                    "❌ Missing Gemini API key!\n\n"
                    "Please set your credentials using one of these methods:\n"
                    "1. Environment variable (recommended): export GEMINI_API_KEY='your-api-key'\n"
                    "2. JSON file: Create credentials.json with: {\"gemini\": {\"key\": \"your-api-key\"}}\n"
                    "   See credentials.json.example for a template.\n\n"
                    "Get your API key: https://aistudio.google.com/app/apikey"
                )
            
            user_parts = [{
                "text": userPrompt
            }]
            if image != "":
                user_parts.append({
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image
                    }
                })
            responsePath = "/candidates/0/content/parts/0/text"
            totalTokenPath = ["/usageMetadata/totalTokenCount"]
            url = 'https://generativelanguage.googleapis.com/v1beta/models/'+LLM_MODEL.GEMINI_2_5_PRO.value+':generateContent?key=' + obj["gemini"]["key"]
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "system_instruction": {
                    "parts": [
                        {
                            "text": systemPrompt
                        }
                    ]
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": user_parts
                    }
                ],
                "generationConfig": {
                    "temperature": temperature,
                }
            }
            if thinking:
                payload["generationConfig"]["thinkingConfig"] = {
                    "thinkingBudget": 24576
                }
        elif provider == run_configs.LLM_Provider.OPENAI_INTERNAL:
            # Validate credentials
            if "gpt_internal" not in obj or "username" not in obj.get("gpt_internal", {}) or "password" not in obj.get("gpt_internal", {}):
                raise ValueError(
                    "❌ Missing GPT Internal credentials!\n\n"
                    "Please set your credentials using one of these methods:\n"
                    "1. Environment variables (recommended):\n"
                    "   export GPT_INTERNAL_USERNAME='your-username'\n"
                    "   export GPT_INTERNAL_PASSWORD='your-password'\n"
                    "2. JSON file: Create credentials.json with:\n"
                    "   {\"gpt_internal\": {\"username\": \"your-username\", \"password\": \"your-password\"}}\n"
                    "   See credentials.json.example for a template."
                )
            
            model_code = None
            # Handle both enum and string types
            model_value = model.value if hasattr(model, 'value') else model
            if model_value == LLM_MODEL.GPT_4O.value or model_value == "gpt-4O":
                model_code = 40
            user_parts = [{"type": "text", "text": userPrompt}]
            if image != "":
                user_parts.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + image}})
            responsePath = "/response/openAIResponse/choices/0/message/content"
            totalTokenPath = ["/response/openAIResponse/usage/total_tokens"]
            url = ""
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "username": obj["gpt_internal"]["username"],
                "password": obj["gpt_internal"]["password"],
                "api": model_code,
                "request": {
                    "messages": [
                        {
                            "role": "system",
                            "content": systemPrompt
                        },
                        {
                            "role": "user",
                            "content": user_parts
                        }
                    ],
                    "temperature": temperature
                }
            }
        elif provider == run_configs.LLM_Provider.PERPLEXITY:
            user_parts = [{"type": "text", "text": userPrompt}]
            if image != "":
                user_parts.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + image}})
            responsePath = "/response/openAIResponse/choices/0/message/content"
            totalTokenPath = ["/response/openAIResponse/usage/total_tokens"]
            modelPath = "/response/openAIResponse/model"
            url = ""
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "request": {
                    "messages": [
                        {
                            "role": "system",
                            "content": systemPrompt
                        },
                        {
                            "role": "user",
                            "content": user_parts
                        }
                    ],
                    "temperature": temperature
                }
            }
        elif provider == run_configs.LLM_Provider.AWS_BEDROCK:
            user_parts = [{
                "type": "text",
                "text": userPrompt
            }]
            if image != "":
                user_parts.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image
                    }
                })
            responsePath = ""
            if thinking:
                responsePath = "/content/1/text"
            else:
                responsePath = "/content/0/text"
            totalTokenPath = ["/usage/input_tokens", "/usage/cache_creation_input_tokens",
                              "/usage/cache_read_input_tokens",
                              "/usage/output_tokens"]

        if provider == run_configs.LLM_Provider.AWS_BEDROCK:
            # Validate credentials
            required_fields = ["service_name", "region_name", "aws_access_key_id", "aws_secret_access_key"]
            if "aws_bedrock" not in obj:
                raise ValueError(
                    "❌ Missing AWS Bedrock credentials!\n\n"
                    "Please set your credentials using one of these methods:\n"
                    "1. Environment variables (recommended):\n"
                    "   export AWS_BEDROCK_SERVICE_NAME='bedrock-runtime'\n"
                    "   export AWS_BEDROCK_REGION='us-east-1'\n"
                    "   export AWS_ACCESS_KEY_ID='your-access-key'\n"
                    "   export AWS_SECRET_ACCESS_KEY='your-secret-key'\n"
                    "   export AWS_SESSION_TOKEN='your-session-token'  # Optional\n"
                    "2. JSON file: Create credentials.json with aws_bedrock section.\n"
                    "   See credentials.json.example for a template."
                )
            
            missing_fields = [field for field in required_fields if field not in obj.get("aws_bedrock", {})]
            if missing_fields:
                raise ValueError(
                    f"❌ Missing AWS Bedrock credential fields: {', '.join(missing_fields)}\n\n"
                    "Please set all required credentials. See credentials.json.example for a template."
                )
            
            import boto3
            config = Config(
                read_timeout=300,  # 5 minutes
                retries={'max_attempts': 3}
            )
            bedrock = boto3.client(
                config=config,
                service_name = obj["aws_bedrock"]["service_name"],
                region_name = obj["aws_bedrock"]["region_name"],
                aws_access_key_id = obj["aws_bedrock"]["aws_access_key_id"],
                aws_secret_access_key = obj["aws_bedrock"]["aws_secret_access_key"],
                aws_session_token = obj["aws_bedrock"].get("aws_session_token")  # Optional field
            )
            if thinking:
                payload = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 65536,
                    "temperature": 1,
                    "system": systemPrompt,
                    "thinking": {
                        "type": "enabled",
                        "budget_tokens": 30000
                    },
                    "messages": [
                        {
                            "role": "user",
                            "content": user_parts
                        }
                    ]
                }
            else:
                payload = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 65536,
                    "temperature": temperature,
                    "system": systemPrompt,
                    "messages": [
                        {
                            "role": "user",
                            "content": user_parts
                        }
                    ]
                }
            # Handle both enum and string types
            model_id = model.value if hasattr(model, 'value') else model
            response = bedrock.invoke_model(
                modelId=model_id,
                body=json.dumps(payload)
            )
            val = response["body"].read().decode("utf-8")
            properResponse = self.extractJsonValueBasedOnPath(val, self.convert_intellij_json_path_to_right_format(responsePath))
        else:
            for attempt in range(3):
                response = requests.post(url=url, data=json.dumps(payload), headers=headers, timeout=120)
                val = response.text
                properResponse = self.extractJsonValueBasedOnPath(val, self.convert_intellij_json_path_to_right_format(responsePath))
                if properResponse is not None:
                    if attempt > 1:
                        print(val)
                        print("LLM responded successfully after " + str(attempt + 1) + " attempts")
                    break
        if properResponse is None:
            print(response.text)
            print("LLM did not respond even after 3 attempts.")
        tokenCount = self.calculate_total_token_count(val, totalTokenPath)
        endTime = time.time()
        duration = endTime - startTime
        llmResponseTime.append(duration)
        if tokenCount is not None:
            llmTokens.append(int(tokenCount))
        else:
            llmTokens.append(0)
        return self.split_on_last(properResponse, "```json")[-1]

    def visualGetText(self, base64Image: str, userPrompt: str) -> str:
        systemPrompt = "You are a helpful assistant. Extract the text specified by user from the given image and return it as a pure string without enclosing in single/double quotes. If no text is found, return `None`. Do not return anything else with this"
        val = self.setupLLM(systemPrompt=systemPrompt, userPrompt=userPrompt, image=base64Image, thinking=False)
        return val

    def getText(self, element, textDescription, keyName):
        if run_configs.dryRun == False:
            val = ""
            if element is not None:
                try:
                    self.scrollToElement(element)
                except Exception as e:
                    for xpath in run_configs.SECTION_AUTO_ID:
                        try:
                            self.scrollToElement(xpath)
                        except Exception as e:
                            pass
            else:
                for xpath in run_configs.SECTION_AUTO_ID:
                    try:
                        self.scrollToElement(xpath)
                    except Exception as e:
                        pass
            val = self.visualGetText(self.take_screenshot_as_base64(), textDescription)
            if val is None or val.lower().strip() == "none" or val.lower().strip() == "":
                print("No text found for the provided element or description")
                return None
            if keyName is not None:
                run_configs.variables[keyName] = val
                print("Text captured and stored in `variables` dictionary", {keyName: val})
            else:
                print("Text `" + val + "` captured but not stored in `variables` dictionary")
            return val

    def extract_json_block(self, s: str) -> str:
        start = s.find('{')
        end = s.rfind('}')
        if start == -1 or end == -1 or start > end:
            return ""  # Return empty if braces are not found or malformed
        return s[start:end + 1]

    def selfHeal(self, locator, text=None, position=1):
        if run_configs.dryRun == False:
            if text is None:
                abc = ""
            else:
                abc = text
            locator = self.verifyAndGetLocator(locator, text, position)
        return locator

    def verifyAndGetLocator(self, locator, text, position):
        if locator is None or locator == "":
            print("Locator is invalid, returning None")
            return None

        if text is None:
            text = ""

        pattern = r"\{[^}]*\}"
        matches = re.findall(pattern, locator)
        # print(f"Dynamic param count: {len(matches)}")
        if len(matches) > 2:
            print("Locator has more than 2 dynamic parameters, but available params to substitute are " + len(
                matches) + " so cannot self-heal")
            return None
        if len(matches) == 1:
            if re.search(r"\[\{.*?\}\]", locator):
                locator = re.sub(r"\[\{.*?\}\]", "[{position}]", locator, count=1)
                locator = "(" + locator
                locator = locator.replace("[{position}]", ")[{position}]")
            else:
                locator = re.sub(pattern, "{text}", locator, count=1)
                matches = list(re.finditer(r"\)\[\d+\]", locator))
                if matches:
                    last = matches[-1]
                    start, end = last.span()
                    locator = locator[:start] + ")" + locator[end:]

        else:
            locator = re.sub(pattern, "{text}", locator, count=1)
            matches = list(re.finditer(pattern, locator))
            if matches:
                last = matches[-1]
                start, end = last.span()
                locator = locator[:start] + "{position}" + locator[end:]

        # print("Locator after dynamic param substitution: " + locator)

        allOccurrenceSpecificLocator = locator.replace(")[{position}]", ")")
        allOccurrenceAllLocator = allOccurrenceSpecificLocator

        allOccurrenceAllLocator = allOccurrenceAllLocator.replace("='{text}'", "")
        allOccurrenceAllLocator = allOccurrenceAllLocator.replace("normalize-space(.),'{text}'",
                                                                  "normalize-space(.),''")
        allOccurrenceAllLocator = allOccurrenceAllLocator.replace("normalize-space(.), '{text}'",
                                                                  "normalize-space(.),''")

        # print("allOccurrenceAllLocator: " + allOccurrenceAllLocator)
        # print("allOccurrenceAllLocator Count: " + str(page.locator(allOccurrenceAllLocator).count()))
        import time

        start_time = time.time()
        timeout = 30
        count = 0
        while time.time() - start_time < timeout:
            try:
                count = self.locatorCount(allOccurrenceAllLocator)
                if count >= 1:
                    break
            except Exception as e:
                pass
            print("Waiting for locator to appear on page...")
            time.sleep(0.5)

        if count <= 0:
            print("Locator: " + allOccurrenceAllLocator + " not found on page, returning None")
            return None

        enhancedText = ""
        if text != "":
            enhancedText = self.getMatchingText(allOccurrenceAllLocator, text)

        if position == 0:
            if text == "":
                # print("Locator: " + allOccurrenceAllLocator)
                return allOccurrenceAllLocator
            allOccurrenceSpecificLocator = allOccurrenceSpecificLocator.replace("{text}", enhancedText)
            # print("Locator: " + allOccurrenceSpecificLocator)
            return allOccurrenceSpecificLocator
        elif position < 0:
            if text == "":
                # print("Locator: " + allOccurrenceAllLocator + "[last()+1" + str(position) + "]")
                return allOccurrenceAllLocator + "[last()+1" + str(position) + "]"
            allOccurrenceSpecificLocator = allOccurrenceSpecificLocator.replace("{text}",
                                                                                enhancedText) + "[last()+1" + str(
                position) + "]"
            # print("Locator: " + allOccurrenceSpecificLocator)
            return allOccurrenceSpecificLocator
        else:
            if text == "":
                # print("Locator: " + "(" + allOccurrenceAllLocator + ")[" + str(position) + "]")
                return "(" + allOccurrenceAllLocator + ")[" + str(position) + "]"
            allOccurrenceSpecificLocator = allOccurrenceSpecificLocator.replace("{text}", enhancedText) + "[" + str(
                position) + "]"
            # print("Locator: " + allOccurrenceSpecificLocator)
            return allOccurrenceSpecificLocator

    def locatorGenUsingLLM(self, locator_description) -> str:
        # locator_description = getMethodName()
        print("Locator Generation using LLM started...")
        outer_html = self.get_section_outer_html(run_configs.SECTION_AUTO_ID)
        sanitized_html = outer_html
        # sanitized_html = sanitize_html(outer_html)
        generated_locator = self.get_relative_xpath(locator_description, sanitized_html)
        print(f"Locator Generated by LLM: {generated_locator}")
        return generated_locator

    @abstractmethod
    def get_section_outer_html(self, xpath_list: list) -> str:
        pass

    @abstractmethod
    def get_relative_xpath(self, locator_description: str, sanitized_html: str) -> str:
        pass

    def selfHealWithoutParent(self, locator_description, locator, text=None, position=1):
        if run_configs.dryRun == False:
            # print("Self Healing without parent called")
            if text is None:
                abc = ""
            else:
                abc = text
            locator = self.verifyAndGetLocator(locator, text, position)
        return locator

    @abstractmethod
    def navigateBack(self):
        pass

    @abstractmethod
    def getTextPure(self, locator):
        pass

    @abstractmethod
    def scrollToElement(self, element):
        pass

    @abstractmethod
    def locatorCount(self, element: str):
        pass

    def assertion(self, assertion: Annotated[
        str, "derived strictly from the user-provided task and the values from `variables` dictionary if applicable"]):
        if run_configs.dryRun == False:
            systemPrompt = """
            You are a helpful assistant. Respond with true/false. Then use a `|` symbol and provide your entire response
            CRITICAL DATE VALIDATION RULE (Applicable only if the assertion involves date validation):
                VALIDATE ONLY: Date number + Month (any format) IGNORE: Year, date format, time (unless user explicitly requests)
                - POSITIVE ASSERTION (True) IF:
                    - Correct date number visible
                    - Correct month visible (abbreviated/full/numeric - any format OK)
                - NEGATIVE ASSERTION (False) ONLY IF:
                    - Wrong date number OR wrong month OR missing date/month
                FORBIDDEN: Failing assertions due to year differences or format variations
                Example:
                    Expected "7 August 2025" → Display "07 Aug" = ✅ POSITIVE,
                    Expected "07 Sept 2025" → Display "7 September" = ✅ POSITIVE
            Note: Prepare your response post your thinking process and answer in the end
            """
            check = self.setupLLM(systemPrompt=systemPrompt, userPrompt=assertion)
            print(check)
            actualAssertion: str = check.split("|")[0].strip().lower()
            soft_assert.equal(actualAssertion, "true", f"Soft Assertion Failed: {assertion}")

    @abstractmethod
    def wait_for_response_to_be_captured(self, response_data: List, timeout: int = 10):
        """Wait for response to be captured with timeout."""
        pass

    @abstractmethod
    def is_broken_link(self, url: str) -> bool:
        pass

    @abstractmethod
    def getAllTexts(self, locator) -> list[str]:
        pass

    def getMatchingText(self, locator, val):
        if run_configs.dryRun == False:
            values:list = self.getAllTexts(locator)
            list_of_lists = [list(filter(None, item.split("\n"))) for item in values]
            for sublist in list_of_lists:
                if val in sublist:
                    return val
            if run_configs.exactMatch == False:
                systemPrompt = (
                    "You are an intelligent semantic based text analyzer responsible for selecting the closest value from the provided list of list for user given text. "

                    "Respond strictly in JSON format:\n"
                    "Schema: {\n"
                    "  \"value\": \"string, exact value from the list of list which is the most suitable value (Strictly do not modify the value in any way even if it feels typical in the process). If no value is suitable return `TERMINATE`\",\n"
                    "  \"index\": \"int, index of the list which contains most suitable value from the list of list [index starts from 0]. If no value is suitable return -1\",\n"
                    "  \"Reasoning\": \"string, one-line explanation for why this value was chosen\"\n"
                    "}\n\n"
                )
                userPrompt = "List: " + str(list_of_lists) + "\nUser text: " + val + "\n\n"
                response = self.setupLLM(systemPrompt=systemPrompt, userPrompt=userPrompt)
                json_response = self.extract_json_block(response)
                value = self.extractJsonValueBasedOnPath(json_response, "/value")
                index = self.extractJsonValueBasedOnPath(json_response, "/index")
                reasoning = self.extractJsonValueBasedOnPath(json_response, "/Reasoning")
                # print("List of values: ", list_of_lists)
                print("Could not find any locator whose text exactly matches: " + val + "\nExact Matching is False so AI is looking for a close match")
                print("Value selected by LLM: " + value + "\nIndex selected by LLM: " + str(index) + "\nLLM Reasoning: " + reasoning)
                return value
            print("Could not find any locator whose text exactly matches: " + val + "\nExact Matching is True so AI is not interfering")
            pytest.fail("Could not find any locator whose text exactly matches: " + val + "\nExact Matching is True so AI is not interfering")
            return -1

    @abstractmethod
    def scroll_the_element_to_top(self, element):
        pass

    @abstractmethod
    def scroll_to_bottom_of_page(self):
        pass

    @abstractmethod
    def run_accessibility_audit(self, html_report=None, with_screenshots=True):
        pass

    @abstractmethod
    def get_performance_metrics(self):
        """
        Extracts performance metrics (FCP, LCP, CLS) from the given page.
        """
        pass

    @abstractmethod
    def compare_performance_metrics(self, prod_metrics, pp_metrics, tolerance):
        pass

    @abstractmethod
    def is_locator_present(self, element):
        pass

    def trigger_api_request(self, url, method="GET", headers=None, params=None, data=None, json_data=None):
        if run_configs.dryRun == False:
            try:
                if headers is None:
                    headers = {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                if method.upper() == "GET":
                    response = requests.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    if json_data:
                        response = requests.post(url, headers=headers, json=json_data)
                    else:
                        response = requests.post(url, headers=headers, data=data)
                elif method.upper() == "PUT":
                    response = requests.put(url, headers=headers, json=json_data)
                elif method.upper() == "DELETE":
                    response = requests.delete(url, headers=headers)
                else:
                    print(f"Unsupported method: {method}")
                    return None
                response.raise_for_status()
                try:
                    return response.json()
                except json.JSONDecodeError:
                    print("Response is not valid JSON")
                    return response.text
            except requests.exceptions.RequestException as e:
                print(f"API request failed: {e}")
                return None

    @abstractmethod
    def validate_ga_event(self, stExpected: list, dyExpected: dict, eventLog: str):
        pass

    @abstractmethod
    def convert_ga_json_to_log_format(self, ga_event_json: str):
        pass

    @abstractmethod
    def validateEvents(self, capturedGAEvents, stExpected: list, dyExpected: dict):
        pass

    @abstractmethod
    def fetch_ga_events_console_data_layer(self):
        pass

    def getLatestTestCases(self):
        # Steps to download a Google Sheet as CSV using Python:
        # 1. Open Google Cloud Console and create a new project.
        # 2. Search Google Sheets API and enable
        # 3. Search API and Services > Oauth consent screen > Internal > Create > Create Oauth Client > Desktop app > Download JSON
        # 4. Install libraries: pip install gspread google-auth google-auth-oauthlib pandas
        # 5. Keep the downloaded JSON as credentials.json in the same folder as this script

        from pathlib import Path
        import pandas as pd
        import gspread
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        import os, pickle

        # Scopes
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

        project_root = Path(__file__).resolve().parent
        credentialsFile = project_root / "credentials.json"
        outputFile = project_root / "tests.csv"

        creds = None
        # Load saved token if it exists (so you don’t login every time)
        if os.path.exists("token.pkl"):
            with open("token.pkl", "rb") as token:
                creds = pickle.load(token)

        # If no valid creds, login via browser
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(credentialsFile), SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.pkl", "wb") as token:
                pickle.dump(creds, token)

        # Connect with gspread
        client = gspread.authorize(creds)

        # Open sheet
        sheet_id = ""
        sheet_name = f"{run_configs.lob}_{run_configs.geo}"
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/" + sheet_id + "/edit")
        worksheet = sheet.worksheet(sheet_name)

        # Convert to DataFrame
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        # Save CSV
        df.to_csv(str(outputFile), index=False)
        print("Latest Test Case CSV downloaded successfully!")

    def get_test_details(self, epic_id, test_id):
        project_root = Path(__file__).resolve().parent
        csv_file = str(project_root / "tests.csv")
        df = pd.read_csv(csv_file, keep_default_na=False)

        # Clean column names to avoid trailing spaces issues
        df.columns = df.columns.str.strip()

        filtered = df[(df['Epic ID'] == epic_id) & (df['Test ID'] == test_id)]
        if filtered.empty:
            print(f"No test case found for Epic ID: {epic_id} and Test ID: {test_id}")
            pytest.fail(f"No test case found for Epic ID: {epic_id} and Test ID: {test_id}")
            return None

        channel = run_configs.channel.strip()

        def get_channel_value(col_base):
            """
            Fetches the channel-specific value for a column.
            Falls back to common if channel-specific data is missing or empty,
            but aborts immediately if the channel cell explicitly contains 'NA'.
            """
            channel_col = f"{col_base} - {channel}"
            common_col = f"{col_base} - common"

            # ✅ Step 1: Check channel-specific column first
            if channel_col in df.columns:
                value = filtered[channel_col].iloc[0].strip()
                # Abort if marked as 'NA' for this channel
                if value.upper() == "NA":
                    print(f"Test case not available for the particular channel ({channel}).")
                    pytest.fail(f"Test case not available for the particular channel ({channel}).")
                    return None
                # Return if non-empty
                if value:
                    return value

            # ✅ Step 2: Fallback to common only if channel cell is missing or blank (not NA)
            if common_col in df.columns:
                return filtered[common_col].iloc[0].strip()

            return ""  # Return empty string if both missing

        # Apply independent logic for both entities
        pre_conditions = get_channel_value("Pre Conditions")
        test_steps = get_channel_value("Test Steps and Assertions")

        # Return both separately (for clarity) or merged, as per your need
        return pre_conditions + test_steps

    @abstractmethod
    def _inject_data_layer_hook(self):
        """
        Inject JavaScript before any page loads to capture GA events.
        """
        pass

    @abstractmethod
    def _expose_event_handler(self):
        """
        Expose a Python function to handle GA events.
        """
        pass

    @classmethod
    @abstractmethod
    def _add_event(cls, event: Dict):
        """
        Internal helper to safely append events to the shared event store.
        """
        pass

    @classmethod
    @abstractmethod
    def get_all_events(cls) -> List[Dict]:
        """
        Retrieve all captured GA events.
        """
        pass

    @classmethod
    @abstractmethod
    def clear_events(cls):
        """
        Clear all stored GA events.
        """
        pass

    @abstractmethod
    def _setup_listener(self):
        """
        Set up the listener by exposing the handler and injecting JS.
        """
        pass

    @abstractmethod
    def build_ga_validation_prompt(self, expected_yaml_path: str, actual_events: list, page_name="home_page",
                                   user_type="guest_user"):
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
        pass

    _request_payloads: List[str] = []

    _handlers = []

    @abstractmethod
    def take_screenshot_as_base64(self) -> str:
        pass

    def sanitize_html(self, html_content: str) -> str:
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, 'html5lib')

        for script in soup.find_all('script'):
            script.string = ''

################################################################################
        for style in soup.find_all('style'):
            style.string = ''

        for img in soup.find_all('img'):
            if img.has_attr('src'):
                img['src'] = ''
            if img.has_attr('data-src'):
                img['data-src'] = ''
            if img.has_attr('srcset'):
                img['srcset'] = ''

        for tag in soup.find_all():
            if tag.has_attr('style'):
                del tag['style']

            if tag.has_attr('style'):
                del tag['style']

            for attr in list(tag.attrs):
                if attr.startswith('on'):
                    del tag[attr]
                elif attr.startswith('data-style'):
                    del tag[attr]

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        return soup.prettify()


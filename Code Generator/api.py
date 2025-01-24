# api.py

import json  # Added import
import requests
from additional_info import ADDITIONAL_INFO
from additional_info import ADDITIONAL_INFO_CODE_MODULE_A
from additional_info import ADDITIONAL_INFO_CODE_MODULE_B

class ChatGPTAPI:
    def __init__(self, api_key, model):
        """
        Initialize with API key and model.
        :param api_key: OpenAI API key.
        :param model: Model to be used (e.g., "gpt-4").
        """
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def generate_code_with_explanation(self, prompt):
        """
        Generate code and explanation using ChatGPT.
        :param prompt: The input prompt to send to the ChatGPT API.
        :return: A dictionary with the generated code and explanation, or error details.
        """
        print("api.py: generate_code_with_explanation")
        if not self.api_key or not self.model:
            return {"error": "API key or model not set.", "raw_response": ""}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1500,
            "temperature": 0.7
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [])[0].get("message", {}).get("content", "")

            # Parse response to extract code and explanation
            return self._parse_response(content)
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "raw_response": ""}
        except (KeyError, IndexError) as e:
            return {"error": "Error parsing response.", "raw_response": response.text}

    def _parse_response(self, response_content):
        """
        Parse the response content to extract code and explanation.
        :param response_content: The full response content from ChatGPT.
        :return: A dictionary with 'code' and 'explanation' fields.
        """
        # Strip code blocks if present
        if response_content.startswith("```") and response_content.endswith("```"):
            # Remove the code block markers
            response_content = response_content.strip("```").strip()

            # Remove language specifier if present (e.g., "json")
            if response_content.lower().startswith("json"):
                response_content = response_content[4:].strip()

        try:
            parsed_response = json.loads(response_content)
            code = parsed_response.get("code", "No code provided.")
            explanation = parsed_response.get("explanation", "No explanation provided.")
            return {"code": code, "explanation": explanation}
        except json.JSONDecodeError:
            # If the response isn't valid JSON, attempt to extract sections manually
            code_marker = "Code:"
            explanation_marker = "Explanation:"

            code_start = response_content.find(code_marker)
            explanation_start = response_content.find(explanation_marker)

            if code_start == -1 or explanation_start == -1:
                return {"code": "", "explanation": response_content.strip()}

            code = response_content[code_start + len(code_marker):explanation_start].strip()
            explanation = response_content[explanation_start + len(explanation_marker):].strip()

            return {"code": code, "explanation": explanation}

    def analyse_text(self, text_input, max_tokens=300):
        """Send a text prompt to ChatGPT and return the response."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": text_input}],
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            return f"API Error: {str(e)}"
        except (KeyError, IndexError):
            return "Error parsing API response."

    # Removed unused methods to clean up the code

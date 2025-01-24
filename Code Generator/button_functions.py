# button_functions.py

import json
import datetime
import threading
import queue
import logging
from logging.handlers import RotatingFileHandler
import traceback
from additional_info import ADDITIONAL_INFO
from additional_info import ADDITIONAL_INFO_CODE_MODULE_A
from additional_info import ADDITIONAL_INFO_CODE_MODULE_B
from api import ChatGPTAPI


class ButtonFunctions:
    def __init__(self, chatgpt_api, ui_components):
        """
        Initialize with ChatGPT API instance and UI components.
        :param chatgpt_api: ChatGPTAPI instance.
        :param ui_components: Dictionary of UI components (text boxes, dropdowns, etc.).
        """
        # Initialize logging with rotating file handler
        self.logger = logging.getLogger("ButtonFunctions")
        self.logger.setLevel(logging.DEBUG)

        # RotatingFileHandler: 5MB per file, keep 3 backups
        fh = RotatingFileHandler("application.log", maxBytes=5 * 1024 * 1024, backupCount=3)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        self.chatgpt_api = chatgpt_api
        self.ui_components = ui_components
        self.refinement_history = []
        self.log_queue = queue.Queue()
        self.poll_log_queue()

        # Configure log tags for color-coding
        self._configure_log_tags()

        # **Debugging: Log the keys present in ui_components**
        self.log_progress(f"UI Components Keys: {list(self.ui_components.keys())}", level="DEBUG")
        print(f"[DEBUG] UI Components Keys: {list(self.ui_components.keys())}")

    def _configure_log_tags(self):
        """Configure tags for different log levels to display colored text."""
        progress_log_box = self.ui_components.get("progress_log_box")
        if progress_log_box:
            progress_log_box.tag_config("INFO", foreground="green")
            progress_log_box.tag_config("WARNING", foreground="orange")
            progress_log_box.tag_config("ERROR", foreground="red")
            progress_log_box.tag_config("DEBUG", foreground="blue")
            progress_log_box.tag_config("REQUEST", foreground="purple")

    def poll_log_queue(self):
        """Poll the log queue and update the log box."""
        while not self.log_queue.empty():
            try:
                log_message = self.log_queue.get_nowait()
                progress_log_box = self.ui_components.get("progress_log_box")
                if progress_log_box:
                    progress_log_box.config(state="normal")
                    progress_log_box.insert("end", log_message)
                    progress_log_box.see("end")
                    progress_log_box.config(state="disabled")
            except queue.Empty:
                pass
        self.ui_components["progress_log_box"].after(100, self.poll_log_queue)  # Poll every 100 ms

    def log_progress(self, message, level="INFO"):
        """Add a log message to the queue and to the log file."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        self.log_queue.put(log_entry)

        # Log to file
        if level == "INFO":
            self.logger.info(message)
        elif level == "WARNING":
            self.logger.warning(message)
        elif level == "ERROR":
            self.logger.error(message)
        else:
            self.logger.debug(message)

        # Insert into progress_log_box with appropriate tag
        progress_log_box = self.ui_components.get("progress_log_box")
        if progress_log_box:
            progress_log_box.config(state="normal")
            progress_log_box.insert("end", log_entry, level)
            progress_log_box.see("end")
            progress_log_box.config(state="disabled")

    def _get_module_details(self, module_name: str) -> dict:
        """
        Retrieve details from the UI for the given module.

        :param module_name: Name of the module ('module_a' or 'module_b').
        :return: Dictionary containing module details.
        """
        if module_name.lower() == "module_a":
            return {
                "type": self.ui_components["sensor_type_entry"].get(),
                "desc": self.ui_components["sensor_desc_entry"].get("1.0", "end").strip(),
                "technology": self.ui_components["sensor_tech_dropdown"].get(),
                "board": self.ui_components["sensor_module_dropdown"].get()
            }
        elif module_name.lower() == "module_b":
            return {
                "type": self.ui_components["endpoint_type_entry"].get(),
                "desc": self.ui_components["endpoint_desc_box"].get("1.0", "end").strip(),
                "technology": self.ui_components["endpoint_tech_dropdown"].get(),
                "board": self.ui_components["endpoint_board_dropdown"].get()
            }
        else:
            self.log_progress(f"Unknown module name: {module_name}", level="WARNING")
            return {}

    def suggest_data_format(self):
        """Use ChatGPT to suggest a data format based on the sensor description."""
        self.log_progress("Initiating data format suggestion.", level="INFO")
        threading.Thread(target=self._suggest_data_format_thread, daemon=True).start()

    def _suggest_data_format_thread(self):
        try:
            # Check if a model is selected
            if not self.chatgpt_api or not self.chatgpt_api.model:
                self._update_feedback("Error: No ChatGPT model selected. Please select a model first.")
                self.log_progress("Failed to suggest data format: No ChatGPT model selected.", level="ERROR")
                return

            sensor_type = self.ui_components["sensor_type_entry"].get().strip()
            sensor_desc = self.ui_components["sensor_desc_entry"].get("1.0", "end").strip()
            self.log_progress(f"Sensor Type: {sensor_type}, Sensor Description: {sensor_desc}", level="DEBUG")

            # Retrieve example code from bottom tabs
            example_code_1 = self.ui_components["example_tab_1_text"].get("1.0", "end").strip()
            example_code_2 = self.ui_components["example_tab_2_text"].get("1.0", "end").strip()

            # Check that necessary inputs are provided
            if not sensor_type or not sensor_desc:
                self._update_feedback("Error: Please fill out the sensor type and description fields.")
                self.log_progress("Failed to suggest data format: Missing sensor type or description.", level="ERROR")
                return

            # Construct the prompt for data format suggestion
            data_format = self.ui_components["data_format_box"].get("1.0", "end").strip()
            prompt = f"""
{ADDITIONAL_INFO['intro']}

{ADDITIONAL_INFO['data_format']}

Code example for Module A:
{ADDITIONAL_INFO_CODE_MODULE_A['example']}

- Example Code 1:  {example_code_1}
- Example Code 2:  {example_code_2}

You are designing an IoT Gateway system. Here is the setup:

Module A:
- Sensor Type: {sensor_type}
- Description: {sensor_desc}
- Wireless Communication Technology: {self.ui_components['sensor_tech_dropdown'].get()}
- Development Board: {self.ui_components['sensor_module_dropdown'].get()}

Module B:
- Data Format for Communication between Module A and Module B: {data_format}

Please suggest a JSON format for communication between Module A and Module B. Provide an explanation of the suggested format.
Remember that for many wireless devices it is not possible to get a timestamp from them.

Provide the response strictly in the following JSON structure:
{{
  "code": "The data format to be used between A and B modules as a string.
            Keep it short as there is limited data size.  
            Short variable names are good.
            Only relevant variables should be transmitted. 
            Multiline format is nice and clearer.",
  "explanation": "A concise explanation of the data format and why it was suggested. Bullet points are preferred. Not JSON!"
}}
Make sure your response is in JSON format! Do not provide answer inside ```!
"""

            # Log the prompt being sent
            self.log_progress(f"Sending prompt to ChatGPT API for data format suggestion:\n{prompt}", level="DEBUG")
            print(f"[DEBUG] Sending prompt to ChatGPT API for data format suggestion:\n{prompt}")

            # Call the ChatGPT API
            self.log_progress("Sending prompt to ChatGPT API for data format suggestion.", level="INFO")
            result = self.chatgpt_api.generate_code_with_explanation(prompt)

            # Log the response received
            self.log_progress(f"Received response from ChatGPT API for data format suggestion:\n{result}", level="DEBUG")
            print(f"[DEBUG] Received response from ChatGPT API for data format suggestion:\n{result}")

            # Handle response or errors
            self._handle_response(result, "data_format")

            # Log successful data format suggestion
            self.log_progress("Data format suggested successfully.", level="INFO")

        except Exception as e:
            error_trace = traceback.format_exc()
            self._update_feedback("Error: An unexpected error occurred while suggesting data format.")
            self.log_progress(f"Exception during data format suggestion: {e}\n{error_trace}", level="ERROR")

    def generate_code_for_module(self, module_name):
        """Generate code for a single module (Module A or Module B)."""
        self.log_progress(f"Initiating code generation for {module_name}.", level="INFO")
        threading.Thread(target=self._generate_code_thread, args=(module_name,), daemon=True).start()

    def _generate_code_thread(self, module_name):
        try:
            # Retrieve module details and data format from the UI
            module_details = self._get_module_details(module_name)
            data_format = self.ui_components["data_format_box"].get("1.0", "end").strip()

            # Retrieve example code from bottom tabs
            example_code_1 = self.ui_components["example_tab_1_text"].get("1.0", "end").strip()
            example_code_2 = self.ui_components["example_tab_2_text"].get("1.0", "end").strip()

            # Validate inputs
            if not module_details or not data_format:
                self._update_feedback(f"Error: Fill all fields for {module_name} and define the data format.")
                self.log_progress(f"Failed to generate code for {module_name}: Missing module details or data format.",
                                  level="ERROR")
                return

            # Extract module-specific values from UI
            sensor_type = module_details.get("type", "")
            sensor_description = module_details.get("desc", "")
            wireless_technology = module_details.get("technology", "")
            development_board = module_details.get("board", "")

            # Get the appropriate prompt
            if module_name.lower() == "module_a":
                prompt = self.get_prompt_a(sensor_type, sensor_description, wireless_technology, development_board,
                                           data_format, example_code_1, example_code_2)
            elif module_name.lower() == "module_b":
                prompt = self.get_prompt_b(wireless_technology, development_board, data_format, example_code_1,
                                           example_code_2)
            else:
                self._update_feedback("Error: Unknown module name.")
                self.log_progress(f"Failed to generate code: Unknown module name '{module_name}'.", level="ERROR")
                return

            # Log the prompt being sent
            self.log_progress(f"Sending prompt to ChatGPT API for {module_name}:\n{prompt}", level="DEBUG")
            print(f"[DEBUG] Sending prompt to ChatGPT API for {module_name}:\n{prompt}")

            # Send the prompt to ChatGPT
            self.log_progress(f"Sending prompt to ChatGPT API for {module_name}.", level="INFO")
            result = self.chatgpt_api.generate_code_with_explanation(prompt)

            # Log the response received
            self.log_progress(f"Received response from ChatGPT API for {module_name}:\n{result}", level="DEBUG")
            print(f"[DEBUG] Received response from ChatGPT API for {module_name}:\n{result}")

            # Handle response or errors
            self._handle_response(result, module_name)

            # Log successful code generation
            self.log_progress(f"Code generation for {module_name} completed.", level="INFO")

            # Save to refinement history
            if "code" in result:
                self.refinement_history.append({
                    "module": module_name,
                    "prompt": prompt,
                    "code": result["code"],
                    "explanation": result.get("explanation", "")
                })
                self.log_progress(f"Appended to refinement_history: Module {module_name}", level="DEBUG")
                print(f"[DEBUG] refinement_history after append: {self.refinement_history}")

        except Exception as e:
            error_trace = traceback.format_exc()
            self._update_feedback("Error: An unexpected error occurred while generating code.")
            self.log_progress(f"Exception during code generation for {module_name}: {e}\n{error_trace}", level="ERROR")

    def refine_last_generated_code(self):
        """Refine the last generated code based on Code Modification Requests."""
        self.log_progress("Initiating code refinement/modification.", level="INFO")
        threading.Thread(target=self._refine_last_generated_code_thread, daemon=True).start()

    def _refine_last_generated_code_thread(self):
        try:
            modification_request = self.ui_components["modification_requests_box"].get("1.0", "end").strip()

            # Prepend [REQUEST] to the modification request
            formatted_request = f"[REQUEST] {modification_request}"

            # Log the modification request with REQUEST tag
            self.log_progress(f"Modification Request:\n{formatted_request}", level="REQUEST")
            print(f"[DEBUG] Modification Request:\n{formatted_request}")

            if not self.refinement_history:
                self._update_feedback("Error: No code history available for refinement.")
                self.log_progress("Refinement failed: No code history available.", level="ERROR")
                return

            last_entry = self.refinement_history[-1]
            original_code = last_entry.get("code")
            if not original_code:
                self._update_feedback("Error: Original code is missing from history.")
                self.log_progress("Refinement failed: Original code is missing.", level="ERROR")
                return

            # Log the original code
            self.log_progress(f"Original Code Retrieved:\n{original_code}", level="DEBUG")
            print(f"[DEBUG] Original Code Retrieved:\n{original_code}")

            # Construct the refine prompt
            refine_prompt = f"""
{formatted_request}

Original Code:
{original_code}

Please apply the requested modification and provide the response strictly in this JSON format:
{{
  "code": "The modified code as a string",
  "explanation": "Detailed explanation of the changes made"
}}
Make sure your response is in JSON format! Do not provide answer inside ```!
"""

            # Log the refine prompt being sent
            self.log_progress(f"Sending refine prompt to ChatGPT API:\n{refine_prompt}", level="DEBUG")
            print(f"[DEBUG] Sending refine prompt to ChatGPT API:\n{refine_prompt}")

            # Send the prompt to ChatGPT
            self.log_progress("Sending refine prompt to ChatGPT API.", level="INFO")
            result = self.chatgpt_api.generate_code_with_explanation(refine_prompt)

            # Log the response received
            self.log_progress(f"Received response from ChatGPT API for refinement/modification:\n{result}",
                              level="DEBUG")
            print(f"[DEBUG] Received response from ChatGPT API for refinement/modification:\n{result}")

            # Handle response or errors
            self._handle_response(result, last_entry["module"])

            # Save refinement/modification to history
            if "code" in result:
                self.refinement_history.append({
                    "module": last_entry["module"],
                    "prompt": refine_prompt,
                    "code": result["code"],
                    "explanation": result.get("explanation", ""),
                    "modification_request": modification_request
                })
                self.log_progress(f"Code refinement/modification for {last_entry['module']} completed.", level="INFO")
                print(f"[DEBUG] refinement_history after append: {self.refinement_history}")

        except Exception as e:
            error_trace = traceback.format_exc()
            self._update_feedback("Error: An unexpected error occurred while refining/modifying code.")
            self.log_progress(f"Exception during code refinement/modification: {e}\n{error_trace}", level="ERROR")

    def _update_feedback(self, message, module_name=None):
        """Update the feedback and code boxes in the UI."""
        self.log_progress(f"Updating feedback box: {message}", level="DEBUG")
        print(f"[DEBUG] Feedback message being sent to feedback_box:\n{message}")

        try:
            # Remove any surrounding backticks (` ``` `) from the response
            if message.startswith("```json") and message.endswith("```"):
                message = message.strip("```").replace("json", "", 1).strip()
                self.log_progress("Cleaned message from backticks for JSON parsing.", level="DEBUG")
                print("[DEBUG] Cleaned message from backticks for JSON parsing.")

            # Attempt to parse JSON
            parsed_response = json.loads(message)
            self.log_progress("Parsed JSON response successfully.", level="DEBUG")
            print("[DEBUG] Parsed JSON Response:", parsed_response)

            # Extract 'code' and 'explanation' fields
            code = parsed_response.get("code", "No code provided.")
            explanation = parsed_response.get("explanation", "No explanation provided.")

            # Debugging extracted fields
            self.log_progress("Extracted Code and Explanation from response.", level="DEBUG")
            print("[DEBUG] Extracted Code:", code)
            print("[DEBUG] Extracted Explanation:", explanation)

            # Update the explanation text box
            feedback_box = self.ui_components["feedback_box"]
            feedback_box.config(state="normal")
            feedback_box.delete("1.0", "end")
            feedback_box.insert("end", explanation)
            feedback_box.config(state="disabled")

            # Determine which code box to update based on module_name
            if module_name == "module_a":
                code_box_key = "module_a_code_box"
            elif module_name == "module_b":
                code_box_key = "module_b_code_box"
            elif module_name == "data_format":
                code_box_key = "data_format_box"
            else:
                code_box_key = None

            if code_box_key:
                code_box = self.ui_components.get(code_box_key)
                if code_box:
                    code_box.config(state="normal")
                    code_box.delete("1.0", "end")
                    code_box.insert("end", code)
                    code_box.config(state="disabled")
                    self.log_progress(f"Updated {code_box_key} with generated code.", level="INFO")
                    print(f"[DEBUG] Updated {code_box_key} with generated code.")
                else:
                    self.log_progress(f"{code_box_key} not found in UI components.", level="WARNING")
                    print(f"[DEBUG] {code_box_key} not found in UI components.")
            else:
                self.log_progress("No module name provided; skipping code box update.", level="DEBUG")
                print("[DEBUG] No module name provided; skipping code box update.")

        except json.JSONDecodeError as e:
            # If message is not JSON, treat it as plain text
            self.log_progress("Received plain text message.", level="DEBUG")
            print("[DEBUG] Received plain text message.")
            feedback_box = self.ui_components["feedback_box"]
            feedback_box.config(state="normal")
            feedback_box.delete("1.0", "end")
            feedback_box.insert("end", message)
            feedback_box.config(state="disabled")
        except Exception as e:
            # Handle other unexpected exceptions
            self.log_progress(f"Unexpected error: {e}", level="ERROR")
            print("[ERROR] An unexpected error occurred:", e)
            explanation = "Error: An unexpected error occurred while processing the response."
            code = "Error: Unable to retrieve code."

            # Show error messages in the feedback box
            feedback_box = self.ui_components["feedback_box"]
            feedback_box.config(state="normal")
            feedback_box.delete("1.0", "end")
            feedback_box.insert("end", explanation)
            feedback_box.config(state="disabled")

    def _handle_response(self, result, module_name):
        """Handle API response and update the UI accordingly."""
        if "error" in result:
            self._update_feedback(f"Error: {result['error']}\n{result.get('raw_response', '')}")
            self.log_progress(f"API Error: {result['error']}", level="ERROR")
            return

        explanation = result.get("explanation", "No explanation provided.")
        code = result.get("code", "No code provided.")

        # Update the code box
        if module_name in ["module_a", "module_b", "data_format"]:
            code_box_key = f"{module_name.lower()}_code_box"
            code_box = self.ui_components.get(code_box_key)
            if code_box:
                code_box.config(state="normal")
                code_box.delete("1.0", "end")
                code_box.insert("end", code)
                code_box.config(state="disabled")
                self.log_progress(f"Updated {module_name} code box with generated code.", level="INFO")
            else:
                self.log_progress(f"Code box for {module_name} not found.", level="WARNING")
        else:
            self.log_progress(f"Unknown module name: {module_name}", level="WARNING")

        # Update feedback box with explanation
        self._update_feedback(explanation, module_name)
        self.log_progress(f"Updated feedback box with explanation for {module_name}.", level="INFO")

    def copy_code_to_clipboard(self, text_box):
        """Copy code from a text box to the clipboard."""
        if text_box:
            text_box_content = text_box.get("1.0", "end").strip()
            if text_box_content:
                self.ui_components["feedback_box"].tk.call("clipboard", "clear")
                self.ui_components["feedback_box"].tk.call("clipboard", "append", text_box_content)
                self._update_feedback("Code copied to clipboard.")
                self.log_progress("Code copied to clipboard.", level="INFO")
                # Log the copied code for auditing
                self.log_progress(f"Copied Code:\n{text_box_content}", level="DEBUG")
                print(f"[DEBUG] Copied Code:\n{text_box_content}")
            else:
                self._update_feedback("Error: No code to copy.")
                self.log_progress("Attempted to copy code: No code available.", level="ERROR")

    # Define prompts for module A and B within the class
    def get_prompt_a(self, sensor_type, sensor_description, wireless_technology, development_board, data_format,
                     example_code_1, example_code_2):
        return f"""
{ADDITIONAL_INFO['intro']}

{ADDITIONAL_INFO['module_a']}

{ADDITIONAL_INFO['data_format']}

Code example for Module A:
{ADDITIONAL_INFO_CODE_MODULE_A['example']}

- Example Code 1:  {example_code_1}
- Example Code 2:  {example_code_2}

You are designing an IoT Gateway system. Here is the setup:

Module A:
- Sensor Type: {sensor_type}
- Description: {sensor_description}
- Wireless Communication Technology: {wireless_technology}
- Development Board: {development_board}

Module B:
- Data Format for Communication between Module A and Module B: {data_format}

Please generate the Arduino code for Module A, which:
1. Connects to the specified sensor using {wireless_technology}.
2. Formats the data according to the given format.
3. Sends the data to Module B.

Use #include "AnttiGateway.h"
Most important thing is to be compatible with the AnttiGateway.h library!

Provide the response strictly in the following JSON structure:
{{
  "code": "The Arduino code for Module A as a string.",
  "explanation": "A concise explanation of how the code works and interfaces with Module B as a string. Bullet points are preferred. Not JSON!"
}}
Make sure your response is in JSON format! Do not provide answer inside ```!
"""

    def get_prompt_b(self, wireless_technology, development_board, data_format, example_code_1, example_code_2):
        return f"""
{ADDITIONAL_INFO['intro']}

{ADDITIONAL_INFO['module_b']}

{ADDITIONAL_INFO['data_format']}

Code example for Module B:
{ADDITIONAL_INFO_CODE_MODULE_B['example']}

- Example Code 1:  {example_code_1}
- Example Code 2:  {example_code_2}


You are designing an IoT Gateway system. Here is the setup:

Module A:
- Data Format for Communication: {data_format}

Module B:
- Technology: {wireless_technology}
- Development Board: {development_board}

Please generate the Arduino code for Module B, which:
1. Receives data from Module A using the specified format.
2. Processes and validates the received data.
3. Transmits the data to the configured endpoint using {wireless_technology}.

Use #include "AnttiGateway.h"
Most important thing is to be compatible with the AnttiGateway.h library!

Provide the response strictly in the following JSON structure:
{{
  "code": "The Arduino code for Module B as a string.",
  "explanation": "A concise explanation of how the code works and interfaces with Module A as a string. Bullet points are preferred. Not JSON!"
}}
Make sure your response is in JSON format! Do not provide answer inside ```!
"""

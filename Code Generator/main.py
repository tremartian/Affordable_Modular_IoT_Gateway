# main.py

import tkinter as tk
from tkinter import ttk, messagebox
import json
from api import ChatGPTAPI
from config_manager import load_config, save_config
from button_functions import ButtonFunctions
from scrollable_frame import ScrollableFrame  # Import the ScrollableFrame class

# Load configuration
config = load_config()

# Initialize ChatGPT API Wrapper
chatgpt_api = ChatGPTAPI(api_key=None, model=None)  # Will be set when a model is selected

# ---------------------------------------------- UI STARTS HERE ----------------------------------------------------

# Initialize main window
root = tk.Tk()
root.title("IoT Gateway Code Generator")
root.geometry("1200x800")  # Adjusted window size for better visibility
root.resizable(True, True)  # Allow window to be resizable

# Create a ScrollableFrame
scrollable_frame = ScrollableFrame(root)
scrollable_frame.pack(fill="both", expand=True)

# Adjust the grid weights for the scrollable_frame.scrollable_frame to control column proportions
scrollable_frame.scrollable_frame.grid_rowconfigure(0, weight=1)     # Main content row
scrollable_frame.scrollable_frame.grid_rowconfigure(1, weight=1)     # Bottom Notebook row
scrollable_frame.scrollable_frame.grid_columnconfigure(0, weight=3)  # Make the left frame (Module A) wider
scrollable_frame.scrollable_frame.grid_columnconfigure(1, weight=1)  # Make the center frame narrower
scrollable_frame.scrollable_frame.grid_columnconfigure(2, weight=3)  # Make the right frame (Module B) wider


# --------------------------------- Helper Functions ---------------------------------

def update_selected_model(ui_components, config, model_selection_var, llm_feedback_box, button_functions):
    """Update feedback to display the selected model and initialize ChatGPT API."""
    selected_model = model_selection_var.get()
    if selected_model:
        model_info = config["models"].get(selected_model, {})
        api_key = model_info.get("key")
        if api_key:
            global chatgpt_api
            chatgpt_api = ChatGPTAPI(api_key=api_key, model=selected_model)

            # Update the ButtonFunctions instance with the new API instance
            button_functions.chatgpt_api = chatgpt_api

            # Update the feedback box
            llm_feedback_box.config(state="normal")
            llm_feedback_box.delete("1.0", "end")
            llm_feedback_box.insert("1.0", f"Selected Model: {selected_model}\n\nDescription: {model_info.get('description', 'No description available.')}")
            llm_feedback_box.config(state="disabled")
            button_functions.log_progress(f"Selected model: {selected_model}", level="INFO")
        else:
            llm_feedback_box.config(state="normal")
            llm_feedback_box.delete("1.0", "end")
            llm_feedback_box.insert("1.0", "Error: No API key found for the selected model.")
            llm_feedback_box.config(state="disabled")
            button_functions.log_progress("Selected model has no API key.", level="ERROR")
    else:
        llm_feedback_box.config(state="normal")
        llm_feedback_box.delete("1.0", "end")
        llm_feedback_box.insert("1.0", "Error: No model selected.")
        llm_feedback_box.config(state="disabled")
        button_functions.log_progress("No model selected.", level="WARNING")


def add_new_board():
    new_board = new_board_entry.get().strip()
    if new_board:
        if new_board not in config["boards"]:
            config["boards"].append(new_board)
            save_config(config)
            sensor_module_dropdown["values"] = config["boards"]
            transmission_module_dropdown["values"] = config["boards"]
            new_board_entry.delete(0, tk.END)
            llm_feedback_box.config(state="normal")
            llm_feedback_box.delete("1.0", tk.END)
            llm_feedback_box.insert(tk.END, f"Added new board: {new_board}")
            llm_feedback_box.config(state="disabled")
            button_functions.log_progress(f"Added new board: {new_board}", level="INFO")
        else:
            llm_feedback_box.config(state="normal")
            llm_feedback_box.delete("1.0", tk.END)
            llm_feedback_box.insert(tk.END, "Board already exists.")
            llm_feedback_box.config(state="disabled")
            button_functions.log_progress("Attempted to add a board that already exists.", level="WARNING")
    else:
        llm_feedback_box.config(state="normal")
        llm_feedback_box.delete("1.0", tk.END)
        llm_feedback_box.insert(tk.END, "Error: No board name entered.")
        llm_feedback_box.config(state="disabled")
        button_functions.log_progress("Attempted to add a board without providing a name.", level="ERROR")


def copy_to_clipboard(text_box):
    """Copy code from a text box to the clipboard."""
    if text_box:
        text_box_content = text_box.get("1.0", "end").strip()
        if text_box_content:
            root.clipboard_clear()
            root.clipboard_append(text_box_content)
            root.update()
            messagebox.showinfo("Copy to Clipboard", "Code copied to clipboard.")
            button_functions.log_progress("Code copied to clipboard.", level="INFO")
        else:
            messagebox.showerror("Copy to Clipboard", "Error: No code to copy.")
            button_functions.log_progress("Attempted to copy code: No code available.", level="ERROR")


# Scrollable Text Widget Helper
def create_scrollable_text(parent, height, width, state="normal", bg=None):
    frame = tk.Frame(parent)
    text_widget = tk.Text(
        frame,
        height=height,
        width=width,
        state=state,
        wrap="none",  # Disable wrapping for better horizontal scrolling
        bg=bg,
        font=("Courier", 10)  # Use monospaced font for code
    )
    y_scrollbar = tk.Scrollbar(frame, command=text_widget.yview)
    x_scrollbar = tk.Scrollbar(frame, orient="horizontal", command=text_widget.xview)
    text_widget.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
    text_widget.pack(side="left", fill="both", expand=True)
    y_scrollbar.pack(side="right", fill="y")
    x_scrollbar.pack(side="bottom", fill="x")
    return frame, text_widget


def create_description_box(parent, height, width, state="normal", bg=None):
    """Create a scrollable text box for text with word wrapping."""
    frame = tk.Frame(parent)
    text_widget = tk.Text(
        frame,
        height=height,
        width=width,
        state=state,
        wrap="word",  # Enable word wrapping for descriptions
        bg=bg or "white",  # Default background for descriptions
        font=("Arial", 9)  # Proportional font for text
    )
    y_scrollbar = tk.Scrollbar(frame, command=text_widget.yview)
    text_widget.configure(yscrollcommand=y_scrollbar.set)
    text_widget.pack(side="left", fill="both", expand=True)
    y_scrollbar.pack(side="right", fill="y")
    return frame, text_widget


# Sensor examples

def load_sensor_examples():
    """Load sensor examples from a JSON file."""
    try:
        with open("sensors.json", "r") as file:
            return json.load(file).get("sensors", {})
    except FileNotFoundError:
        messagebox.showerror("File Not Found", "sensors.json file not found.")
        return {}
    except json.JSONDecodeError:
        messagebox.showerror("JSON Error", "Error decoding sensors.json.")
        return {}


def fill_example_details(event):
    """Fill in example details based on the selected sensor."""
    sensor_key = sensor_examples_var.get()
    if sensor_key in sensor_data:
        example = sensor_data[sensor_key]

        # Fill in the related UI components
        sensor_type_entry.delete(0, tk.END)
        sensor_type_entry.insert(0, example["type"])

        sensor_desc_entry.delete("1.0", "end")
        sensor_desc_entry.insert("1.0", example["description"])

        sensor_tech_dropdown.set(example["technology"])
        sensor_module_dropdown.set(example["board"])

        # Format data as JSON and insert it
        data_format_box.config(state="normal")
        data_format_box.delete("1.0", "end")
        data_format_box.insert("1.0", json.dumps(example["data_format"], indent=4))
        data_format_box.config(state="normal")  # Ensure it's editable
        button_functions.log_progress(f"Loaded example details for sensor: {sensor_key}", level="INFO")
    else:
        button_functions.log_progress(f"No example data found for sensor: {sensor_key}", level="WARNING")


# Function to update sensor technology details dynamically
def update_sensor_tech_details(event):
    selected_tech = sensor_tech_dropdown.get()
    if selected_tech in config["technologies"]:
        details = config["technologies"][selected_tech]
        sensor_tech_label.config(text=f"Details: {details}")
        button_functions.log_progress(f"Selected technology for Module A: {selected_tech}", level="INFO")
    else:
        sensor_tech_label.config(text="Details not available for the selected technology.")
        button_functions.log_progress(f"Selected unknown technology for Module A: {selected_tech}", level="WARNING")


def update_sensor_tech_detailsB(event):
    selected_tech = endpoint_tech_dropdown.get()
    if selected_tech in config["technologies"]:
        details = config["technologies"][selected_tech]
        endpoint_tech_label.config(text=f"Details: {details}")
        button_functions.log_progress(f"Selected technology for Module B: {selected_tech}", level="INFO")
    else:
        endpoint_tech_label.config(text="Details not available for the selected technology.")
        button_functions.log_progress(f"Selected unknown technology for Module B: {selected_tech}", level="WARNING")


# --------------------------------- UI Elements ---------------------------------

# Left Frame for Module A (Receiver)
module_a_frame = tk.LabelFrame(scrollable_frame.scrollable_frame, text="Module A: Receiver (Sensor)", padx=10, pady=10)
module_a_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Load sensors data from JSON
sensor_data = load_sensor_examples()

# Dropdown for selecting sensor examples
sensor_examples_var = tk.StringVar()
sensor_examples_dropdown = ttk.Combobox(
    module_a_frame, textvariable=sensor_examples_var, state="readonly"
)
sensor_examples_dropdown.pack(anchor="w", pady=5)
sensor_examples_dropdown["values"] = list(sensor_data.keys())

# Bind dropdown selection event
sensor_examples_dropdown.bind("<<ComboboxSelected>>", fill_example_details)


tk.Label(module_a_frame, text="Sensor Type or Model Name (e.g., temperature sensor, Ruuvitag):").pack(anchor="w")
sensor_type_entry = tk.Entry(module_a_frame, width=40)
sensor_type_entry.pack(anchor="w")

tk.Label(module_a_frame, text="Sensor Description (e.g., Measures temperature from -40°C to +85°C):").pack(anchor="w")
sensor_desc_frame, sensor_desc_entry = create_description_box(module_a_frame, height=10, width=40)
sensor_desc_frame.pack(anchor="w", fill="x", pady=5)

# Wireless Communication Technology Section
tk.Label(module_a_frame, text="Wireless Communication Technology:").pack(anchor="w")
# Dropdown for selecting technology
sensor_tech_dropdown = ttk.Combobox(module_a_frame, values=list(config["technologies"].keys()), state="readonly")
sensor_tech_dropdown.pack(anchor="w")
# Bind selection event to update details
sensor_tech_dropdown.bind("<<ComboboxSelected>>", update_sensor_tech_details)
# Label for displaying technology details
sensor_tech_label = tk.Label(module_a_frame, text="Select a technology to see details.", wraplength=300, justify="left")
sensor_tech_label.pack(anchor="w", pady=5)

tk.Label(module_a_frame, text="Development Board:").pack(anchor="w")
sensor_module_var = tk.StringVar()
sensor_module_dropdown = ttk.Combobox(module_a_frame, textvariable=sensor_module_var, values=config["boards"], state="readonly")
sensor_module_dropdown.pack(anchor="w")

tk.Label(module_a_frame, text="Generated Code for Module A:").pack(anchor="w")
module_a_code_frame, module_a_code_box = create_scrollable_text(module_a_frame, height=15, width=70)
module_a_code_frame.pack(fill="x", pady=10)

tk.Button(module_a_frame, text="Copy Code", command=lambda: button_functions.copy_code_to_clipboard(module_a_code_box)).pack(pady=5)

# Right Frame for Module B (Transmitter)
module_b_frame = tk.LabelFrame(scrollable_frame.scrollable_frame, text="Module B: Transmitter (Endpoint)", padx=10, pady=10)
module_b_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

tk.Label(module_b_frame, text="Endpoint Type or Name (e.g., REST, Google Firebase):").pack(anchor="w")
endpoint_type_entry = tk.Entry(module_b_frame, width=40)
endpoint_type_entry.pack(anchor="w")

tk.Label(module_b_frame, text="Endpoint Description (e.g., REST API URL and credentials):").pack(anchor="w")
endpoint_desc_frame, endpoint_desc_entry = create_description_box(module_b_frame, height=10, width=40)
endpoint_desc_frame.pack(anchor="w", fill="x", pady=5)

# Wireless Communication Technology Section
tk.Label(module_b_frame, text="Wireless Communication Technology:").pack(anchor="w")
# Dropdown for selecting technology
endpoint_tech_dropdown = ttk.Combobox(module_b_frame, values=list(config["technologies"].keys()), state="readonly")
endpoint_tech_dropdown.pack(anchor="w")
# Bind selection event to update details
endpoint_tech_dropdown.bind("<<ComboboxSelected>>", update_sensor_tech_detailsB)
# Label for displaying technology details
endpoint_tech_label = tk.Label(module_b_frame, text="Select a technology to see details.", wraplength=300, justify="left")
endpoint_tech_label.pack(anchor="w", pady=5)

tk.Label(module_b_frame, text="Development Board:").pack(anchor="w")
transmission_module_var = tk.StringVar()
transmission_module_dropdown = ttk.Combobox(module_b_frame, textvariable=transmission_module_var, values=config["boards"], state="readonly")
transmission_module_dropdown.pack(anchor="w")

tk.Label(module_b_frame, text="Generated Code for Module B:").pack(anchor="w")
module_b_code_frame, module_b_code_box = create_scrollable_text(module_b_frame, height=15, width=70)
module_b_code_frame.pack(fill="x", pady=10)

tk.Button(module_b_frame, text="Copy Code", command=lambda: button_functions.copy_code_to_clipboard(module_b_code_box)).pack(pady=5)

# Center Frame for LLM Feedback and Board Management
center_frame = tk.LabelFrame(scrollable_frame.scrollable_frame, text="Feedback from LLM and Board Management", padx=10, pady=10, width=300)
center_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Prevent the frame from resizing to fit its content
center_frame.grid_propagate(False)

# Feedback from LLM
tk.Label(center_frame, text="Feedback from LLM:").pack(anchor="w")

# Scrollable text box for feedback
llm_feedback_frame, llm_feedback_box = create_description_box(center_frame, height=15, width=30, state="disabled", bg="lightgray")
llm_feedback_frame.pack(fill="x", pady=5)

# Add New Development Board Section
tk.Label(center_frame, text="Add New Development Board:").pack(anchor="w", pady=10)
board_entry_frame = tk.Frame(center_frame)
board_entry_frame.pack(anchor="w", pady=5, fill="x")

# New board entry
new_board_entry = tk.Entry(board_entry_frame, width=30)
new_board_entry.pack(side="left", padx=(0, 5))
add_board_button = tk.Button(board_entry_frame, text="Add Board")
add_board_button.pack(side="left")

# Dropdown for Model Selection
tk.Label(center_frame, text="Select ChatGPT Model:").pack(anchor="w", pady=5)
model_selection_var = tk.StringVar()  # Variable to store the selected model
model_dropdown = ttk.Combobox(center_frame, textvariable=model_selection_var, state="readonly", width=28)
model_dropdown["values"] = list(config["models"].keys())  # Populate dropdown with model names from config
model_dropdown.pack(fill="x", pady=5)

# Data Format Section
tk.Label(center_frame, text="Define Data Format for Communication:").pack(anchor="w", pady=10)
data_format_frame, data_format_box = create_scrollable_text(center_frame, height=10, width=40, state="normal")  # Ensure state="normal"
data_format_frame.pack(anchor="w", fill="x", pady=5)

# Arduino IDE Errors Section
tk.Label(center_frame, text="Code modification requests and Arduino IDE Errors (paste errors from IDE here):").pack(anchor="w")
error_log_frame, modification_requests_box = create_scrollable_text(center_frame, height=20, width=35)
error_log_frame.pack(fill="x", pady=5)

# Bottom Tabs for Example Code and Progress Log
notebook = ttk.Notebook(scrollable_frame.scrollable_frame)
notebook.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

# Create frames for each tab
example_tab_1 = tk.Frame(notebook)
example_tab_2 = tk.Frame(notebook)
progress_log_tab = tk.Frame(notebook)  # **Added Progress Log Tab**

# Add tabs to the notebook
notebook.add(example_tab_1, text="Example Code 1")
notebook.add(example_tab_2, text="Example Code 2")
notebook.add(progress_log_tab, text="Progress Log")  # **Added Progress Log Tab**

# Create scrollable text boxes for example tabs
example_tab_1_frame, example_tab_1_text = create_scrollable_text(example_tab_1, height=10, width=140)
example_tab_2_frame, example_tab_2_text = create_scrollable_text(example_tab_2, height=10, width=140)
example_tab_1_frame.pack(fill="both", expand=True)
example_tab_2_frame.pack(fill="both", expand=True)

# Create a scrollable text box for the progress log tab
progress_log_frame, progress_log_box = create_scrollable_text(progress_log_tab, height=20, width=140, state="disabled", bg="black")
progress_log_box.config(fg="white", bg="black")  # Set text color to white for better visibility
progress_log_frame.pack(fill="both", expand=True)

# Pass UI Components to Button Functions
ui_components = {
    "sensor_type_entry": sensor_type_entry,
    "sensor_desc_entry": sensor_desc_entry,
    "sensor_tech_dropdown": sensor_tech_dropdown,
    "sensor_module_dropdown": sensor_module_dropdown,
    "endpoint_type_entry": endpoint_type_entry,
    "endpoint_desc_box": endpoint_desc_entry,
    "endpoint_tech_dropdown": endpoint_tech_dropdown,
    "endpoint_board_dropdown": transmission_module_dropdown,
    "data_format_box": data_format_box,
    "feedback_box": llm_feedback_box,
    "module_a_code_box": module_a_code_box,
    "module_b_code_box": module_b_code_box,
    "new_board_entry": new_board_entry,
    "example_tab_1_text": example_tab_1_text,
    "example_tab_2_text": example_tab_2_text,
    #"error_log_box": error_log_box,
    "modification_requests_box": modification_requests_box,
    "progress_log_box": progress_log_box  # **Added Progress Log Box to UI Components**
}

# Initialize ButtonFunctions instance
button_functions = ButtonFunctions(chatgpt_api, ui_components)

# Now that button_functions is defined, bind the model dropdown selection event
model_dropdown.bind("<<ComboboxSelected>>", lambda e: update_selected_model(ui_components, config, model_selection_var, llm_feedback_box, button_functions))

# Test Log Message
button_functions.log_progress("Application started successfully.", level="INFO")

# Connect Buttons to Functions
tk.Button(module_a_frame, text="Generate Code For Module A", command=lambda: button_functions.generate_code_for_module("module_a")).pack(pady=5)
tk.Button(module_b_frame, text="Generate Code For Module B", command=lambda: button_functions.generate_code_for_module("module_b")).pack(pady=5)
tk.Button(center_frame, text="Suggest Data Format", command=button_functions.suggest_data_format).pack(pady=5)

# Refine button using button_functions instance
tk.Button(center_frame, text="Refine Last Generated Code", command=button_functions.refine_last_generated_code).pack(pady=5)

# Add Board button configuration
add_board_button.config(command=add_new_board)

# Run the application
root.mainloop()

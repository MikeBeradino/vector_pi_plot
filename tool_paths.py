import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from xml.dom import minidom
import re
import math
import serial.tools.list_ports  # For serial port discovery
import serial  # For serial communication
import time
from tkinter import filedialog

from svg.path import parse_path
from xml.dom import minidom
#from print_module import HPGLPrinter

# Plotter speeds in mm/s
SLEWING_SPEED = 400  # Pen-up speed
DRAWING_SPEED = 100  # Pen-down speed

# Global variables for tool path window
canvas_hpgl = None
fig_hpgl = None
hpgl_code = ""
current_svg = "vector_output.svg"  # Set to the uploaded SVG file path
serial_connection = None  # To store the serial connection object

# After the root window is created, create `BooleanVar` for border toggling
root = tk.Tk()
root.withdraw()  # Hide the window
include_border = tk.BooleanVar(value=True)  # Create after the root window is initialized

# Serial port tools - list available ports and initialize the baud rate
available_ports = [port.device for port in serial.tools.list_ports.comports()]
baud_rates = [75, 110, 150, 200, 300, 600, 1200, 2400, 2800, 9600, 19200, 38400, 57600, 115200]  # Available baud rates

# Add this near the top of your script
pen_color_mapping = {
    1: 'green',
    2: 'red',
    3: 'blue',
    4: 'gray',  # Default pen color
    5: 'yellow',
    6: 'pink'
}

# Serial connection helper functions
def connect_to_plotter(selected_port, selected_baud_rate):
    global serial_connection
    try:
        # Close any existing connection
        if serial_connection:
            serial_connection.close()

        # Establish new connection
        serial_connection = serial.Serial(selected_port, selected_baud_rate, timeout=1)
        messagebox.showinfo("Success", f"Connected to {selected_port} at {selected_baud_rate} baud.")
    except serial.SerialException as e:
        messagebox.showerror("Connection Error", str(e))

def send_hpgl_command(command):
    if serial_connection:
        try:
            serial_connection.write(f"{command}\n".encode())
            messagebox.showinfo("Success", f"Sent HPGL command: {command}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send command: {e}")
    else:
        messagebox.showerror("Error", "Not connected to the plotter.")

def send_hpgl_code_from_vect   ():
    """Send HPGL code to the plotter."""
    global hpgl_code
    if not serial_connection:
        messagebox.showerror("Error", "No connection to the plotter.")
        return

    try:
        lines = hpgl_code.splitlines()
        for line in lines:
            serial_connection.write(f"{line}\n".encode())
            serial_connection.flush()  # Ensure all data is sent
            time.sleep(0.4)  # Add a small delay to allow the plotter to process each command
            print(line)



    except Exception as e:
        messagebox.showerror("Error", f"Failed to send HPGL code: {e}")

# Helper function to parse 'd' attribute from path elements (basic M and L commands)
def parse_svg_path(path_data):
    commands = re.findall(r'[MLZmlz][^MLZmlz]*', path_data)
    points = []
    current_pos = (0, 0)

    for command in commands:
        cmd_type = command[0].upper()  # Get command (M, L, etc.), and make it uppercase
        params = re.findall(r"[-+]?\d*\.\d+|\d+", command[1:])  # Extract numbers

        if cmd_type == 'M':  # Move to
            x, y = float(params[0]), float(params[1])
            current_pos = (x, y)
            points.append(current_pos)

        elif cmd_type == 'L':  # Line to
            x, y = float(params[0]), float(params[1])
            current_pos = (x, y)
            points.append(current_pos)

        elif cmd_type == 'Z':  # Close path
            points.append(points[0])  # Close the shape by returning to the start

    return points

# Function to get the dimensions of the SVG canvas
def convert_to_pixels(value_str):
    try:
        if not value_str or value_str.strip() == "":
            return None
        value_str = value_str.strip()
        if value_str.endswith('px'):
            return float(value_str[:-2])
        elif value_str.endswith('pt'):
            return float(value_str[:-2]) * 1.333
        elif value_str.endswith('mm'):
            return float(value_str[:-2]) * 3.7795275591
        elif value_str.endswith('cm'):
            return float(value_str[:-2]) * 37.795275591
        elif value_str.endswith('in'):
            return float(value_str[:-2]) * 96
        elif value_str.endswith('%'):
            print(f"Warning: Percentage unit '{value_str}' not supported. Returning None.")
            return None
        else:
            return float(value_str)
    except ValueError:
        print(f"Could not parse dimension '{value_str}'. Returning None.")
        return None



def get_svg_canvas_size(svg_filename):
    svg_doc = minidom.parse(svg_filename)
    svg_element = svg_doc.getElementsByTagName('svg')[0]

    width = svg_element.getAttribute('width')
    height = svg_element.getAttribute('height')
    print(f"SVG raw width: '{width}', height: '{height}'")

    width_px = convert_to_pixels(width)
    height_px = convert_to_pixels(height)

    # Fallback to viewBox if dimensions fail
    if not width_px or not height_px or width_px <= 0 or height_px <= 0:
        view_box = svg_element.getAttribute('viewBox')
        if view_box:
            print("Falling back to viewBox dimensions.")
            parts = view_box.strip().split()
            if len(parts) == 4:
                width_px = float(parts[2])
                height_px = float(parts[3])

    return width_px, height_px


# Function to convert from pixels (px) to points (pt)
def convert_px_to_pt(px_value):
    return px_value / 1.333


from svg.path import parse_path
from xml.dom import minidom

def parse_svg_path_accurate(svg_filename):
    doc = minidom.parse(svg_filename)
    path_elements = doc.getElementsByTagName('path')
    all_points = []

    for path_el in path_elements:
        d = path_el.getAttribute('d')
        if not d:
            continue
        path = parse_path(d)

        # Sample points along the path
        sampled_points = []
        for segment in path:
            for t in [i / 10.0 for i in range(11)]:  # 10 segments per curve/line
                point = segment.point(t)
                sampled_points.append((point.real, point.imag))

        all_points.append(sampled_points)

    doc.unlink()
    return all_points


# Updated function to convert SVG to HPGL, excluding the canvas border and mapping pen colors
from xml.dom import minidom
from svg.path import parse_path
import re
import tkinter as tk

def convert_svg_to_hpgl():
    global hpgl_code

    svg_doc = minidom.parse(current_svg)
    path_elements = svg_doc.getElementsByTagName('path')

    # Initialize HPGL
    hpgl_code_lines = ["IN;", "PA;"]

    # Get SVG canvas size
    canvas_width_px, canvas_height_px = get_svg_canvas_size(current_svg)

    # HPGL space
    HPGL_MAX_UNITS_X = 13000
    HPGL_MAX_UNITS_Y = 16800

    # Scale to fit canvas
    x_scale = HPGL_MAX_UNITS_X / canvas_width_px
    y_scale = HPGL_MAX_UNITS_Y / canvas_height_px
    uniform_scale = min(x_scale, y_scale)

    print(f"Uniform scale factor: {uniform_scale}")

    seen_paths = set()

    for path in path_elements:
        path_data = path.getAttribute('d')
        path_color = path.getAttribute('style')

        if not path_data or path_data in seen_paths:
            continue  # skip duplicates or empty paths
        seen_paths.add(path_data)

        # Extract pen number from stroke color
        pen_number = 4
        if path_color:
            color_match = re.search(r'stroke:([^;]+);', path_color)
            if color_match:
                color = color_match.group(1).strip().upper()
                color_to_pen = {
                    '#008000': 1,  # Green
                    '#FF0000': 2,  # Red
                    '#0000FF': 3,  # Blue
                    '#808080': 4,  # Gray/Black
                    '#FFFF00': 5,  # Yellow
                    '#FFC0CB': 6,  # Pink
                }
                pen_number = color_to_pen.get(color, 4)

        hpgl_code_lines.append(f"SP{pen_number};")

        # Parse and convert path
        try:
            path_obj = parse_path(path_data)
        except Exception as e:
            print(f"Error parsing path: {e}")
            continue

        for segment in path_obj:
            if segment.length(error=1e-2) == 0:
                continue  # skip zero-length segments

            # Sample points along the segment
            points = [(segment.point(t).real, segment.point(t).imag) for t in [i / 10.0 for i in range(11)]]
            if not points:
                continue

            # Start new path
            start_x, start_y = points[0]
            hpgl_code_lines.append(f"PU{int(start_x * uniform_scale)},{int(start_y * uniform_scale)};")
            hpgl_code_lines.append("PD;")

            last_pt = (int(start_x * uniform_scale), int(start_y * uniform_scale))
            for x, y in points[1:]:
                scaled_x = int(x * uniform_scale)
                scaled_y = int(y * uniform_scale)
                if (scaled_x, scaled_y) != last_pt:
                    hpgl_code_lines.append(f"PA{scaled_x},{scaled_y};")
                    last_pt = (scaled_x, scaled_y)

            hpgl_code_lines.append("PU;")

    # Finalize HPGL output
    hpgl_code = '\n'.join(hpgl_code_lines)
    hpgl_text_box.delete(1.0, tk.END)
    hpgl_text_box.insert(tk.END, hpgl_code)

    print("Generated HPGL Code:\n", hpgl_code)

    with open("output.hpgl", "w") as hpgl_file:
        hpgl_file.write(hpgl_code)


# Function to calculate distance between two points
def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - y1) ** 2 + (y2 - y1) ** 2)

# Updated function to estimate plotting time based on HPGL code
def estimate_plotting_time():
    hpgl_commands = hpgl_code.splitlines()
    current_pos = (0, 0)
    total_slewing_distance = 0  # Pen-up movement
    total_drawing_distance = 0  # Pen-down movement
    pen_down = False

    for cmd in hpgl_commands:
        if cmd.startswith('PU'):  # Pen up (slewing)
            params = re.findall(r"[-+]?\d*\.\d+|\d+", cmd)
            if params:
                next_pos = (float(params[0]), float(params[1]))
                total_slewing_distance += calculate_distance(current_pos[0], current_pos[1], next_pos[0], next_pos[1])
                current_pos = next_pos
            pen_down = False

        elif cmd.startswith('PD'):  # Pen down (drawing)
            pen_down = True

        elif cmd.startswith('PA'):  # Absolute line to point
            params = re.findall(r"[-+]?\d*\.\d+|\d+", cmd)
            if params:
                next_pos = (float(params[0]), float(params[1]))
                if pen_down:
                    total_drawing_distance += calculate_distance(current_pos[0], current_pos[1], next_pos[0], next_pos[1])
                current_pos = next_pos

    # Calculate time for slewing and drawing
    slewing_time = total_slewing_distance / SLEWING_SPEED  # in seconds
    drawing_time = total_drawing_distance / DRAWING_SPEED  # in seconds
    total_time = slewing_time + drawing_time

    # Convert to minutes and seconds
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)

    messagebox.showinfo("Plotting Time Estimate", f"Estimated plotting time: {minutes} minutes, {seconds} seconds")

# Updated function to visualize HPGL commands with pen-up movements drawn first
def visualize_hpgl(hpgl_preview_frame, pen_color_mapping):
    global canvas_hpgl, fig_hpgl
    if fig_hpgl is None:
        fig_hpgl, ax_hpgl = plt.subplots()
    else:
        fig_hpgl.clear()
        ax_hpgl = fig_hpgl.add_subplot(111)

    # Extract Y-coordinates from the HPGL commands
    y_coords = []
    hpgl_commands = hpgl_code.splitlines()

    for cmd in hpgl_commands:
        if cmd.startswith(('PU', 'PA')):  # Pen-up or Pen-down commands contain coordinates
            params = re.findall(r"[-+]?\d*\.\d+|\d+", cmd)
            if len(params) >= 2:  # Ensure at least two parameters are present (X, Y)
                y_coords.append(float(params[1]))  # Append Y-coordinate

    if not y_coords:
        print("No Y-coordinates found in HPGL code.")
        return  # Avoid further processing if there are no coordinates

    # Get the maximum Y value to flip the Y coordinates correctly
    max_y = max(y_coords)

    # Prepare lists for pen-up and pen-down movements
    pen_up_movements = []
    pen_down_movements = []
    current_pos = (0, 0)
    pen_down = False
    current_color = 'black'  # Default color

    for cmd in hpgl_commands:
        if cmd.startswith('SP'):
            # Pen select command (change pen)
            pen_number = int(cmd[2])  # Extract pen number (SP1, SP2, etc.)
            current_color = pen_color_mapping.get(pen_number, 'black')  # Get the color for the selected pen
            print(f"Changing to pen {pen_number} with color {current_color}")

        elif cmd.startswith('PU'):
            # Pen Up: Move the pen without drawing
            params = re.findall(r"[-+]?\d*\.\d+|\d+", cmd)
            if len(params) >= 2:
                next_pos = (float(params[0]), float(params[1]))
                next_pos = (next_pos[0], max_y - next_pos[1])  # Flip the Y-coordinate
                pen_up_movements.append((current_pos, next_pos))  # Store pen-up movement
                current_pos = next_pos
            pen_down = False

        elif cmd.startswith('PD'):
            # Pen Down: Start drawing
            pen_down = True

        elif cmd.startswith('PA'):
            # Absolute line to point (either Pen Up or Pen Down)
            params = re.findall(r"[-+]?\d*\.\d+|\d+", cmd)
            if len(params) >= 2:
                next_pos = (float(params[0]), float(params[1]))
                next_pos = (next_pos[0], max_y - next_pos[1])  # Flip the Y-coordinate
                if pen_down:
                    pen_down_movements.append((current_pos, next_pos, current_color))  # Store pen-down movement with color
                current_pos = next_pos

    # Draw pen-up movements first (dashed blue lines)
    for start, end in pen_up_movements:
        ax_hpgl.plot([start[0], end[0]], [start[1], end[1]], color='lightblue', linestyle='dashed', linewidth=1)

    # Draw pen-down movements next (use stroke/pen color)
    for start, end, color in pen_down_movements:
        ax_hpgl.plot([start[0], end[0]], [start[1], end[1]], color=color, linewidth=1)

    ax_hpgl.set_title("HPGL Tool Path with Pen Colors")
    ax_hpgl.set_aspect('equal')
    ax_hpgl.axis('off')

    if canvas_hpgl:
        canvas_hpgl.get_tk_widget().destroy()

    canvas_hpgl = FigureCanvasTkAgg(fig_hpgl, master=hpgl_preview_frame)
    canvas_hpgl.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    canvas_hpgl.draw()

# Main function to open the tool path window
def open_tool_path_window(root):
    new_window = tk.Toplevel(root)
    new_window.title("SVG and HPGL Toolpath Previewer with Time Estimate")

    # Create layout for the new window
    frame = ttk.Frame(new_window, padding="10")
    frame.grid(row=0, column=0, sticky="nsew")

    # Button to load and display the SVG and HPGL
    load_button = ttk.Button(frame, text="Convert and Preview HPGL", command=lambda: [convert_svg_to_hpgl(), visualize_hpgl(hpgl_preview_frame, pen_color_mapping)])
    load_button.grid(row=0, column=0, padx=10, pady=5)

    # Button to estimate plotting time
    time_button = ttk.Button(frame, text="Estimate Plotting Time", command=estimate_plotting_time)
    time_button.grid(row=0, column=1, padx=10, pady=5)

    # Add a checkbox to toggle whether to include the border or ignore it
    border_checkbox = ttk.Checkbutton(frame, text="Include Border", variable=include_border)
    border_checkbox.grid(row=0, column=2, padx=10, pady=5)

    # Frame for HPGL toolpath preview
    global hpgl_preview_frame
    hpgl_preview_frame = ttk.Frame(new_window, padding="10")
    hpgl_preview_frame.grid(row=1, column=0, sticky="nsew")

    # HPGL code display text box
    global hpgl_text_box
    hpgl_text_box = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=40, height=15)
    hpgl_text_box.grid(row=1, column=0, padx=10, pady=5)

    # Set up a flexible grid layout for the new window
    new_window.columnconfigure(0, weight=1)
    new_window.columnconfigure(1, weight=1)
    new_window.rowconfigure(1, weight=1)

    select_button = ttk.Button(frame, text="Select SVG and Convert", command=select_svg_and_convert)
    select_button.grid(row=0, column=4, padx=10, pady=5)

# Serial Port Testing Module
def open_serial_port_window(root):
    serial_window = tk.Toplevel(root)
    serial_window.title("Serial Port Testing Tool")

    # Create layout for the serial tool window
    frame = ttk.Frame(serial_window, padding="10")
    frame.grid(row=0, column=0, sticky="nsew")

    # Serial port selection dropdown
    serial_port_label = ttk.Label(frame, text="Select Serial Port:")
    serial_port_label.grid(row=0, column=0, padx=10, pady=5)
    serial_port_dropdown = ttk.Combobox(frame, values=available_ports)
    serial_port_dropdown.grid(row=0, column=1, padx=10, pady=5)

    # Baud rate selection dropdown
    baud_rate_label = ttk.Label(frame, text="Select Baud Rate:")
    baud_rate_label.grid(row=1, column=0, padx=10, pady=5)
    baud_rate_dropdown = ttk.Combobox(frame, values=baud_rates)
    baud_rate_dropdown.grid(row=1, column=1, padx=10, pady=5)
    baud_rate_dropdown.set("9600")  # Set default baud rate

    # Connect button
    connect_button = ttk.Button(frame, text="Connect", command=lambda: connect_to_plotter(serial_port_dropdown.get(), baud_rate_dropdown.get()))
    connect_button.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

    # Command buttons for HPGL test commands
    ttk.Button(frame, text="Pen Up", command=lambda: send_hpgl_command("PU")).grid(row=3, column=0, padx=10, pady=5)
    ttk.Button(frame, text="Pen Down", command=lambda: send_hpgl_command("PD")).grid(row=3, column=1, padx=10, pady=5)
    ttk.Button(frame, text="Change to Pen 1", command=lambda: send_hpgl_command("SP1")).grid(row=4, column=0, padx=10, pady=5)
    ttk.Button(frame, text="Change to Pen 2", command=lambda: send_hpgl_command("SP2")).grid(row=4, column=1, padx=10, pady=5)
    ttk.Button(frame, text="Change to Pen 3", command=lambda: send_hpgl_command("SP3")).grid(row=5, column=0, padx=10, pady=5)

    # Set up grid layout for flexibility
    serial_window.columnconfigure(0, weight=1)
    serial_window.rowconfigure(1, weight=1)

def select_svg_and_convert():
    global current_svg
    file_path = filedialog.askopenfilename(
        title="Select SVG File",
        filetypes=[("SVG files", "*.svg")]
    )
    if file_path:
        current_svg = file_path
        convert_svg_to_hpgl()
        visualize_hpgl(hpgl_preview_frame, pen_color_mapping)


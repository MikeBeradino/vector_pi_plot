import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from xml.dom import minidom
import re
import math

# Plotter speeds in mm/s
SLEWING_SPEED = 400  # Pen-up speed
DRAWING_SPEED = 100  # Pen-down speed

# Global variables for tool path window
canvas_hpgl = None
fig_hpgl = None
hpgl_code = ""
current_svg = "vector_output.svg"  # Set to the uploaded SVG file path

# Global variable to track border toggle state
include_border = tk.BooleanVar(value=True)

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
# Function to convert unit strings to float values in pixels
def convert_to_pixels(value_str):
    if value_str.endswith('px'):
        return float(value_str[:-2])  # Remove 'px' and convert to float
    elif value_str.endswith('pt'):
        return float(value_str[:-2]) * 1.333  # Convert 'pt' to 'px'
    else:
        return float(value_str)  # Assume it's already in pixels or has no units

# Function to get the dimensions of the SVG canvas, handling unit conversions
def get_svg_canvas_size(svg_filename):
    svg_doc = minidom.parse(svg_filename)
    svg_element = svg_doc.getElementsByTagName('svg')[0]
    width = svg_element.getAttribute('width')
    height = svg_element.getAttribute('height')

    # Convert width and height to pixels
    width_px = convert_to_pixels(width)
    height_px = convert_to_pixels(height)

    return width_px, height_px


# Function to convert SVG to HPGL, excluding the canvas border
# Helper function to convert from points (pt) to pixels (px)
def convert_pt_to_px(pt_value):
    return float(pt_value) * 1.333


# Function to get the canvas size in pixels from the SVG file
def get_svg_canvas_size_in_px(svg_filename):
    svg_doc = minidom.parse(svg_filename)
    svg_element = svg_doc.getElementsByTagName('svg')[0]
    width = svg_element.getAttribute('width')
    height = svg_element.getAttribute('height')

    # Convert from pt to px if needed
    width_px = convert_pt_to_px(width[:-2]) if width.endswith('pt') else float(width)
    height_px = convert_pt_to_px(height[:-2]) if height.endswith('pt') else float(height)

    return width_px, height_px


# Function to convert from pixels (px) to points (pt) for consistency in units
def convert_px_to_pt(px_value):
    return px_value / 1.333


# Define a color-to-pen mapping (adjust based on your plotter's setup)
color_to_pen = {'#FF0000': 1,  # Red
    '#0000FF': 2,  # Blue
    '#00FF00': 3,  # Green
    '#000000': 4,  # Black (default)
    '#FFFF00': 5,  # Yellow
    '#FF00FF': 6,  # Pink
}

# Define the pen color mapping
pen_color_mapping = {
    1: '#FF0000',  # Red
    2: '#0000FF',  # Blue
    3: '#00FF00',  # Green
    4: '#000000',  # Black
    5: '#FFFF00',  # Yellow
    6: '#FF00FF',  # Pink
}



# Function to convert from pixels (px) to points (pt) for consistency in units
def convert_px_to_pt(px_value):
    return px_value / 1.333


# Updated function to convert SVG to HPGL, excluding the canvas border and mapping pen colors
def convert_svg_to_hpgl():
    global hpgl_code
    svg_doc = minidom.parse(current_svg)
    path_elements = svg_doc.getElementsByTagName('path')

    # Get the canvas size in pixels and convert to points for comparison
    canvas_width_px, canvas_height_px = get_svg_canvas_size_in_px(current_svg)
    canvas_width_pt = convert_px_to_pt(canvas_width_px)
    canvas_height_pt = convert_px_to_pt(canvas_height_px)
    print(f"Canvas size in points: {canvas_width_pt}x{canvas_height_pt}")

    # Calculate the four corners of the canvas in points
    top_left = (0.0, 0.0)
    top_right = (canvas_width_pt, 0.0)
    bottom_left = (0.0, canvas_height_pt)
    bottom_right = (canvas_width_pt, canvas_height_pt)

    print(f"Canvas corners in points: {top_left}, {top_right}, {bottom_left}, {bottom_right}")

    hpgl_code_lines = []

    # Process path elements for toolpath generation
    for path in path_elements:
        path_data = path.getAttribute('d')
        path_color = path.getAttribute('style')  # Extract the style attribute for color

        # Extract the fill or stroke color from the 'style' attribute (assuming 'stroke' or 'fill' contains color)
        color_match = re.search(r'stroke:([^;]+);', path_color)


        if color_match:

            color = color_match.group(1).strip()
            color = color.upper()  # Clean up whitespace


            # Map the color to a plotter pen using the color-to-pen mapping
            pen_number = color_to_pen.get(color, 4)  # Default to black (pen 4) if color not found

            # Generate HPGL command to select the correct pen
            hpgl_code_lines.append(f"SP{pen_number};")  # Select Pen command

        points = parse_svg_path(path_data)

        print(f"Parsed points: {points}")  # Debugging print to see the parsed points

        if points:
            # Check if the points form a rectangle matching the canvas size in points
            if len(points) == 5 and ((points[0], points[1], points[2], points[3]) == (top_left, top_right, bottom_right, bottom_left) or (points[0], points[1], points[2], points[3]) == (bottom_left, bottom_right, top_right, top_left)):
                # Skip this rectangle, as it represents the canvas border
                print("Skipping canvas border rectangle")
                continue

            # Move to the start of the path (Pen Up)
            hpgl_code_lines.append(f"PU{int(points[0][0])},{int(points[0][1])};")
            hpgl_code_lines.append("PD")  # Pen Down to start drawing

            # Generate the HPGL path for the remaining points
            for x, y in points[1:]:
                hpgl_code_lines.append(f"PA{int(x)},{int(y)};")
            hpgl_code_lines.append("PU;")  # Pen Up at the end of the path

    hpgl_code = '\n'.join(hpgl_code_lines)

    # Display the HPGL code in the text box
    hpgl_text_box.delete(1.0, tk.END)
    hpgl_text_box.insert(tk.END, hpgl_code)


# Function to calculate distance between two points
def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# Function to estimate the plotting time based on HPGL code
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
                # Apply vertical flip to Y-coordinate
                next_pos = (next_pos[0], max_y - next_pos[1])
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
                # Apply vertical flip to Y-coordinate
                next_pos = (next_pos[0], max_y - next_pos[1])
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


#jsut some tools
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import platform

from xml.dom import minidom

# Detect the OS
is_mac = platform.system() == "Darwin"

# Import tkmacosx Button if on macOS, otherwise use default tk.Button
if is_mac:
    from tkmacosx import Button
else:
    Button = tk.Button  # Use default Button for non-macOS systems

# Store properties for six layers
layer_properties = {i: None for i in range(1, 7)}
layer_properties[1] = {'num_layers': 5, 'num_sides': 4, 'shape_size': 5, 'size_increment': 2, 'rotation_increment': 15, 'x_offset': 0, 'y_offset': 0, 'arc_extent': 360, 'roundness': 0, 'color': 'black'}

current_layer = 1  # Default to Layer 1
current_color = layer_properties[1]['color']  # Default color of Layer 1

from xml.dom import minidom


# Function to remove rectangles from clipPath elements in the SVG and resave
def remove_clip_path_rectangles(svg_filename):
    # Load the SVG
    svg_doc = minidom.parse(svg_filename)

    # Get all 'clipPath' elements in the SVG
    clip_paths = svg_doc.getElementsByTagName('clipPath')

    # Remove any rectangle ('rect') elements inside the clipPaths
    for clip_path in clip_paths:
        rects_in_clip = clip_path.getElementsByTagName('rect')
        for rect in rects_in_clip:
            clip_path.removeChild(rect)

    # Resave the modified SVG
    with open(svg_filename, 'w') as updated_svg_file:
        svg_doc.writexml(updated_svg_file)


def generate_concentric_polygons(ax, properties):
    if properties is None:
        return  # Skip drawing if the layer is cleared

    num_layers = properties['num_layers']
    num_sides = properties['num_sides']
    shape_size = properties['shape_size']
    size_increment = properties['size_increment']
    rotation_increment = properties['rotation_increment']
    x_offset = properties['x_offset']
    y_offset = properties['y_offset']
    arc_extent = properties['arc_extent']
    roundness = properties['roundness']
    color = properties['color']

    base_size = shape_size

    for layer in range(num_layers):
        scaled_size = base_size + layer * size_increment
        rotation = np.deg2rad(layer * rotation_increment)

        theta = np.linspace(0, np.deg2rad(arc_extent), num_sides, endpoint=False)
        x_points = scaled_size * np.cos(theta + rotation) + x_offset
        y_points = scaled_size * np.sin(theta + rotation) + y_offset

        if arc_extent == 360:
            x_points = np.append(x_points, x_points[0])
            y_points = np.append(y_points, y_points[0])

        if roundness > 0:
            x_points, y_points = apply_bezier_roundness(x_points, y_points, roundness)

        # Plot the polygon
        ax.plot(x_points, y_points, lw=1, color=color)

    # Disable axis, frame, and tight plot limits
    ax.set_frame_on(False)
    ax.axis('off')
    ax.set_aspect('equal', adjustable='box')



# Function to apply Bézier curve for rounding the corners of the polygon
def apply_bezier_roundness(x_points, y_points, roundness_factor):
    new_x_points = []
    new_y_points = []

    num_points = len(x_points)
    for i in range(num_points - 1):
        p1_x, p1_y = x_points[i], y_points[i]
        p2_x, p2_y = x_points[i + 1], y_points[i + 1]

        mid_x = (p1_x + p2_x) / 2
        mid_y = (p1_y + p2_y) / 2

        cp_x = p1_x + (mid_x - p1_x) * roundness_factor
        cp_y = p1_y + (mid_y - p1_y) * roundness_factor

        new_x_points.append(p1_x)
        new_y_points.append(p1_y)
        new_x_points.append(cp_x)
        new_y_points.append(cp_y)

    new_x_points.append(new_x_points[0])
    new_y_points.append(new_y_points[0])

    return np.array(new_x_points), np.array(new_y_points)


# Function to export the current plot to SVG without any borders
def export_to_svg():
    svg_filename = "vector_output.svg"
    fig.savefig(svg_filename, format='svg', bbox_inches='tight')
    print(f"SVG file saved as {svg_filename}")

    # Call the post-processing function to remove the rectangle from clipPath
    remove_clip_path_rectangles(svg_filename)
    print(f"Post-processed SVG saved without clipPath rectangles.")


# Function to update the plot for all layers
def update_plot(*args):
    ax.clear()
    ax.set_facecolor('#cdc7c5')  # Set the background color to cdc7c5
    ax.set_xlim(-100, 100)  # Static X-axis limits
    ax.set_ylim(-100, 100)  # Static Y-axis limits
    ax.set_aspect('equal')
    ax.axis('off')  # Hide axes

    # Draw all layers (skip if layer is None)
    for layer_num, properties in layer_properties.items():
        if properties is not None:
            generate_concentric_polygons(ax, properties)

    canvas.draw()


# Function to switch between layers using radio buttons
def switch_layer():
    global current_layer, current_color
    current_layer = layer_var.get()  # Get selected layer from radio button
    properties = layer_properties[current_layer]

    if properties is not None:
        num_layers_slider.set(properties['num_layers'])
        num_sides_slider.set(properties['num_sides'])
        shape_size_slider.set(properties['shape_size'])
        size_increment_slider.set(properties['size_increment'])
        rotation_increment_slider.set(properties['rotation_increment'])
        x_offset_slider.set(properties['x_offset'])
        y_offset_slider.set(properties['y_offset'])
        arc_extent_slider.set(properties['arc_extent'])
        roundness_slider.set(properties['roundness'])
        current_color = properties['color']

    update_plot()


# Function to clear the current layer and not create a default shape until sliders are moved
def clear_layer():
    layer_properties[current_layer] = None  # Erase the current shape
    update_plot()  # Redraw the plot without the shape


# Function to set the color based on button click
def set_color(color):
    global current_color
    current_color = color
    if layer_properties[current_layer] is not None:
        layer_properties[current_layer]['color'] = current_color
    update_plot()


# Create main window
root = tk.Tk()
root.title("Concentric Polygon Generator with Layers")

# Set the window to a standard size (e.g., 800x600)
root.geometry("800x800")

# Create the left frame for buttons and sliders (set a fixed width)
control_frame = ttk.Frame(root, padding="10", width=250)  # Fixed width for the left panel
control_frame.grid(row=0, column=0, sticky='ns')
control_frame.grid_propagate(False)  # Prevent the frame from resizing based on its contents

# Create the right frame for the plot (this will adjust to the remaining space)
plot_frame = ttk.Frame(root)
plot_frame.grid(row=0, column=1, sticky='nsew')

# Configure the grid layout to ensure proper scaling
root.grid_columnconfigure(0, weight=0)  # Left panel should not expand
root.grid_columnconfigure(1, weight=1)  # Right panel should expand to fill available space
root.grid_rowconfigure(0, weight=1)  # Make sure the right panel expands vertically

# Add a canvas to the right frame for displaying the plot
fig, ax = plt.subplots(figsize=(6, 6))
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


# Radio buttons for selecting layers, now in 2 rows
layer_var = tk.IntVar(value=1)  # Default to Layer 1
layer_frame = ttk.Frame(control_frame)
layer_frame.pack(pady=10)
ttk.Label(layer_frame, text="Select Layer").grid(row=0, column=0, columnspan=3)

for i in range(1, 7):
    ttk.Radiobutton(layer_frame, text=f"Layer {i}", variable=layer_var, value=i, command=switch_layer).grid(row=(i - 1) // 3 + 1, column=(i - 1) % 3, padx=5, pady=5)

# Label and slider for Number of Shapes, placed at the top
num_layers_label_var = tk.StringVar()
num_layers_label = ttk.Label(control_frame, text="Number of Shapes")
num_layers_label.pack(anchor='w')

num_layers_slider = tk.Scale(control_frame, from_=1, to=100, orient='horizontal', command=lambda *args: update_slider_label(num_layers_label_var, num_layers_slider, save_current_layer_properties))
num_layers_slider.pack(fill='x')

# Variables to hold the label text for each slider
num_sides_label_var = tk.StringVar()
shape_size_label_var = tk.StringVar()
size_increment_label_var = tk.StringVar()
rotation_increment_label_var = tk.StringVar()
x_offset_label_var = tk.StringVar()
y_offset_label_var = tk.StringVar()
arc_extent_label_var = tk.StringVar()
roundness_label_var = tk.StringVar()


# Add sliders and labels for controlling concentric polygon properties
def create_slider_with_label(parent, label_text, slider_var, from_, to_, command, resolution=0.01):
    label = ttk.Label(parent, text=label_text)
    label.pack(anchor='w')
    slider = tk.Scale(parent, from_=from_, to=to_, orient='horizontal',width=10,command=lambda *args: update_slider_label(slider_var, slider, command), resolution=resolution)
    slider.pack(fill='x')
    return slider


# Function to update the numeric label when slider is moved
def update_slider_label(slider_var, slider, command):
    slider_var.set(f"{slider.get():.2f}")
    command()


num_sides_slider = create_slider_with_label(control_frame, "Number of Sides", num_sides_label_var, 3, 20,lambda *args: save_current_layer_properties(), resolution=1)  # Integers
shape_size_slider = create_slider_with_label(control_frame, "Shape Size", shape_size_label_var, 1, 40, lambda *args: save_current_layer_properties())  # Max size 40
size_increment_slider = create_slider_with_label(control_frame, "Size Increment", size_increment_label_var, 0.5, 5, lambda *args: save_current_layer_properties())
rotation_increment_slider = create_slider_with_label(control_frame, "Rotation Increment", rotation_increment_label_var, 0, 90, lambda *args: save_current_layer_properties())
x_offset_slider = create_slider_with_label(control_frame, "X Offset", x_offset_label_var, -50, 50, lambda *args: save_current_layer_properties())
y_offset_slider = create_slider_with_label(control_frame, "Y Offset", y_offset_label_var, -50, 50, lambda *args: save_current_layer_properties())
arc_extent_slider = create_slider_with_label(control_frame, "Arc Extent", arc_extent_label_var, 10, 360, lambda *args: save_current_layer_properties())
roundness_slider = create_slider_with_label(control_frame, "Roundness", roundness_label_var, 0, 10, lambda *args: save_current_layer_properties())
# Set fixed size for the control frame
control_frame.pack_propagate(False)


# Add buttons to select color in two rows of 3 + 1 layout with fixed width and height
color_frame = ttk.Frame(control_frame)
color_frame.pack(pady=2)

colors = ['green', 'red', 'blue', 'black', 'yellow', 'pink']

# Adjust the size of the color buttons using width and height
for i, color in enumerate(colors):
    color_button = Button(
        color_frame,
        bg=color,
        width=30,  # Adjust width
        height=30,  # Adjust height
        command=lambda c=color: set_color(c)
    )
    color_button.grid(row=i // 3, column=i % 3, padx=5, pady=5)

# Button to clear the current layer
clear_layer_button = ttk.Button(control_frame, text="Clear Layer", command=clear_layer)
clear_layer_button.pack(pady=10)

# Button to export to SVG
export_button = ttk.Button(control_frame, text="Export as SVG", command=export_to_svg)
export_button.pack(pady=10)

# Add a button to reset the sliders and everything
reset_button = ttk.Button(control_frame, text="Reset All", command=lambda: reset_all())
reset_button.pack(pady=10)


# Function to reset everything, including the sliders, layers, and canvas
def reset_all():
    global layer_properties, current_color
    layer_properties = {i: None for i in range(1, 7)}
    layer_properties[1] = {'num_layers': 5, 'num_sides': 4, 'shape_size': 5, 'size_increment': 2, 'rotation_increment': 15, 'x_offset': 0, 'y_offset': 0, 'arc_extent': 360, 'roundness': 0, 'color': 'black'}
    current_color = 'black'
    reset_sliders()
    update_plot()


# Function to save the current properties of the selected layer
def save_current_layer_properties():
    if layer_properties[current_layer] is None:
        layer_properties[current_layer] = {'num_layers': 5, 'num_sides': 4, 'shape_size': 5, 'size_increment': 2, 'rotation_increment': 15, 'x_offset': 0, 'y_offset': 0, 'arc_extent': 360, 'roundness': 0, 'color': current_color}

    layer_properties[current_layer] = {'num_layers': int(num_layers_slider.get()), 'num_sides': int(num_sides_slider.get()), 'shape_size': shape_size_slider.get(), 'size_increment': size_increment_slider.get(), 'rotation_increment': rotation_increment_slider.get(), 'x_offset': x_offset_slider.get(), 'y_offset': y_offset_slider.get(), 'arc_extent': arc_extent_slider.get(), 'roundness': roundness_slider.get(), 'color': current_color}
    update_plot()


# Function to reset the sliders
def reset_sliders():
    num_layers_slider.set(5)
    num_sides_slider.set(4)
    shape_size_slider.set(5)
    size_increment_slider.set(2)
    rotation_increment_slider.set(15)
    x_offset_slider.set(0)
    y_offset_slider.set(0)
    arc_extent_slider.set(360)
    roundness_slider.set(0)


# Function to open a new window (for tool path creation or any other feature)


    # You can add additional widgets to the new window here
    # For example: more sliders, buttons, canvases, etc.
# Import the tool path window creation function from tool_paths.py
from tool_paths import open_tool_path_window

# Add a button to open the new window for tool paths
tool_path_button = ttk.Button(control_frame, text="Open Tool Path Window", command=lambda: open_tool_path_window(root))
tool_path_button.pack(pady=10)



# Initialize the plot with default values
reset_all()

# Set up a flexible grid layout
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

# macOS compatibility settings
if is_mac:
    root.tk_setPalette(background='#ececec')  # Improve macOS default appearance for Tkinter

# Start the Tkinter event loop
root.mainloop()

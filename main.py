#jsut some tools
import tkinter as tk
from tkinter import ttk
from tool_paths import open_tool_path_window ,open_serial_port_window
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import platform
from xml.dom import minidom
import tool_paths


# Detect the OS
is_mac = platform.system() == "Darwin"

# Import tkmacosx Button if on macOS, otherwise use default tk.Button
if is_mac:
    from tkmacosx import Button
else:
    Button = tk.Button  # Use default Button for non-macOS systems

current_layer = 1  # Default to Layer 1
# Store properties for six layers
layer_properties = {i: None for i in range(1, 7)}
layer_properties[current_layer] = {'num_layers': 5, 'num_sides': 4, 'shape_size': 5, 'size_increment': 2, 'rotation_increment': 15, 'x_offset': 0, 'y_offset': 0, 'arc_extent': 360, 'roundness': 0, 'color': 'green'}


current_color = layer_properties[current_layer]['color']  # Default color of Layer 1



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
    """Generate and plot concentric polygons for a given layer."""


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

    # Generate each polygon in the layer
    for layer in range(num_layers):
        scaled_size = base_size + layer * size_increment
        rotation = np.deg2rad(layer * rotation_increment)

        theta = np.linspace(0, np.deg2rad(arc_extent), num_sides, endpoint=False)
        x_points = scaled_size * np.cos(theta + rotation) + x_offset
        y_points = scaled_size * np.sin(theta + rotation) + y_offset

        if arc_extent == 360:
            x_points = np.append(x_points, x_points[0])
            y_points = np.append(y_points, y_points[0])

        # Apply roundness if needed
        if roundness > 0:
            x_points, y_points = apply_bezier_roundness(x_points, y_points, roundness)

        # Plot the polygon
        ax.plot(x_points, y_points, lw=1, color=color)


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


def update_plot():
    """Redraw the entire canvas with all layers."""
    ax.clear()  # Clear the canvas
    ax.set_facecolor('#cdc7c5')  # Set background color
    ax.set_xlim(-100, 100)  # Set X-axis limits
    ax.set_ylim(-100, 100)  # Set Y-axis limits
    ax.set_aspect('equal')  # Maintain aspect ratio
    ax.axis('off')  # Hide axes

    # Draw each layer independently
    for layer_num, properties in layer_properties.items():
        if properties is not None:
            print(f"Drawing Layer {layer_num} with properties: {properties}")  # Debugging
            generate_concentric_polygons(ax, properties)
        else:
            print(f"Skipping Layer {layer_num} (no properties).")  # Debugging

    # Redraw the canvas
    canvas.draw()



def clear_layer():
    """Clear the currently selected layer."""
    print(f"Clearing Layer {current_layer}.")  # Debugging
    layer_properties[current_layer] = None  # Reset the active layer
    update_plot()  # Redraw the plot without the cleared layer

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
root.geometry("1000x800")

# Create the left frame for buttons and sliders (set a fixed width)
control_frame = ttk.Frame(root, padding="10", width=250)  # Fixed width for the left panel
control_frame.grid(row=0, column=0, sticky='ns')
control_frame.grid_propagate(False)  # Prevent the frame from resizing based on its contents

def switch_layer(layer_numb):
    global current_layer, current_color
    current_layer = layer_numb

    if layer_properties[current_layer] is None:
        initialize_layer_properties(current_layer)

    properties = layer_properties[current_layer]
    update_sliders_from_properties(properties)
    current_color = properties['color']
    update_plot()



# Update sliders based on the selected layer's properties
def update_sliders_from_properties(properties):
    num_layers_slider.set(properties['num_layers'])
    num_sides_slider.set(properties['num_sides'])
    shape_size_slider.set(properties['shape_size'])
    size_increment_slider.set(properties['size_increment'])
    rotation_increment_slider.set(properties['rotation_increment'])
    x_offset_slider.set(properties['x_offset'])
    y_offset_slider.set(properties['y_offset'])
    arc_extent_slider.set(properties['arc_extent'])
    roundness_slider.set(properties['roundness'])

# Create the right frame for the plot (this will adjust to the remaining space)
plot_frame = ttk.Frame(root)
plot_frame.grid(row=0, column=1, sticky='nsew')

# Configure the grid layout to ensure proper scaling
root.grid_columnconfigure(0, weight=0)  # Left panel should not expand
root.grid_columnconfigure(1, weight=1)  # Right panel should expand to fill available space
root.grid_rowconfigure(0, weight=1)  # Make sure the right panel expands vertically

# Add buttons to the right side (above the plot)
button_frame = ttk.Frame(plot_frame)
button_frame.pack(side=tk.TOP, pady=10)

# Button to clear the current layer
clear_layer_button = ttk.Button(button_frame, text="Clear Layer", command=clear_layer)
clear_layer_button.grid(row=0, column=0, padx=10)

# Button to export to SVG
export_button = ttk.Button(button_frame, text="Export as SVG", command=export_to_svg)
export_button.grid(row=0, column=1, padx=10)

# Add a button to reset the sliders and everything
reset_button = ttk.Button(button_frame, text="Reset All", command=lambda: reset_all())
reset_button.grid(row=0, column=2, padx=10)

# Add a button to open the new window for tool paths
tool_path_button = ttk.Button(button_frame, text="Open Tool Path Window", command=lambda: open_tool_path_window(root))
tool_path_button.grid(row=0, column=3, padx=10)

# Add a button to open the new window for tool paths
tool_path_button2 = ttk.Button(button_frame, text="Connect", command=lambda: open_serial_port_window(root))
tool_path_button2.grid(row=0, column=4, padx=10)


# Add a button to open the new window for tool paths
print_button = ttk.Button(button_frame, text="Print?", command=lambda: tool_paths.send_hpgl_code_from_vect())
print_button.grid(row=0, column=5, padx=10)


# Add a canvas to the right frame for displaying the plot
fig, ax = plt.subplots(figsize=(6, 6))
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


# Create radio buttons for selecting layers
layer_var = tk.IntVar(value=1)  # Track selected layer (default to Layer 1)
layer_frame = ttk.Frame(control_frame)
layer_frame.pack(pady=10)

ttk.Label(layer_frame, text="Select Layer").grid(row=0, column=0, columnspan=3)



for i in range(1, 7):
    ttk.Radiobutton(
        layer_frame,
        text=f"Layer {i}",
        variable=layer_var,
        value=i,
        command=lambda i=i : switch_layer(i)
    ).grid(row=(i - 1) // 3 + 1, column=(i - 1) % 3, padx=5, pady=5)



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

colors = ['green', 'red', 'blue', 'gray', 'yellow', 'pink']

# Adjust the size of the color buttons using width and height
for i, color in enumerate(colors):
    color_button = Button(
        color_frame,
        bg=color,
        text=str(i + 1),  # Add the number in the center of each button
        width=1,  # Adjust width
        height=1,  # Adjust height
        command=lambda c=color: set_color(c)
    )
    color_button.grid(row=i // 3, column=i % 3, padx=5, pady=5)

# Function to reset everything, including the sliders, layers, and canvas
def reset_all():
    global layer_properties, current_color
    layer_properties = {i: None for i in range(1, 7)}
    layer_properties[1] = {'num_layers': 5, 'num_sides': 4, 'shape_size': 5, 'size_increment': 2, 'rotation_increment': 15, 'x_offset': 0, 'y_offset': 0, 'arc_extent': 360, 'roundness': 0, 'color': 'green'}
    current_color = 'green'
    reset_sliders()
    update_plot()

def save_current_layer_properties():
    """Save the properties of the currently selected layer."""
    global layer_properties

    # Ensure the selected layer is initialized if not already done
    if layer_properties[current_layer] is None:
        print(f"Initializing properties for Layer {current_layer}")
        layer_properties[current_layer] = {
            'num_layers': 5,
            'num_sides': 4,
            'shape_size': 5.0,
            'size_increment': 2.0,
            'rotation_increment': 15.0,
            'x_offset': 0.0,
            'y_offset': 0.0,
            'arc_extent': 360.0,
            'roundness': 0.0,
            'color': current_color,
        }

    # Update properties of the selected layer based on slider values
    layer_properties[current_layer].update({
        'num_layers': int(num_layers_slider.get()),
        'num_sides': int(num_sides_slider.get()),
        'shape_size': shape_size_slider.get(),
        'size_increment': size_increment_slider.get(),
        'rotation_increment': rotation_increment_slider.get(),
        'x_offset': x_offset_slider.get(),
        'y_offset': y_offset_slider.get(),
        'arc_extent': arc_extent_slider.get(),
        'roundness': roundness_slider.get(),
        'color': current_color,
    })

    # Debug: Print updated properties for the selected layer
    print(f"Layer {current_layer} properties updated: {layer_properties[current_layer]}")

    # Redraw the plot to reflect the new properties
    update_plot()


def reset_sliders():
    """Reset all sliders to default values."""

    num_layers_slider.set(5)
    num_sides_slider.set(4)
    shape_size_slider.set(5)
    size_increment_slider.set(2)
    rotation_increment_slider.set(15)
    x_offset_slider.set(0)
    y_offset_slider.set(0)
    arc_extent_slider.set(360)
    roundness_slider.set(0)
    print("Sliders reset to default values.")  # Debugging

# Function to open a new window (for tool path creation or any other feature)


# Initialize the plot with default values


# Initialize layer properties with default values
def initialize_layer_properties(layer):
    layer_properties[layer] = {
        'num_layers': 5,
        'num_sides': 4,
        'shape_size': 5.0,
        'size_increment': 2.0,
        'rotation_increment': 15.0,
        'x_offset': 0.0,
        'y_offset': 0.0,
        'arc_extent': 360.0,
        'roundness': 0.0,
        'color': 'green',
    }
    print(f"Initialized Layer {layer} with default properties.")




reset_all()

# Set up a flexible grid layout
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)

# macOS compatibility settings
if is_mac:
    root.tk_setPalette(background='#ececec')  # Improve macOS default appearance for Tkinter

# Start the Tkinter event loop
root.mainloop()

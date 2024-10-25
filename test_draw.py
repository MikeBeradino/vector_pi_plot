import time
import serial
from tkinter import messagebox

# Define the serial connection (global variable)
serial_connection = None


def connect_to_plotter(port, baud_rate=9600):
    """Establish a connection to the plotter using RTS/CTS flow control."""
    global serial_connection
    try:
        if serial_connection:
            serial_connection.close()  # Close any existing connection

        # Initialize the serial connection with RTS/CTS enabled
        serial_connection = serial.Serial(
            port=port,
            baudrate=baud_rate,
            timeout=1,  # Read timeout
            write_timeout=1,  # Write timeout
            rtscts=True  # Enable RTS/CTS flow control
        )
        messagebox.showinfo("Connection", f"Connected to {port} at {baud_rate} baud.")
    except serial.SerialException as e:
        messagebox.showerror("Connection Error", f"Failed to connect: {e}")


def send_hpgl_command(hpgl_code):
    """Send HPGL commands to the plotter with pacing to avoid buffer overflow."""
    if not serial_connection:
        messagebox.showerror("Error", "No connection to the plotter.")
        return

    try:
        # Split the HPGL code into individual lines or commands
        commands = hpgl_code.splitlines()

        for command in commands:
            full_command = f"{command};\n".encode()  # Format command with terminator
            serial_connection.write(full_command)  # Send the command
            serial_connection.flush()  # Ensure the command is sent immediately

            print(f"Sent: {command}")  # Debugging print

            # Small delay between commands to allow processing
            time.sleep(0.2)  # Adjust as necessary based on plotter's response

    except Exception as e:
        messagebox.showerror("Error", f"Failed to send command: {e}")


def disconnect_plotter():
    """Close the serial connection safely."""
    if serial_connection:
        serial_connection.close()
        messagebox.showinfo("Disconnected", "Plotter disconnected.")


# Example usage
hpgl_code = """
IN;SP1;
PU0,0;PD100,100;
PA100,0,0,100;
PU;
"""

# Connect to the plotter and send commands (replace 'COM3' with the actual port on Windows or '/dev/ttyUSB0' on Linux/macOS)
connect_to_plotter('/dev/ttyUSB0', 9600)
send_hpgl_command(hpgl_code)
disconnect_plotter()

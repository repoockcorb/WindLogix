import tkinter as tk
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from customtkinter import set_appearance_mode, set_default_color_theme
import serial
import csv
import threading
import time
from serial.tools.list_ports import comports
import ctypes
import webbrowser
import os
import pywinstyles

from PIL import Image

class MyInterface:
    def __init__(self, master):
        self.master = master
        self.master.title("WindLogix")

        self.com_ports = [port.device for port in comports()]  # Fetch available COM ports

        self.anemometers = []
        self.wind_speed_labels = []
        self.logging_active = False  # Flag to indicate whether logging is active

        self.live_update_flag = True  # Flag to control live update thread

        set_default_color_theme("dark-blue")

        self.setup_ui()
    
    def setup_ui(self):
        
        # Header Frame
        header_frame = ctk.CTkFrame(master=self.master, width=200)
        header_frame.pack(pady=10, padx=10)

        IMAGE_WIDTH = 255
        IMAGE_HEIGHT = 50

        image = ctk.CTkImage(light_image=Image.open("images/windlogix.png"), dark_image=Image.open("images/windlogix_white.png"), size=(IMAGE_WIDTH , IMAGE_HEIGHT))

        # Create a label to display the image
        image_label = ctk.CTkLabel(header_frame, image=image, text='')
        image_label.grid(row=0, column=0, columnspan=3, pady=10, padx=10)  # Span across all columns

        # Create frame for the top section
        top_frame = ctk.CTkFrame(master=self.master, width=1000, height=1000)  # Use CTkFrame
        top_frame.pack(pady=10)

        # Create com port selection dropdowns for each anemometer
        self.com_port_dropdowns = []
        self.clear_port_buttons = []  # List to store the clear port buttons

        for i in range(3):
            name_label = ctk.CTkLabel(top_frame, text=f"Anemometer {i+1}:", width=100)
            name_label.grid(row=i, column=0, padx=5, pady=5)

            com_port_var = ctk.StringVar()
            # Add a blank option at the beginning
            com_ports_with_blank = [''] + self.com_ports

            dropdown = ctk.CTkComboBox(top_frame, values=com_ports_with_blank, variable=com_port_var, width=90)
            dropdown.grid(row=i, column=1, padx=5, pady=5)

            wind_speed_label = ctk.CTkLabel(top_frame, text="0.00 m/s", height=1, width=40)
            wind_speed_label.grid(row=i, column=3, padx=5, pady=5)
            self.wind_speed_labels.append(wind_speed_label)

            self.com_port_dropdowns.append(com_port_var)

            refresh_image = ctk.CTkImage(Image.open(r"images/refresh_arrow_white.png"))

            refresh_button = ctk.CTkButton(top_frame, text="", width=5, bg_color="#000001", fg_color="grey40", font=("Arial", 12, "bold"), corner_radius=20, command=lambda d=dropdown: self.refresh_ports(d), image=refresh_image)
            refresh_button.grid(row=i, column=2, padx=5, pady=5)
            pywinstyles.set_opacity(refresh_button, color="#000001") # just add this line


        # Create frame for the middle section
        middle_frame = ctk.CTkFrame(master=self.master, width=420)  # Use CTkFrame
        middle_frame.pack(pady=10, padx=10)

        # Create four buttons stacked vertically
        button_names = ["Connect", "Start Logging", "Stop Logging", "Reset"]
        commands = [self.connect_anemometers, self.start_logging, self.stop_logging, self.reset_display]
        button_colour = ["#28a745", "#007bff", "#dc3545", "#cc8400"]
        self.buttons = []
        for name, command, colour in zip(button_names, commands, button_colour):
            button = ctk.CTkButton(middle_frame, text=name, command=command, hover_color="grey", width=270, fg_color=colour)
            button.pack(pady=5)  # Use pack with pady for vertical spacing
            self.buttons.append(button)

        # Create frame for the bottom section (terminal)
        bottom_frame = ctk.CTkFrame(master=self.master, width=400)  # Use CTkFrame
        bottom_frame.pack(pady=10, padx=10)

        # Terminal (text output)
        self.terminal = ctk.CTkTextbox(bottom_frame, height=100, width=400)
        self.terminal.pack(pady=10, padx=10)

        # Handle window closing event
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create frame for the footer section with a larger width
        footer_frame = ctk.CTkFrame(master=self.master, width=200)  # Set a larger width
        footer_frame.pack(pady=10, padx=10)  # Use fill='x' to make the frame fill the entire width

        # Developer label
        developer_label = ctk.CTkLabel(footer_frame, text="Developed By: ", anchor="w")
        developer_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)  # Adjust padx as needed

        # Developer's name with hyperlink
        developer_name_label = ctk.CTkLabel(footer_frame, text="Brock Cooper", anchor="w", cursor="hand2", text_color="#007bff")
        developer_name_label.grid(row=0, column=0, sticky="w", padx=95, pady=5)  # Adjust padx as needed
        developer_name_label.bind("<Button-1>", lambda event: self.open_website("https://brockcooper.au"))

        # space
        space_label = ctk.CTkLabel(footer_frame, text="", anchor="e")
        space_label.grid(row=0, column=2, sticky="e", padx=78, pady=5)  # Adjust padx as needed

        # Version label
        version_label = ctk.CTkLabel(footer_frame, text="Version 1.1", anchor="e")
        version_label.grid(row=0, column=2, sticky="e", padx=10, pady=5)  # Adjust padx as needed
    
    def refresh_ports(self, dropdown):
        new_com_ports = [''] + [port.device for port in comports()]
        dropdown.configure(values=new_com_ports)


    def open_website(self, url):
            webbrowser.open_new(url)
            
    def change_theme(self, choice):
        ctk.set_appearance_mode(choice)

    def connect_anemometers(self):
            # Clear terminal
            self.clear_terminal()
            # Reset wind speed display labels
            for label in self.wind_speed_labels:
                label.configure(text="0.00 m/s")
            # Close all serial connections
            for ser in self.anemometers:
                ser.close()
            self.anemometers = []
            # Open serial connections to anemometers
            for i, com_port_var in enumerate(self.com_port_dropdowns):
                com_port = com_port_var.get()
                if com_port:
                    try:
                        ser = serial.Serial(com_port, 9600, timeout=1)
                        self.anemometers.append(ser)
                        # Read initial data from the serial port
                        initial_line = ser.readline().decode().strip()
                        if initial_line:
                            # Split the line and extract wind speed if data is available
                            # initial_wind_speed = float(initial_line.split(",")[2])
                            # self.update_wind_speed_display(i, initial_wind_speed)
                            self.update_terminal(f"Connected to Anemometer {i+1} on port {com_port}\n")

                            # Start a thread to continuously update wind speed
                            threading.Thread(target=self.update_wind_speed_live, args=(ser, i)).start()
                        else:
                            self.update_terminal(f"Failed to connect to Anemometer {i+1} on port {com_port}\n")
                            # self.update_terminal(f"No data received from Anemometer {i+1} on port {com_port}\n")
                            
                    except serial.SerialException:
                        self.update_terminal(f"Failed to connect to Anemometer {i+1} on port {com_port}\n")
                        continue

    def update_wind_speed_live(self, ser, index):
        while self.live_update_flag:
            if ser is None or not ser.is_open:
                self.update_terminal(f"Serial port for Anemometer {index+1} is not properly initialized or is closed.")
                break
            try:
                line = ser.readline().decode().strip()
                if line:
                    # Split the line into components
                    parts = line.split(",")
                    if len(parts) > 2:  # Check if parts has enough elements
                        wind_speed = parts[2]
                        wind_speed = float(wind_speed)  # Parse wind speed as float
                        # Update the wind speed label
                        self.wind_speed_labels[index].configure(text=f"{wind_speed:.2f} m/s")
            except (serial.SerialException, ValueError, IndexError) as e:
                self.update_terminal(f"Error reading data from Anemometer {index+1}")
            except Exception as e:
                pass
                # self.update_terminal(f"Unexpected error: {e}")
            finally:
                time.sleep(0.1)  # Short sleep to prevent high CPU usage


    def start_logging(self):
        # Check if at least one serial connection is established
        if not self.anemometers:
            self.update_terminal("No serial connection established. Please connect to at least one anemometer.\n")
            return
        
        if self.logging_active == True:
            self.update_terminal("Logging already active\n")
            return
    
        # Generate file name based on current date and time
        current_datetime = time.strftime("(%d-%m-%Y)_(%H-%M-%S)")
        folder_path = os.path.join(os.getcwd(), "WindLogix Logs")  # Folder path one level deep
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)  # Create folder if it doesn't exist
        file_name = os.path.join(folder_path, f"anemometer_data_{current_datetime}.csv")

        self.live_update_flag = False  # Stop live update thread

        # Start a thread to handle data logging
        self.logging_active = True
        logging_thread = threading.Thread(target=self.log_data, args=(file_name,))
        logging_thread.start()

        # Pass the file name to stop_logging when logging stops
        # self.stop_button.configure(command=lambda: self.stop_logging(file_name))

    def stop_logging(self):
        if self.logging_active == True:
            # Stop logging
            self.logging_active = False
            self.live_update_flag = True
        else:
            self.update_terminal("Logging not active\n")
            

    def log_data(self, file_name):
        # Write column headings to CSV
        with open(file_name, "w", newline="") as csvfile:
            csv_writer = csv.writer(csvfile)
            # Write headings
            csv_writer.writerow(["Timestamp", "Anemometer 1 Raw Data", "Anemometer 1 Wind Speed (m/s)", 
                                "Anemometer 2 Raw Data", "Anemometer 2 Wind Speed (m/s)",
                                "Anemometer 3 Raw Data", "Anemometer 3 Wind Speed (m/s)",])
            time.sleep(1)
        
        # Continuously read data from anemometers and log it
        while self.logging_active and self.master.winfo_exists():
            row_data = [time.strftime("%Y-%m-%d %H:%M:%S")]
            serial_conn = 0
            for i, com_port_var in enumerate(self.com_port_dropdowns):
                com_port = com_port_var.get()
                if com_port:  # Check if COM port is selected
                    try:
                        ser = self.anemometers[serial_conn]
                        if ser.is_open:  # Check if serial port is open
                            line = ser.readline().decode().strip()
                            raw_data = line
                            wind_speed = float(line.split(",")[2])  # Extract wind speed from raw data
                            row_data.append(raw_data)
                            row_data.append(wind_speed)
                            self.update_wind_speed_display(i, wind_speed)
                            self.update_terminal(f"Anemometer {i+1} - Wind Speed: {wind_speed} m/s\n")
                            serial_conn += 1
                        else:
                            self.update_terminal(f"Anemometer {i+1} - Serial port is not open\n")
                            serial_conn += 1
                            row_data.append("")  # Append blank data if serial port is not open
                            row_data.append("")  # Append blank data if serial port is not open
                    except (serial.SerialException, ValueError, UnicodeDecodeError, IndexError):
                        self.update_terminal(f"Anemometer {i+1} - Error reading data - Please Check Device\n")
                        serial_conn += 1
                        row_data.append("")  # Append blank data if error reading data
                        row_data.append("")  # Append blank data if error reading data
                else:
                    # If no COM port selected, append blank data
                    row_data.append("")
                    row_data.append("")

            # Write row data to CSV
            with open(file_name, "a", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(row_data)

        # Close all serial connections
        for ser in self.anemometers:
            ser.close()
        # Clear the list of anemometers
        self.anemometers.clear()

        # Reset wind speed display labels
        for label in self.wind_speed_labels:
            label.configure(text="0.00 m/s")

        self.update_terminal(f"File location: {file_name}\n")
        self.update_terminal("Logging stopped\n")


    def update_wind_speed_display(self, index, wind_speed):
        if index < len(self.wind_speed_labels):
            self.wind_speed_labels[index].configure(text=f"{wind_speed:.2f} m/s")
                
    def reset_display(self):
        # Close all serial connections
        for ser in self.anemometers:
            ser.close()
        # Clear the list of anemometers
        self.anemometers.clear()

        # Clear COM port selections
        for var in self.com_port_dropdowns:
            var.set('')
        
        # Stop logging
        self.stop_logging()
        
        # Clear terminal
        self.clear_terminal()

        self.live_update_flag = True  # Reset live update flag

        # Reset wind speed display labels
        for label in self.wind_speed_labels:
            label.configure(text="0.00 m/s")

    def clear_terminal(self):
        self.terminal.delete(1.0, ctk.END)
        self.terminal.update()


    def update_terminal(self, message):
        self.terminal.insert(ctk.END, message)
        self.terminal.see(ctk.END)  # Scroll to the end of the text

    def on_close(self):
        msg = CTkMessagebox(title="Exit?", message="Do you want to close the program?",
                        icon="question", option_1="No", option_2="Yes")
        response = msg.get()
        
        if response=="Yes":
            self.live_update_flag = False
            for ser in self.anemometers:
                ser.close()
            self.master.destroy()       
        
def create_about_dialog(root):
    cur_dir = os.getcwd()
    cur_dir = cur_dir.replace("\\", "/")
    # icon_path = cur_dir+"/favicon.ico"
    icon_path = "images/favicon.ico"

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(icon_path)

    # Set the icon for the about dialog
    about_dialog = ctk.CTk()
    
    # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(icon_path)
    about_dialog.geometry("430x655")  # Adjust dimensions as needed
    about_dialog.title("About")
    about_dialog.attributes("-topmost", True)  # Set the window to be topmost
    about_dialog.iconbitmap(icon_path)  # Set the icon for the about dialog

    # Frame for content
    content_frame = ctk.CTkFrame(master=about_dialog, width=600, height=200)
    content_frame.pack(padx=25, pady=25)

    # Application name label (customize text and font)
    app_name_label = ctk.CTkLabel(master=content_frame,
                                text="WindLogix Interface",
                                font=("Arial", 18, "bold"))
    app_name_label.pack(pady=10)

    # Version label (customize text and font)
    version_label = ctk.CTkLabel(master=content_frame,
                                text="Version: 1.1",  # Update version number
                                font=("Arial", 12, "bold"))
    version_label.pack()

    # Author label (customize text and font)
    author_label = ctk.CTkLabel(master=content_frame,
                                text="Developed by: Brock Cooper",
                                font=("Arial", 12, "bold"))
    author_label.pack()

    # Usage
    description_label = ctk.CTkLabel(master=content_frame,
                                text="This program was designed specifically to be used\n\
with the WindSonic 75 Anemometer from Gill Instruments.\n\n\
Anemometer Configuration\n\
M2, U1, O1, L1, P2, B3, H1, NQ, F1, E3, T1, S4, C2, G0, K50\n\n\
Select the COM port of the anemometer and click Connect.\n\
The anemometers should show connected in the output window\n\
and display the live wind speed. If there is no wind speed\n\
present, please check the connection to the anemometer\n\
or ensure you have the correct COM port selected and try again.\n\
Once connected, you can start logging the data\n\
by pressing the Start Logging button. To stop logging,\n\
press the Stop Logging button. This will disconnect \n\
the anemometers and display the location where \n\
the CSV file is stored. If it's the first time logging has occured, \n\
the program will generate a folder called 'WindLogix Logs'\n\
in the same location where the program is stored. \n\
If you need to start logging again,\n\
please reconnect to the anemometers.",
                                font=("Arial", 12), padx=10)
    description_label.pack()

    # Important note label (customize text and font)
    important_note_label = ctk.CTkLabel(master=content_frame,
                                text="\nImportant Note: Please ensure the anemometers\n\
are connected in the order you require\n\
and are checked before you start logging.\n\
Failure to do so may result in incorrect data being logged\n\
and unable to be determined post logging.\n ",
                                font=("Arial", 12, "bold"))
    important_note_label.pack()


    # Copyright label (customize text and font)
    copyright_label = ctk.CTkLabel(master=content_frame,
                                text="Copyright © 2024 Brock Cooper",
                                font=("Arial", 10))
    copyright_label.pack()

    # Close button
    close_button = ctk.CTkButton(master=content_frame,
                                text="Close",
                                command=about_dialog.destroy)
    close_button.pack(pady=20)

    # Apply desired theme (optional)
    # about_dialog.set_theme("dark")  # Example theme, customize as needed

    about_dialog.mainloop()

def main():
    root = ctk.CTk()
    root.geometry("450x600")  # Set the initial size of the window to 1000x800 pixels
    app = MyInterface(root)
    # Set the window icon
    cur_dir = os.getcwd()
    cur_dir = cur_dir.replace("\\", "/")
    # icon_path = cur_dir+"/favicon.ico"
    icon_path = "images/favicon.ico"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(icon_path)
    print(icon_path)
    root.iconbitmap(icon_path)  # Set the window icon

    # Create a Tkinter menubar
    menubar = tk.Menu(root)

    # Create "File" menu
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)

    # Create "Theme" submenu under "File" menu
    theme_menu = tk.Menu(file_menu, tearoff=0)
    file_menu.add_cascade(label="Theme", menu=theme_menu)
    theme_menu.add_command(label="Light Theme", command=lambda: app.change_theme("light"))
    theme_menu.add_command(label="Dark Theme", command=lambda: app.change_theme("dark"))
    theme_menu.add_command(label="System Theme", command=lambda: app.change_theme("system"))

    # Add "Help" command directly to "File" menu
    file_menu.add_command(label="Help", command=lambda: create_about_dialog(root))

    root.configure(menu=menubar)
    root.mainloop()

if __name__ == "__main__":
    main()

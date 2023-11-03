#imports
import sys
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import Tk, PhotoImage

import re
from itertools import zip_longest
import binascii
from PIL import ImageTk, Image

#Global defined values
line_start_with = " "  #For skipping the header
line_divider = chr(0x255F)+chr(0x2500)*9+chr(0x253C)+chr(0x2500)*19+chr(0x253C)+chr(0x2500)*19+chr(0x2562)+ "\n"


#global variables
global file_path_1 #The file paths of the two .trc files to compare
global file_path_2 #The file paths of the two .trc files to compare
global parsed_messages_1
global parsed_messages_2
global differences
global file_1_set 
global file_2_set
global nb_errors

#Class TrcParser for parsing messages in the .trc file
class TrcParser:
    def __init__(self, filename, progress_var_x, progress_label_x, number_frames_x):
        self.messages = []
        #count total number of messages in file
        number_lines_header = 0
        with open(filename, "r") as f:
            # skip header lines until [Data]
            while True:
                header = f.readline()
                if header.startswith(line_start_with):
                    break
                else :
                    number_lines_header += 1
        with open(filename, 'r') as file:
            lines = sum(1 for line in file)
            self.nb_messages = lines-number_lines_header #number of messages (total number of lines - number of lines in header)
        with open(filename, "r") as f:
            # skip header lines until [Data]
            while True:
                line = f.readline()
                if line.startswith(line_start_with):
                    break
            idx=0
            # read messages until end of file
            while True:
                if not line:
                    progress_var_x.set(100)
                    progress_label_x["text"] = f"{100}%"
                    number_frames_x["text"] = f"{self.nb_messages} CAN Frames"
                    break

                line = line.strip() # remove leading/trailing whitespace
                elements = line.split() # split by whitespace
                dlc = elements[7]
                if(elements[2] == 'DT') :
                    data_list = elements[8:] 
                else :
                    data_list = elements[7:] 
                data = ''.join(data_list)
                self.messages.append({
                #         "Timestamp": match.group(1) + " " + match.group(2),
                #         "Bus ID": match.group(3),
                #         "Frame Type": match.group(4),
                #         "ID": match.group(4),
                #         "DLC": match.group(8),
                         "Data": [byte for byte in bytes.fromhex(data)]   #[int(data[i:i+2], 16) for i in range(0, len(data-1), 2)]
                })
                idx+=1
                progress_var_x.set(idx*100/self.nb_messages)
                progress_label_x["text"] = f"{idx*100/self.nb_messages}%"
                line = f.readline()




def open_file_1():
    global file_path_1 
    global parsed_messages_1
    global file_1_set


    # Open a file dialog and get the path of the selected file
    file_path_1 = filedialog.askopenfilename()

    if file_path_1 :
        file_1_set = True
        progress_bar_1.start()
        print("Selected file:", file_path_1)
        parsed_messages_1 = TrcParser(file_path_1, progress_var_1, progress_label_1, number_frames_1)
        progress_bar_1.stop()
        # enable or disable the button based on the condition
        if file_2_set and file_1_set:
            compare_button.config(state=tk.NORMAL)


def open_file_2():
    global file_path_2 
    global parsed_messages_2
    global file_2_set


            
    # Open a file dialog and get the path of the selected file
    file_path_2 = filedialog.askopenfilename()

    if file_path_2 :
        file_2_set = True
        progress_bar_2.start()
        print("Selected file:", file_path_2)
        parsed_messages_2 = TrcParser(file_path_2, progress_var_2, progress_label_2, number_frames_2)
        progress_bar_2.stop()
        # enable or disable the button based on the condition
        if file_2_set and file_1_set:
            compare_button.config(state=tk.NORMAL)



def compare():
    global parsed_messages_1
    global parsed_messages_2
    global nb_errors
    global differences
    global file_1_set
    global file_2_set

    nb_errors = 0
    differences = []
    for i in range(min(len(parsed_messages_1.messages), len(parsed_messages_2.messages))) :
        #Fill the missing values in list of Data with 0
        for msg1_byte, msg2_byte in zip_longest(parsed_messages_1.messages[i]["Data"], parsed_messages_2.messages[i]["Data"], fillvalue=0):
            if msg1_byte != msg2_byte:
                nb_errors+=1 #increment number of errors
                differences.append((i, parsed_messages_1.messages[i]["Data"], parsed_messages_2.messages[i]["Data"]))
                # print("MSG in file 1 : {}".format(parsed_messages_1.messages[i]["Data"]))
                # print("MSG in file 2 : {}".format(parsed_messages_2.messages[i]["Data"]))
                break

    #Add the left Frames
    if(len(parsed_messages_1.messages) > len(parsed_messages_2.messages)) :
        for i in range(len(parsed_messages_2.messages), len(parsed_messages_1.messages)):
            differences.append((i+1000000, parsed_messages_1.messages[i]["Data"], None))
            nb_errors+=1 #Increment number of errors

    if(len(parsed_messages_2.messages) > len(parsed_messages_1.messages)) :
        for i in range(len(parsed_messages_1.messages), len(parsed_messages_2.messages)):
            differences.append((i+1000000, None, parsed_messages_2.messages[i]["Data"]))
            nb_errors+=1 #Increment number of errors

    #Update number of errors
    errors_label["text"] = f"{nb_errors} Errors"
    file_2_set = False
    file_1_set = False
    compare_button.config(state=tk.DISABLED)
    save_button.config(state=tk.NORMAL)


def check_condition():
    #check the condition
    condition = file_2_set and file_1_set
    # enable or disable the button based on the condition
    if condition:
        compare_button.config(state=tk.NORMAL)
    else:
        compare_button.config(state=tk.DISABLED)          

def save_to_file():
    global differences

    header_0 =  chr(0x2554)+chr(0x2550)*9+chr(0x2564) +chr(0x2550)*19+chr(0x2564)+chr(0x2550)*19+chr(0x2557)+ "\n"
    header_1 = chr(0x2551) + " Index   " + chr(0x2502) + " File 1            " + chr(0x2502) +"  File 2           " + chr(0x2551) +"\n"
    header_2 =  chr(0x255F) + chr(0x2500) * 9 + chr(0x253C)  + chr(0x2500) * 19 + chr(0x253C) + chr(0x2500) * 19 + chr(0x2562) + "\n"
    
    file_path = filedialog.asksaveasfilename(defaultextension=".txt")
    if file_path:
        with open(file_path, 'w+', encoding='utf-8') as file:
            file.write(header_0)
            file.write(header_1)
            file.write(header_2)
            for index, difference in enumerate(differences):
                frame_idx = str(difference[0]+1)
                if(difference[1] != None) :
                    hex_string_1 = binascii.hexlify(bytes(difference[1])).decode('utf-8')
                    hex_string_1 = hex_string_1.upper()
                else :
                    hex_string_1 = "None"
                if(difference[2] != None) :
                    hex_string_2 = binascii.hexlify(bytes(difference[2])).decode('utf-8')
                    hex_string_2 = hex_string_2.upper()
                else :
                    hex_string_2 = "None"

                hex_string_1 = hex_string_1 + " " * (16-len(hex_string_1))
                hex_string_2 = hex_string_2 + " " * (16-len(hex_string_2)) + " " + chr(0x2551)
                hex_string_0 = chr(0x2551) + " " + frame_idx + " " * (8-len(frame_idx))
                special_chr = "" + chr(0x2502)
                file.write(f"{hex_string_0}{special_chr} {hex_string_1}  {special_chr}  {hex_string_2}\n")
                if index != len(differences) - 1:
                    file.write(f"{line_divider}")
                
            end = chr(0x255A)+chr(0x2550)*9+chr(0x2567)+chr(0x2550)*19+chr(0x2567)+chr(0x2550)*19+chr(0x255D)+ "\n"
            file.write(end)

        save_button.config(state=tk.DISABLED)

    



# Get the path of the images folder within the executable
if getattr(sys, 'frozen', False):
    # The application is frozen/compiled
    images_folder = os.path.join(sys._MEIPASS, "images")
else:
    # The application is not frozen
    images_folder = "images"
    

#Initialize
file_1_set = False
file_2_set = False

# Create the main window
root = tk.Tk()
root.title("File Comparison")
root.geometry("480x300")
root.resizable(False, False) # Make the window not resizable
# Define the relative path of the image file
image_path_1 = os.path.join(images_folder, "compare.png")
root.iconphoto(False, PhotoImage(file=image_path_1))

# open the PNG image
image_path_2 = os.path.join(images_folder, "compare_2.png")
image = Image.open(image_path_2)
image = image.resize((90, 90), Image.ANTIALIAS)
# create a PhotoImage object from the PNG image
photo = ImageTk.PhotoImage(image)
# create a label to display the image
label = tk.Label(image=photo)
# add the label to the Tkinter window
label.place(relx=0.1, rely=0.6)


# Create a button to open the file 1 dialog
open_button_1 = tk.Button(root, text="Open File 1", command=open_file_1)
open_button_1.grid(row=0, column=0, padx=10, pady=10)

# Create a button to open the file 2 dialog
open_button_2 = tk.Button(root, text="Open File 2", command=open_file_2)
open_button_2.grid(row=1, column=0, padx=10, pady=10)

# Add Label for the progress bar 1
progress_label_1 = tk.Label(root, text="0%")
progress_label_1.grid(row=0, column=2, padx=10, pady=10)

# Add a progress bar 1
progress_var_1 = tk.DoubleVar()
progress_bar_1 = ttk.Progressbar(root, orient="horizontal", length=200, variable=progress_var_1, maximum=100)
progress_bar_1.grid(row=0, column=1, padx=10, pady=10)

# Add Label for the progress bar 2
progress_label_2 = tk.Label(root, text="0%")
progress_label_2.grid(row=1, column=2, padx=10, pady=10)

# Add a progress bar 2
progress_var_2 = tk.DoubleVar()
progress_bar_2 = ttk.Progressbar(root, orient="horizontal", length=200, variable=progress_var_2, maximum=100)
progress_bar_2.grid(row=1, column=1, padx=10, pady=10)

# Add Label for number of frames for File 1
number_frames_1 = tk.Label(root, text="0 CAN Frames")
number_frames_1.grid(row=0, column=3, padx=10, pady=10)

# Add Label for number of frames for File 2
number_frames_2 = tk.Label(root, text="0 CAN Frames")
number_frames_2.grid(row=1, column=3, padx=10, pady=10)


# Create a button for comparing both files
compare_button = tk.Button(root, text="Compare", command=compare, width=20, height=3)
compare_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
compare_button.config(state=tk.DISABLED)


# Add Label for total number of errors
errors_label = tk.Label(root, text="0 Errors")
errors_label.place(relx=0.45, rely=0.62)


# Create a button for Saving comparison file
save_button = tk.Button(root, text="Save", command=save_to_file, width=10, height=2)
save_button.place(relx=0.7, rely=0.62)
save_button.config(state=tk.DISABLED)


# Start the main loop to display the window and handle events
root.mainloop()

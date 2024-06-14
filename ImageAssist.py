from tkinter import Tk, Entry, Label, Button, Text, Scrollbar
from PIL import ImageGrab
import pytesseract
from pytesseract import Output
import numpy as np
import cv2
from screeninfo import get_monitors
import pyautogui
import keyboard  # For listening to keyboard events
import re  # For regular expression matching
from pynput import mouse

class GUI:
    def __init__(self, window):
        self.window = window
        window.title("Text Locator")


        self.entry_text = Entry(window)
        self.entry_text.pack()
        self.entry_text.insert(0, "Enter your text")

        self.locate_button = Button(window, text="Locate", command=self.locate_text)
        self.locate_button.pack()

        self.drift_button = Button(window, text="Drift", command=self.move_mouse)
        self.drift_button.pack()

        self.auto_button = Button(window, text="Auto", command=self.auto_mode)
        self.auto_button.pack()

        self.contextualize_button = Button(window, text="Contextualize", command=self.contextualize_text)
        self.contextualize_button.pack()

        self.draw_box_button = Button(window, text="Draw Box", command=self.draw_box)
        self.draw_box_button.pack()

        self.auto_status_label = Label(window, text="Auto mode is off")
        self.auto_status_label.pack()

        self.coordinates_label = Label(window, text="")
        self.coordinates_label.pack()

        self.text_box = Text(window, height=10, width=50)
        self.text_box.pack()

        self.scrollbar = Scrollbar(window)
        self.scrollbar.pack(side="right", fill="y")

        self.text_box.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.text_box.yview)

        self.coordinates_list = None
        self.auto_mode_on = False
        self.current_index = 0

        keyboard.on_press_key("2", self.handle_enter)
        keyboard.on_press_key("4", self.handle_left)
        keyboard.on_press_key("6", self.handle_right)
        keyboard.on_press_key("8", self.handle_up)

        self.top_left = None
        self.bottom_right = None
        self.coordinates_box = Label(window, text="")
        self.coordinates_box.pack()
        
        self.contextualize_box_button = Button(window, text="Contextualize Box", command=self.contextualize_boxed_text)
        self.contextualize_box_button.pack()


    def locate_text(self):
        text = self.entry_text.get()
        monitor = get_monitors()[0]  # Change the index to choose a different monitor
        bbox = (monitor.x, monitor.y, monitor.width + monitor.x, monitor.height + monitor.y)
        screenshot = ImageGrab.grab(bbox=bbox)  
        screenshot.show()  # Show the screenshot for testing purposes
        screenshot_np = np.array(screenshot)
        self.coordinates_list = self.get_coordinates(screenshot_np, text)
        self.current_index = 0  # Reset index each time new text is located

        if not self.coordinates_list:
            self.coordinates_label.config(text="The text '{}' was not found in the screenshot.".format(text))
        else:
            self.coordinates_label.config(text=str(self.coordinates_list))

    def move_mouse(self):
        if self.coordinates_list:
            # Get the first set of coordinates
            ((x1, y1), (x2, y2)) = self.coordinates_list[self.current_index]
            # Calculate the center
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            # Move the mouse to the center of the first textbox
            pyautogui.moveTo(center_x, center_y)

    def auto_mode(self):
        self.auto_mode_on = not self.auto_mode_on  # Toggle auto mode on/off

    def handle_enter(self, event):
        if self.auto_mode_on and self.coordinates_list and self.current_index < len(self.coordinates_list):
            self.move_mouse()
            pyautogui.click()
            self.current_index += 1
            if self.current_index >= len(self.coordinates_list):  # If we've visited all entries, turn off auto mode
                self.auto_mode_on = False

    def handle_right(self, event):
        if self.auto_mode_on and self.coordinates_list:
            self.current_index = (self.current_index + 1) % len(self.coordinates_list)
            self.move_mouse()

    def handle_left(self, event):
        if self.auto_mode_on and self.coordinates_list:
            self.current_index = (self.current_index - 1) % len(self.coordinates_list)
            self.move_mouse()

    def handle_up(self, event):
        if self.auto_mode_on:
            self.handle_enter(event)

    def get_coordinates(self, img, text):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ocr_result = pytesseract.image_to_data(gray, output_type=Output.DICT)
        coords_list = []

        for i in range(len(ocr_result['text'])):
            line = ocr_result['text'][i]
            match = re.search(r'\b' + text.lower() + r'\b', line.lower())
            if match:
                x_start = match.start() * (ocr_result['width'][i] // len(line))
                x_end = match.end() * (ocr_result['width'][i] // len(line))
                (x, y, w, h) = (ocr_result['left'][i] + x_start, ocr_result['top'][i], x_end - x_start, ocr_result['height'][i])
                coords_list.append(((x, y), (x + w, y + h)))

        return coords_list

    def contextualize_boxed_text(self):
        if self.top_left and self.bottom_right:
            screenshot = ImageGrab.grab(bbox=(self.top_left[0], self.top_left[1], self.bottom_right[0], self.bottom_right[1]))  
            screenshot_np = np.array(screenshot)
            text = self.extract_text(screenshot_np)
            self.display_text(text)
        else:
            self.coordinates_box.config(text="No box has been drawn. Click 'Draw Box' to draw a box.")

    def contextualize_text(self):
        screenshot = ImageGrab.grab()  
        screenshot_np = np.array(screenshot)
        text = self.extract_text(screenshot_np)
        self.display_text(text)

    def extract_text(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ocr_result = pytesseract.image_to_data(gray, output_type=Output.DICT)
        text_list = []

        for i in range(len(ocr_result['text'])):
            line = ocr_result['text'][i]
            if line.strip():  # Exclude empty lines
                text_list.append(line.strip())

        return text_list

    def display_text(self, text_list):
        self.text_box.delete(1.0, "end")
        for text in text_list:
            self.text_box.insert("end", text + "\n")

    def draw_box(self):
        # Reset the coordinates
        self.top_left = None
        self.bottom_right = None
        self.coordinates_box.config(text="Click the top left corner of the box.")
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()

    def on_click(self, x, y, button, pressed):
        if pressed:
            if self.top_left is None:
                self.top_left = (x, y)
                self.coordinates_box.config(text="Click the bottom right corner of the box.")
            else:
                self.bottom_right = (x, y)
                self.coordinates_box.config(text="Box coordinates: {} - {}".format(self.top_left, self.bottom_right))
                self.listener.stop()

window = Tk()
my_gui = GUI(window)
window.mainloop()
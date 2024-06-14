from PIL import ImageGrab
import easyocr
import numpy as np
import cv2
from screeninfo import get_monitors
import pyautogui
import re  # For regular expression matching
import torch
import time


class OCRHandler:
    def __init__(self):
        self.reader = easyocr.Reader(['en'])
        self.stored_coordinates = {}  # Dictionary to store coordinates of found text

    def locate_text(self, text, bbox=None):
        print("locate_text method called")
        print(f"Text: {text}, Bbox: {bbox}")

        if bbox is None:
            monitor = get_monitors()[0]
            bbox = (monitor.x, monitor.y, monitor.width + monitor.x, monitor.height + monitor.y)

        screenshot = ImageGrab.grab(bbox=bbox)  # Grab the screenshot but don't show it
        screenshot_np = np.array(screenshot)
        local_coordinates = self.get_coordinates(screenshot_np, text)
        self.current_index = 0

        print(local_coordinates)  # For debugging purposes

        self.coordinates_list = [((x1+bbox[0], y1+bbox[1]), (x2+bbox[0], y2+bbox[1])) for ((x1, y1), (x2, y2)) in local_coordinates]

        return self.coordinates_list


    def get_coordinates(self, img, text):
        ocr_result = self.reader.readtext(img, detail = 1)
        coords_list = []

        for result in ocr_result:
            line = result[1]
            match = re.search(r'\b' + text.lower() + r'\b', line.lower())
            if match:
                x_start = result[0][0][0]
                y_start = result[0][0][1]
                x_end = result[0][2][0]
                y_end = result[0][2][1]
                coords_list.append(((x_start, y_start), (x_end, y_end)))

        return coords_list

    def contextualize_boxed_text(self, top_left, bottom_right):
        if top_left and bottom_right:
            screenshot = ImageGrab.grab(bbox=(top_left[0], top_left[1], bottom_right[0], bottom_right[1]))  
            screenshot_np = np.array(screenshot)
            text = self.extract_text(screenshot_np)
            return text
        else:
            return "No box has been drawn. Click 'Draw Box' to draw a box."

    def contextualize_text(self):
        screenshot = ImageGrab.grab()  
        screenshot_np = np.array(screenshot)
        recognized_text = self.extract_text(screenshot_np)
        return recognized_text

    def extract_text(self, img):
        ocr_result = self.reader.readtext(img, detail = 0)
        text_list = []

        for line in ocr_result:
            if line.strip():  # Exclude empty lines
                text_list.append(line.strip())

        return text_list

    def get_stored_coordinates(self, text):
        return self.stored_coordinates.get(text, None)

    def extract_text_with_coordinates(self, bbox=None):
        if bbox is None:
            monitor = get_monitors()[0]
            bbox = (monitor.x, monitor.y, monitor.width + monitor.x, monitor.height + monitor.y)

        screenshot = ImageGrab.grab(bbox=bbox)  # Grab the screenshot but don't show it
        screenshot_np = np.array(screenshot)
        
        ocr_result = self.reader.readtext(screenshot_np, detail = 1)
        texts_with_coordinates = []

        for result in ocr_result:
            line = result[1]
            x_start = result[0][0][0]
            y_start = result[0][0][1]
            x_end = result[0][2][0]
            y_end = result[0][2][1]
            coords = ((x_start + bbox[0], y_start + bbox[1]), (x_end + bbox[0], y_end + bbox[1]))
            texts_with_coordinates.append((line, coords))

        return texts_with_coordinates

    def get_text_from_box(self, box):
        # Capture the screen area defined by the box
        image = ImageGrab.grab(bbox=(box[0][0], box[0][1], box[1][0], box[1][1]))

        # Convert the PIL Image object to a numpy array
        image_np = np.array(image)

        # Get the text from the image using OCR
        result = self.reader.readtext(image_np)

        # The result is a list of tuples, where each tuple represents a recognized piece of text.
        # The first item in the tuple is the coordinates of the text, and the second item is the text itself.
        # We'll just take the first recognized piece of text and convert it to a float.
        price_text = result[0][1]

        # Remove commas from the price text
        price_text = price_text.replace(',', '')

        # Convert the price to a number and return it
        return float(price_text)

    def click_buy(self, coords):
        # Move the mouse to the given coordinates and click
        pyautogui.click(*coords)

    def click_yes(self, coords):
        # Move the mouse to the given coordinates and click
        pyautogui.click(*coords)
from tkinter import Tk, Entry, Label, Button, Text, Scrollbar, Frame, RAISED, SUNKEN, LEFT
import pyautogui
import keyboard  # For listening to keyboard events
from pynput import mouse
from ocr_handler import OCRHandler
from ai_handler import AIHandler
from screeninfo import get_monitors
import time
from threading import Thread
# user exception if more than one instance of an item is found*
class GUI:
    def __init__(self, window):
        # Basic GUI setup
        self.window = window
        window.title("OCR+GPT Interact")

        self.buyer_button = Button(self.window, text="Buyer", command=self.start_buyer)
        self.buyer_button.pack()

        self.set_yes_button = Button(self.window, text="Set Yes Button", command=self.set_yes_button)
        self.set_yes_button.pack()

        self.set_buy_button = Button(self.window, text="Set Buy Button", command=self.set_buy_button)
        self.set_buy_button.pack()

        # Frame
        self.buttons_frame = Frame(window)
        self.buttons_frame.pack()

        # OCR and AI handlers
        self.ocr_handler = OCRHandler()
        self.ai_handler = AIHandler(self.ocr_handler)

        # Bounding box and related parameters
        self.bbox = None
        self.bbox_drawn = False
        self.top_left = None
        self.bottom_right = None

        # AI parameters
        self.ai_is_running = False
        self.initial_prompt_sent = False
        self.initial_prompt = ("Pretend you are using an OCR/text model to read data on screen, whatever you encapsulate in quotes is what you will next click on. Please click on things you believe would perform an action, only reply with the quoted words, also do not run. The context is: ")

        # Entry for additional prompt
        self.append_prompt_entry = Entry(window)
        self.append_prompt_entry.insert(0, "Enter text to append to prompt")
        self.append_prompt_entry.pack()

        # Buttons
        self.ai_write_button = Button(self.buttons_frame, text="AI Write", command=self.toggle_ai_write)
        self.ai_write_button.pack(side=LEFT)

        self.locate_button = Button(window, text="Locate", command=self.locate_text_wrapper)
        self.locate_button.pack()

        self.drift_button = Button(window, text="Drift", command=self.move_mouse)
        self.drift_button.pack()

        self.auto_button = Button(window, text="Auto", command=self.auto_mode)
        self.auto_button.pack()

        self.execute_ai_button = Button(window, text="Start AI", command=self.toggle_ai)
        self.execute_ai_button.pack()

        self.contextualize_button = Button(window, text="Contextualize", command=self.ocr_handler.contextualize_text)
        self.contextualize_button.pack()

        self.draw_box_button = Button(window, text="Draw Box", command=self.draw_box)
        self.draw_box_button.pack()

        self.contextualize_box_button = Button(window, text="Contextualize Box", command=self.contextualize_boxed_text_wrapper)
        self.contextualize_box_button.pack()

        # Labels
        self.auto_status_label = Label(window, text="Auto mode is off")
        self.auto_status_label.pack()

        self.coordinates_label = Label(window, text="")
        self.coordinates_label.pack()

        self.coordinates_box = Label(window, text="")
        self.coordinates_box.pack()

        # Entry for text and wait time
        self.entry_text = Entry(window)
        self.entry_text.insert(0, "Enter your text")
        self.entry_text.pack()

        self.user_set_wait_time = Entry(window)
        self.user_set_wait_time.insert(0, "10")  # Insert a default value of 1 second    
        self.user_set_wait_time.pack()

        self.task_goal_text = Entry(window)
        self.task_goal_text.insert(0, "Enter your task goal")
        self.task_goal_text.pack()

        # Text box
        self.text_box = Text(window, height=10, width=50)
        self.text_box.pack()

        # Scrollbar
        self.scrollbar = Scrollbar(window)
        self.scrollbar.pack(side="right", fill="y")
        self.text_box.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.text_box.yview)

        # Other parameters
        self.coordinates_list = None
        self.auto_mode_on = False
        self.current_index = 0

        # Keyboard events
        keyboard.on_press_key("2", self.handle_enter)
        keyboard.on_press_key("4", self.handle_left)
        keyboard.on_press_key("6", self.handle_right)
        keyboard.on_press_key("8", self.handle_up)

    def locate_text_wrapper(self):
        text = self.entry_text.get()
        coordinates = self.ocr_handler.locate_text(text, self.bbox)
        if not coordinates:
            self.coordinates_label.config(text="The text '{}' was not found in the screenshot.".format(text))
        else:
            self.coordinates_list = [coordinates]  # Store the coordinates in the list
            self.current_index = 0  # Set the current index to 0
            self.coordinates_label.config(text=str(coordinates))


    def contextualize_boxed_text_wrapper(self):
        if self.top_left and self.bottom_right:
            print(f"Contextualizing box from {self.top_left} to {self.bottom_right}")  # Debug print
            text = self.ocr_handler.contextualize_boxed_text(self.top_left, self.bottom_right)
            self.display_text(text)
        else:
            self.coordinates_box.config(text="No box has been drawn. Click 'Draw Box' to draw a box.")

    def contextualize_text_wrapper(self):
        text = self.ocr_handler.contextualize_text()
        self.display_text(text)

    def move_mouse(self):
        print(self.coordinates_list)  # Add this line
        if self.coordinates_list:
            ((x1, y1), (x2, y2)) = self.coordinates_list[self.current_index][0]
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

    def display_text(self, text_list):
        self.text_box.delete(1.0, "end")
        self.text_box.insert("end", "\n".join(text_list))

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
                print(f"Top left set to: {self.top_left}")  # Debug print
                self.coordinates_box.config(text="Click the bottom right corner of the box.")
            elif self.bottom_right is None:  # Only set bottom_right if top_left has been set and bottom_right hasn't
                self.bottom_right = (x, y)
                print(f"Bottom right set to: {self.bottom_right}")  # Debug print
                self.bbox = (*self.top_left, *self.bottom_right)  # Update bbox values
                self.ai_handler.bbox = self.bbox  # Update the bbox in the AIHandler instance
                self.bbox_drawn = True  # Set the bbox_drawn flag
                self.coordinates_box.config(text="Box coordinates: {} - {}".format(self.top_left, self.bottom_right))
                self.listener.stop()

    def execute_ai(self):
        # If AI is not running, just return
        if not self.ai_is_running:
            return

        # Get user input from the Entry widget
        append_text = self.append_prompt_entry.get()
        if append_text == "Enter text to append to prompt":  # Ignore the placeholder text
            append_text = ""
        else:
            append_text = " " + append_text  # Add a space before the appended text if it's not empty

        # If the initial prompt hasn't been sent yet, send it
        if not self.initial_prompt_sent:
            context = self.ocr_handler.contextualize_boxed_text(self.top_left, self.bottom_right)
            context_str = ' '.join(context) if isinstance(context, list) else context
            prompt = self.initial_prompt + append_text + context_str  # Append context and user input to initial prompt
            self.initial_prompt_sent = True  # Update the flag
        else:
            # Otherwise, get the screen context and use that as the prompt
            context = self.ocr_handler.contextualize_boxed_text(self.top_left, self.bottom_right)
            context_str = ' '.join(context) if isinstance(context, list) else context
            prompt = "The context is now:" + append_text + " " + context_str  # Append user input and prepend "The context is now: "

        gpt3_response = self.ai_handler.locate_and_click_quoted_gpt3_response(prompt, self.bbox)

        if self.ai_handler.ai_can_write:  # Check if the AI is allowed to write
            # Write the GPT-3 response
            pyautogui.write(gpt3_response, interval=0.25)

        # Only schedule the next execution if the AI is still running
        if self.ai_is_running:
            # Wait for a user-specified amount of time before running the function again
            wait_time = int(self.user_set_wait_time.get())  # Get the user-specified wait time
            self.window.after(wait_time * 1000, self.execute_ai)


    def toggle_ai(self):
        if self.ai_is_running:
            self.ai_is_running = False
            self.execute_ai_button.config(text="Start AI")
        else:
            self.ai_is_running = True
            self.execute_ai_button.config(text="Stop AI")
            self.execute_ai()  # Start the AI

    def toggle_ai_write(self):
        if self.ai_handler.ai_can_write:
            self.ai_can_write = False
            self.ai_write_button.config(relief=RAISED)  # Change the button appearance to raised when it's off
        else:
            self.ai_can_write = True
            self.ai_write_button.config(relief=SUNKEN)  # Change the button appearance to sunken when it's on

        self.ai_handler.ai_can_write = self.ai_can_write  # Pass the AI writing status to the AI handler

    def start_buyer(self):
        if not hasattr(self, 'is_buying') or not self.is_buying:
            # Start the buying process
            self.is_buying = True
            self.buyer_thread = Thread(target=self.buyer_thread)
            self.buyer_thread.start()
            self.buyer_button.config(relief=SUNKEN, text="Stop Buyer")  # Button appears pressed
        else:
            # Stop the buying process
            self.is_buying = False
            self.buyer_button.config(relief=RAISED, text="Start Buyer")  # Button appears normal

    def buyer_thread(self):
        while self.is_buying:
            try:
                price_bbox = (self.top_left, self.bottom_right)  # Use the bounding box set by the draw_box method
                price = self.ocr_handler.get_text_from_box(price_bbox)
                if price is not None and price < 24000:  # replace with actual threshold
                    self.ocr_handler.click_buy(self.buy_button_coords)  # Use the captured buy button coordinates
                    time.sleep(0.1)  # Wait for the confirmation screen to appear
                    self.ocr_handler.click_yes(self.yes_button_coords)  # Click the "Yes" button
            except Exception as e:
                print(f"Encountered an error: {e}. Retrying in 1 second.")
                time.sleep(0.1)  # Wait for 1 second before retrying

    def set_buy_button(self):
        # Create a mouse listener
        listener = mouse.Listener(on_click=self.on_buy_button_click)
        listener.start()

    def on_buy_button_click(self, x, y, button, pressed):
        if pressed:
            # If the button is pressed, set the buy button coordinates and stop the listener
            self.buy_button_coords = (x, y)
            print(f"Buy button coordinates set to: {self.buy_button_coords}")  # Debug print
            # Stop the listener
            return False  # Returning False stops the listener

    def set_yes_button(self):
        # Create a mouse listener
        listener = mouse.Listener(on_click=self.on_yes_button_click)
        listener.start()

    def on_yes_button_click(self, x, y, button, pressed):
        if pressed:
            # If the button is pressed, set the yes button coordinates and stop the listener
            self.yes_button_coords = (x, y)
            print(f"Yes button coordinates set to: {self.yes_button_coords}")  # Debug print
            # Stop the listener
            return False  # Returning False stops the listener

window = Tk()
my_gui = GUI(window)
window.mainloop()
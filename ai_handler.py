import openai
import re
import pyautogui
import time
from fuzzywuzzy import fuzz

class AIHandler:
    task_goal = ""
    
    def __init__(self, ocr_handler, bbox=None):
        self.ocr_handler = ocr_handler
        self.bbox = bbox
        openai.api_key = ''
        self.conversation = [] # Initialize conversation as an empty list
        self.ai_can_write = False

    def process_task_goal(self, task_goal, initial_prompt, bbox=None):
        self.conversation.append({"role": "system", "content": initial_prompt})

        while not self.is_task_goal_achieved(task_goal):
            # Add user message containing the text visible on the screen
            visible_text = self.ocr_handler.extract_visible_text(bbox)
            self.conversation.append({'role': 'user', 'content': visible_text})
            
            # Get the response from GPT-3
            self.conversation = self.run_conversation()

            # Extract the quoted texts and perform click action
            quoted_texts = self.get_quoted_text(self.conversation[-1]['content'])
            if quoted_texts:  # Ensure there is at least one quoted text
                for quoted_text in quoted_texts:
                    self.locate_and_click_text(quoted_text, bbox)

    def get_quoted_text(self, text):
        quoted = re.findall('"([^"]*)"', text)
        return [q.replace('\n', ' ').replace('\t', ' ') for q in quoted]

    def locate_and_click_text(self, text, bbox=None):
        all_texts_with_coordinates = self.ocr_handler.extract_text_with_coordinates(bbox)

        for recognized_text, coords in all_texts_with_coordinates:
            match_ratio = fuzz.ratio(text.lower(), recognized_text.lower())
            if match_ratio > 50:  # You can adjust this threshold as needed
                ((x1, y1), (x2, y2)) = coords

                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2

                time.sleep(2)  # Wait for 2 seconds before clicking

                # Disable the fail-safe
                pyautogui.FAILSAFE = False

                pyautogui.click(center_x, center_y)

                # Get the screen size
                screen_width, screen_height = pyautogui.size()

                # Move the mouse to the bottom right of the screen
                pyautogui.moveTo(screen_width - 1, screen_height - 1)

                return  # Exit the function once we've clicked on the text

        print(f"The text '{text}' was not found on the screen.")


    def locate_and_click_quoted_gpt3_response(self, initial_prompt, bbox=None):
        self.conversation.append({"role": "system", "content": initial_prompt})
        response = self.run_conversation()
        gpt3_response = response.choices[0].message['content']  # Extract the text from the response

        print(f"GPT-3's full response: {gpt3_response}")  # Print the entire GPT-3 response

        quoted_texts = self.get_quoted_text(gpt3_response)
        if quoted_texts:  # Ensure there is at least one quoted text
            print(f"Found quoted texts in GPT-3 response: {quoted_texts}")  # Print the quoted texts found
            for quoted_text in quoted_texts:
                self.locate_and_click_text(quoted_text, bbox)
                time.sleep(0.2)  # Add delay between clicks on different texts
        else:
            print("No quoted text found in the GPT-3 response.")
        
        return gpt3_response  # Return the full GPT-3 response


    def run_conversation(self):
        max_tokens = 1000 if self.ai_can_write else 10
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0301",
            messages=self.conversation,
            max_tokens=max_tokens,
            temperature = 0.1,
        )
        self.conversation.append({
            "role": response.choices[0].message.role,
            "content": response.choices[0].message.content
        })
        return response

    def is_task_goal_achieved(self, termination_phrase):
        """
        Check if the task goal has been achieved.

        Args:
            termination_phrase (str): The termination phrase to look for in the GPT-3 response.

        Returns:
            bool: True if the termination phrase is in the GPT-3 response, otherwise False.
        """
        # Check if the termination phrase is in the last GPT-3 response (case insensitive)
        return termination_phrase.lower() in self.conversation[-1]['content'].lower()
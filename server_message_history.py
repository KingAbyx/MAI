import os
import json


class ServerMessageHistory:
    def __init__(self, server_id, folder_name):
        self.folder_name = folder_name
        self.server_id = server_id

        self.history_filename = os.path.join(self.folder_name, f"{self.server_id}_history.json")
        self.create_folder_if_not_exists()
        self.message_history = self.load_message_history()

        self.frame_filename = os.path.join(self.folder_name, f"{self.server_id}_frame.json")
        self.frame = self.load_frame()

    def create_folder_if_not_exists(self):
        if not os.path.exists(self.folder_name):
            os.makedirs(self.folder_name)

    def load_message_history(self):
        if os.path.exists(self.history_filename):
            with open(self.history_filename, "r") as f:
                return json.load(f)
        else:
            return []

    def load_frame(self):
        if os.path.exists(self.frame_filename):
            with open(self.frame_filename, "r") as f:
                return json.load(f)
        else:
            # These aren't actually ever used, just an example and a quick way to catch coding errors
            return [{"role": "system", "content": "You are an angry barabarian who likes to scream and shout all the time"},
                    {"role": "user", "content": "What's up, pal?"},
                    {"role": "assistant", "content": "AAAAH, how dare you speak to me, puny weakling AAAAAA"}]

    def add_message(self, message):
        self.message_history.append(message)
        self.save_message_history()

    def trim_message_history(self, top):
        if top:
            self.message_history.pop()
        else:
            self.message_history.pop(0)

    def save_message_history(self):
        with open(self.history_filename, "w") as f:
            json.dump(self.message_history, f, indent=2)

    def save_frame_messages(self):
        with open(self.frame_filename, "w") as f:
            json.dump(self.frame, f, indent=2)

    def clear_message_history(self):
        self.message_history.clear()
        print(f'Message history of {self.server_id} deleted!')

    def remove_message_pair_by_text(self, assistant_message_text):
        indices = [i for i, message in enumerate(self.message_history) if
                   message['role'] == 'assistant' and message['content'] == assistant_message_text]

        if not indices:
            raise ValueError("The specified assistant message text was not found in the message history.")

        # Take the first matching pair
        index = indices[0]

        if index == 0:
            raise ValueError("The first message in the history cannot be removed with this method.")

        self.message_history.pop(index)
        self.message_history.pop(index - 1)


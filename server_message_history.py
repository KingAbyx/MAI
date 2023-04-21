import os
import json


class ServerMessageHistory:
    def __init__(self, server_id, folder_name, message_limit):
        self.folder_name = "message_histories"
        self.server_id = server_id

        self.history_filename = os.path.join(self.folder_name, f"{self.server_id}_history.json")
        self.create_folder_if_not_exists()
        self.message_history = self.load_message_history()
        self.message_limit = 150

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
            return [{"role": "system", "content": "You are an angry barabarian who likes to scream and shout all the time"},
                    {"role": "user", "content": "What's up, pal?"},
                    {"role": "assistant", "content": "AAAAH, how dare you speak to me, puny weakling AAAAAA"}]

    def add_message(self, message):
        self.message_history.append(message)
        self.trim_message_history()
        self.save_message_history()

    def trim_message_history(self):
        if len(self.message_history) > self.message_limit:
            self.message_history.pop(0)

    def save_message_history(self):
        with open(self.history_filename, "w") as f:
            json.dump(self.message_history, f, indent=2)

    def save_frame_messages(self):
        with open(self.frame_filename, "w") as f:
            json.dump(self.frame, f, indent=2)

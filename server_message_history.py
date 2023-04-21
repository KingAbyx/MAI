import os
import json


class ServerMessageHistory:
    def __init__(self, server_id):
        self.folder_name = "message_histories"
        self.server_id = server_id
        self.filename = os.path.join(self.folder_name, f"{self.server_id}_history.json")
        self.create_folder_if_not_exists()
        self.message_history = self.load_message_history()

    def create_folder_if_not_exists(self):
        if not os.path.exists(self.folder_name):
            os.makedirs(self.folder_name)

    def load_message_history(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                return json.load(f)
        else:
            return []

    def add_message(self, message):
        self.message_history.append(message)
        self.save_message_history()

    def save_message_history(self):
        with open(self.filename, "w") as f:
            json.dump(self.message_history, f, indent=2)

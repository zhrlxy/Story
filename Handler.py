import base64
import requests
import os
import shutil

class DataHandler:
    def __init__(self):
        pass
    @staticmethod
    def encode_image(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    @staticmethod
    def get_image_from_url(url, image_name, save_path):
        full_path = os.path.join(save_path, image_name)
        response = requests.get(url)
        if response.status_code == 200:
            with open(full_path, "wb") as f:
                f.write(response.content)
            print(f"Image Saved In {full_path}")
        return full_path
    @staticmethod
    def save_voice(content, name, save_path):
        full_path = os.path.join(save_path, name)
        with open(full_path, "wb") as f:
            f.write(content)
        print(f"Voice Saved In {full_path}")
        return full_path
    @staticmethod
    def save_story(content, name, save_path):
        full_path = os.path.join(save_path, name)
        with open(full_path, "w") as f:
            f.write(content)
        print(f"Story Saved In {full_path}")
        return full_path
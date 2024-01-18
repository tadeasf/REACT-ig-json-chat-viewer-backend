import random
import base64
from locust import task, between, FastHttpUser
from dotenv import load_dotenv
import os

load_dotenv()

class TestCaddy(FastHttpUser):
    wait_time = between(1, 5)  # Simulate real user behavior

    def on_start(self):
        self.auth_header = self.create_basic_auth_header(os.getenv("USERNAME"), os.getenv("PASSWORD"))
        self.word_list = self.load_word_list()

    def load_word_list(self):
        # Load a list of words or use a fixed list for random queries
        return ['have', 'this', 'they', 'there', 'which', 'their', 'about', 'would', 'other', 'could', 'these', 'still', 'while', 'where', 'should', 'because', 'through', 'before', 'without', 'something', 'mohu', 'vice', 'clovek', 'dulezite', 'vi', 'budu', 'jsem', 'vim', 'potrebuji', 'chci', 'muze', 'musim', 'dobry', 'tady', 'jit', 'delat', 'kde', 'velmi', 'neco', 'cas']

    def create_basic_auth_header(self, username, password):
        credentials = f'{username}:{password}'
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return {'Authorization': f'Basic {encoded_credentials}'}

    @task
    def search_random_word(self):
        random_word = random.choice(self.word_list)
        body = {"query": random_word}
        headers = self.auth_header.copy()
        headers.update({
            "Accept": "*/*",
            "Accept-Language": "en-GB,en;q=0.9",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        })
        self.client.post("/search", json=body, headers=headers, name="Random Word Search")

# Usage: locust -f script_name.py --host=https://secondary.dev.tadeasfort.com

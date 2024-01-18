import base64
from locust import task, between, FastHttpUser
from dotenv import load_dotenv
import os

load_dotenv()

class TestCaddy(FastHttpUser):
    wait_time = between(1, 5)  # Simulate real user behavior

    def on_start(self):
        # Encode your username and password in base64 for Basic Auth
        self.auth_header = self.create_basic_auth_header(
            os.getenv("USERNAME"), os.getenv("PASSWORD")
        )

    def create_basic_auth_header(self, username, password):
        # Create the Basic Auth header
        credentials = f'{username}:{password}'
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return {'Authorization': f'Basic {encoded_credentials}'}

    @task
    def load_initial_page(self):
        self.client.get("/", headers=self.auth_header, name="Initial Page Load")

    @task
    def fetch_messages(self):
        collection_names = ["RachelRachel", "AnalniAnet", "KristynaSmirova", "AndreaZizkova",
                            "MarketaSvobodova", "KarolinaLiskova", "KarolinaCernochova", "KlaraSmitkova", "OliStemenkova",
                            "NikolaHronova", "AnetaStokrova", "MariaGorbatova_1", "AnnaPopelkova", "LucieKopecka"]
        for name in collection_names:
            headers = self.auth_header.copy()
            headers.update({
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
            })
            self.client.get(f"/messages/{name}", headers=headers, name=f"Fetch messages from this lovely person: {name}")


# Run the test with:
# Usage: locust -f script_name.py --host=https://secondary.dev.tadeasfort.com
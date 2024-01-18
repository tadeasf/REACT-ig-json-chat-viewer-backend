from locust import task, between, FastHttpUser

class TestCaddy(FastHttpUser):
    wait_time = between(1, 5)
    @task
    def fetch_messages(self):
        collection_names = [["RachelRachel", "KristynaSmirova", "AndreaZizkova",
                            "MarketaSvobodova", "KarolinaLiskova", "KarolinaCernochova", "KlaraSmitkova"]]

        for name in collection_names:
            response = self.client.get(f"/messages/{name}", name=f"Fetch messages from: {name}")
#            print(f"Response from {name}: {response.text}")
            self.client.get(f"/messages/{name}", name=f"Fetch messages from this lovely person: {name}")
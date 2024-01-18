from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 2)  # Simulated users wait 1-2 seconds between tasks

    @task
    def load_messages(self):
        self.client.get("/messages/KristynaSmirova")

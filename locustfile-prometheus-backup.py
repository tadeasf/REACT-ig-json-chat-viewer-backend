from locust import task, SequentialTaskSet, FastHttpUser

class PrometheusAPITasks(SequentialTaskSet):
    def on_start(self):
        self.base_url = "http://167.86.68.173:9090"
        self.endpoints = [
            "/",
            "/api/v1/alertmanagers",
            "/api/v1/rules",
            "/api/v1/status/buildinfo",
            "/api/v1/query_range",
            "/api/v1/query",
            "/api/v1/labels",  # Corrected from /api/v1/labes
            "/api/v1/scrape_pools"  # Corrected from /api/v1/screape_pools
        ]

    @task
    def query_prometheus(self):
        for endpoint in self.endpoints:
            self.client.get(self.base_url + endpoint)

class PrometheusUser(FastHttpUser):
    tasks = [PrometheusAPITasks]

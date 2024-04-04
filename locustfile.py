from locust import task, FastHttpUser
import gevent.pool


class MyUser(FastHttpUser):

    @task
    def my_task(self):
        self.client.get("/stress-test")

    @task
    def t(self):
        def concurrent_request(url):
            self.client.get(url)

        pool = gevent.pool.Pool()
        urls = ["/stress-test", "/collections", "/load-cpu"]
        for url in urls:
            pool.spawn(concurrent_request, url)
        pool.join()

from locust import task, SequentialTaskSet, FastHttpUser
import gevent.pool # type: ignore

class CpuLoadingTasks(SequentialTaskSet):
    def on_start(self):
        self.endpoints = [
            "/collections/alphabetical",
            # "/collections",
            "/messages/KlaraSmitkova",
            # "/messages/KristynaSmirova",
            # "/messages/AnalniAnet",
            # "/messages/RachelRachel",
            # "/messages/AndreaZizkova",
            # "/messages/KarolinaLiskova",
            # "/messages/MarketaSvobodova",
            # # "/stress-test"
        ]

    @task
    def t(self):
        for endpoint in self.endpoints:
            self.client.get(endpoint)

class CpuLoadingNerd(FastHttpUser):
    tasks = [CpuLoadingTasks]
# class StressedUser(FastHttpUser):
    
#     @task
#     def t(self):
#         self.client.get("/stress-test")

# # concurrent request to different endpoints
# class PoolOfRandomGuys(FastHttpUser):
#     @task
#     def t(self):
#         def concurrent_request(url):
#             self.client.get(url)

#         pool = gevent.pool.Pool()
#         urls = ['/collections/alphabetical', '/collections', '/messages/RachelRachel', '/messages/RachelRachel/photo']
#         for url in urls:
#             pool.spawn(concurrent_request, url)
#         pool.join()

'''
class Collectionist(FastHttpUser):

    @task
    def t(self):
        self.client.get("/collections")

class PedantSorter(FastHttpUser):

    @task
    def t(self):
        self.client.get("/collections/alphabetical")

class LivesInThePast(FastHttpUser):

    @task
    def t(self):
        self.client.get("/messages/AnalniAnet")

class PortraitURL(FastHttpUser):

    @task
    def t(self):
        self.client.get("/messages/AnalniAnet/photo")
'''

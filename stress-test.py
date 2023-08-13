import requests
import random
import time
import json
import seaborn as sns
import matplotlib.pyplot as plt

def get_integer_input(prompt_msg):
    while True:
        try:
            value = int(input(prompt_msg))
            return value
        except ValueError:
            print("Please enter a valid integer.")

num_calls = get_integer_input("Enter the number of API calls: ")
duration = get_integer_input("Enter the duration in seconds for all calls: ")

endpoints = [
    "https://server.kocouratko.eu/messages/Krist%C3%BDna%20%C5%A0m%C3%ADrov%C3%A1",
    "https://server.kocouratko.eu/messages/Andrea%20%C5%BDi%C5%BEkov%C3%A1",
    "https://server.kocouratko.eu/messages/Mark%C3%A9ta%20Svobodov%C3%A1",
    "https://server.kocouratko.eu/messages/Krist%C3%BDnka%20%C5%A0m%C3%ADrov%C3%A1",
    "https://server.kocouratko.eu/messages/Zuzana%20Jandov%C3%A1",
    "https://server.kocouratko.eu/messages/Veronika%20Homolov%C3%A1",
    "https://server.kocouratko.eu/messages/Karol%C3%ADna%20%C4%8Cernochov%C3%A1",
    "https://server.kocouratko.eu/messages/Ernesta%20%C5%A0imkevi%C4%8Di%C5%ABt%C4%97",
    "https://server.kocouratko.eu/messages/Karol%C3%ADna%20Li%C5%A1kov%C3%A1"
]

data = []

start_time = time.time()

for _ in range(num_calls):
    endpoint = random.choice(endpoints)
    
    # Measure HTTP latency
    latency_start = time.time()
    response = requests.get(endpoint)
    latency_end = time.time()

    http_latency = latency_end - latency_start
    response_time = response.elapsed.total_seconds()
    response_size = len(response.content)

    data.append({
        "endpoint": endpoint,
        "http_latency": http_latency,
        "response_time": response_time,
        "response_size": response_size
    })

    time_elapsed = time.time() - start_time
    if time_elapsed < duration:
        sleep_time = (duration - time_elapsed) / (num_calls - _)
        time.sleep(sleep_time)

# Save raw data to JSON
with open("raw_data.json", "w") as f:
    json.dump(data, f)

# Calculate statistics
avg_response_time = sum([d["response_time"] for d in data]) / len(data)
median_response_time = sorted([d["response_time"] for d in data])[len(data) // 2]
avg_response_size = sum([d["response_size"] for d in data]) / len(data)
median_response_size = sorted([d["response_size"] for d in data])[len(data) // 2]
avg_http_latency = sum([d["http_latency"] for d in data]) / len(data)
median_http_latency = sorted([d["http_latency"] for d in data])[len(data) // 2]

# Performance score (simplified for now)
performance_score = 1000 / (avg_response_time * avg_response_size / 1000)

print(f"Average Response Time: {avg_response_time}")
print(f"Median Response Time: {median_response_time}")
print(f"Average Response Size: {avg_response_size}")
print(f"Median Response Size: {median_response_size}")
print(f"Average HTTP Latency: {avg_http_latency}")
print(f"Median HTTP Latency: {median_http_latency}")
print(f"Performance Score: {performance_score}")

# Plotting
sns.set_style("whitegrid")

# Example: Response Time vs Endpoint
plt.figure(figsize=(10, 6))
sns.barplot(x=[d["endpoint"] for d in data], y=[d["response_time"] for d in data])
plt.xticks(rotation=45)
plt.title("Response Time vs Endpoint")
plt.tight_layout()
plt.savefig("response_time_vs_endpoint.jpg")

# 1. Response Time Distribution
plt.figure(figsize=(10, 6))
sns.histplot(data=[d["response_time"] for d in data], bins=30, kde=True)
plt.title("Response Time Distribution")
plt.xlabel("Response Time (s)")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig("response_time_distribution.jpg")

# 2. HTTP Latency Distribution
plt.figure(figsize=(10, 6))
sns.histplot(data=[d["http_latency"] for d in data], bins=30, kde=True)
plt.title("HTTP Latency Distribution")
plt.xlabel("HTTP Latency (s)")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig("http_latency_distribution.jpg")

# 3. Response Size Distribution
plt.figure(figsize=(10, 6))
sns.histplot(data=[d["response_size"] for d in data], bins=30, kde=True)
plt.title("Response Size Distribution")
plt.xlabel("Response Size (bytes)")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig("response_size_distribution.jpg")

# 4. Response Time vs HTTP Latency
plt.figure(figsize=(10, 6))
sns.scatterplot(x=[d["response_time"] for d in data], y=[d["http_latency"] for d in data])
plt.title("Response Time vs HTTP Latency")
plt.xlabel("Response Time (s)")
plt.ylabel("HTTP Latency (s)")
plt.tight_layout()
plt.savefig("response_time_vs_http_latency.jpg")

# 5. Response Time vs Response Size
plt.figure(figsize=(10, 6))
sns.scatterplot(x=[d["response_time"] for d in data], y=[d["response_size"] for d in data])
plt.title("Response Time vs Response Size")
plt.xlabel("Response Time (s)")
plt.ylabel("Response Size (bytes)")
plt.tight_layout()
plt.savefig("response_time_vs_response_size.jpg")

# 6. Number of Calls to Each Endpoint
plt.figure(figsize=(10, 6))
sns.countplot(x=[d["endpoint"] for d in data])
plt.xticks(rotation=45)
plt.title("Number of Calls to Each Endpoint")
plt.xlabel("Endpoint")
plt.ylabel("Number of Calls")
plt.tight_layout()
plt.savefig("calls_per_endpoint.jpg")

print("Stress test completed!")

print("Stress test completed!")

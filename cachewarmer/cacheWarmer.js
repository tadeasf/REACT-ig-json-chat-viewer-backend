const express = require("express");
const redis = require("redis");
const cors = require("cors");

const app = express();
const port = 3039;
const redisClient = redis.createClient({
  url: "redis://localhost:6379",
});

const mainAppUri = "https://messenger.tadeasfort.com/";

redisClient.connect();

async function fetchWithImport(url) {
  const { default: fetch } = await import("node-fetch");
  return fetch(url);
}

//ALLOW CORS FOR LOAD BALANCER
app.use(
  cors({
    origin: "*",
  })
);

// Fetch collections and store them in Redis
async function warmUpCollectionsCache() {
  const collectionsResponse = await fetchWithImport(
    `${mainAppUri}/collections`
  );
  const collectionsData = await collectionsResponse.json();
  await redisClient.set("collections", JSON.stringify(collectionsData));

  // Warm up the cache for collections sorted alphabetically
  const collectionsAlphabeticalResponse = await fetchWithImport(
    `${mainAppUri}/collections/alphabetical`
  );
  const collectionsAlphabeticalData =
    await collectionsAlphabeticalResponse.json();
  await redisClient.set(
    "collectionsAlphabetical",
    JSON.stringify(collectionsAlphabeticalData)
  );

  // Now, warm up cache for each collection
  for (let collection of collectionsData) {
    // Assuming collectionsData is an array of collection names
    await warmUpCacheForCollectionEndpoints(collection.name);
  }
}

// Warm up cache for messages and photos of a collection
async function warmUpCacheForCollectionEndpoints(collectionName) {
  // Warm up cache for messages of the collection
  // Here, you might need logic to determine `fromDate` and `toDate` if applicable
  const messagesResponse = await fetchWithImport(
    `${mainAppUri}/messages/${encodeURIComponent(collectionName)}`
  );
  const messagesData = await messagesResponse.json();
  const messagesCacheKey = `messages-${collectionName}`; // Adjust the cache key as needed
  await redisClient.set(
    messagesCacheKey,
    JSON.stringify(messagesData),
    "EX",
    36000
  );

  // Warm up cache for photos of the collection
  const photosResponse = await fetchWithImport(
    `${mainAppUri}/photos/${encodeURIComponent(collectionName)}`
  );
  const photosData = await photosResponse.json();
  const photosCacheKey = `photos-${collectionName}`; // Adjust the cache key as needed
  await redisClient.set(
    photosCacheKey,
    JSON.stringify(photosData),
    "EX",
    36000
  );
}

// Endpoint to trigger cache warming
app.get("/warm-up-cache", async (req, res) => {
  try {
    await warmUpCollectionsCache();
    console.log("Cache warming process completed successfully.");
    res.send("Cache warming initiated. Check server logs for progress.");
  } catch (error) {
    console.error("Error during cache warming:", error);
    res.status(500).send("Failed to warm up cache");
  }
});

app.listen(port, () => {
  console.log(`Cache warmer running at http://localhost:${port}`);
});

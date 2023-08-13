/** @format */

require("dotenv").config();
const express = require("express");
const { MongoClient } = require("mongodb");
const cors = require("cors");
const morgan = require("morgan");
const app = express();
const port = process.env.PORT || 5555;
const multer = require("multer");
const fs = require("fs").promises;
const path = require("path");
const os = require("os");
const bodyParser = require("body-parser");
const { combine_and_convert_json_files } = require("./json_combiner");
const { LRUCache } = require('lru-cache')

// Database Connection Management
const uri = process.env.MONGODB_URI;
const client = new MongoClient(uri, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
  connectTimeoutMS: 30000,
  socketTimeoutMS: 360000,
  compressors: ['zlib'],
  zlibCompressionLevel: 6,
  maxPoolSize: 50,
  minPoolSize: 10,
  maxConnecting: 5,
  maxIdleTimeMS: 60000,
  waitQueueTimeoutMS: 30000,
  retryReads: true,
  retryWrites: true,
  directConnection: false,
  writeConcern: { w: 'majority', wtimeout: 5000 }
});

function sizeof(object) {
  const stringifiedObject = JSON.stringify(object);
  const bytes = Buffer.from(stringifiedObject).length;
  return bytes;
}

const cacheOptions = {
  maxSize: 8 * 1024 * 1024 * 1024, // 4GB
  ttl: 7 * 24 * 60 * 60 * 1000, // 12 hours
  sizeCalculation: (value) => {
    // Assuming each message is a JSON string, adjust if needed
    return Buffer.from(JSON.stringify(value)).length;
  },
  length: (value) => {
    // Return the number of objects in the cached collection
    return Array.isArray(value) ? value.length : 1;
  },
  dispose: (value, key) => {
    // Handle any cleanup if needed when an item is removed from cache
  }
};

const cache = new LRUCache(cacheOptions);


client.connect();

app.use(cors({
  origin: [
    "https://kocouratko.cz",
    "https://server.kocouratko.eu",
    "http://localhost:5009",
    "http://193.86.152.148:5009",
    "http://193.86.152.148:3000",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3335",
    "app://.",
    "tauri://localhost",
  ],
}));

app.use(morgan("combined")); // Using Morgan for logging

app.use(bodyParser.json());

app.use("/photos", express.static(path.join(__dirname, "photos"))); // Serving static photos

// Middleware for file uploads with structured directory
const storage = multer.diskStorage({
  destination: async function (req, file, cb) {
    const dir = `uploads/${req.get("host")}`;
    await fs.mkdir(dir, { recursive: true });
    cb(null, dir);
  },
  filename: function (req, file, cb) {
    cb(null, file.originalname);
  },
});

function sanitizeName(name) {
  return name.replace(/\s+/g, "_").replace(/[^a-zA-Z0-9_]/g, "");
}

// Middleware for photo uploads with structured naming
const photoStorage = multer.diskStorage({
  destination: function (req, file, cb) {
    const dir = path.join(__dirname, "photos");
    cb(null, dir);
  },
  filename: function (req, file, cb) {
    const collectionName = decodeURIComponent(req.params.collectionName);
    const sanitizedCollectionName = sanitizeName(collectionName); // Assuming you have a sanitizeName function
    const filename = `${sanitizedCollectionName}-${file.originalname}`;
    cb(null, filename);
  },
});

const upload_photo = multer({ storage: photoStorage });


const upload = multer({ storage: storage });

// Middleware to track start time of request
app.use((req, res, next) => {
  req.startTime = Date.now();
  next();
});

// Utility function to format time difference
function formatTimeDifference(startTime) {
  const endTime = Date.now();
  const diff = new Date(endTime - startTime);
  const hh = String(diff.getUTCHours()).padStart(2, "0");
  const mm = String(diff.getUTCMinutes()).padStart(2, "0");
  const ss = String(diff.getUTCSeconds()).padStart(2, "0");
  return `${hh}:${mm}:${ss}`;
}

// Utility function to log endpoint info
function logEndpointInfo(req, res, endpoint) {
  const timeTaken = formatTimeDifference(req.startTime);
  console.log(
    `Endpoint: ${endpoint}, Request Contents: ${JSON.stringify(
      req.body
    )}, Requester URL: ${req.get("origin")}, Time Taken: ${timeTaken}`
  );
}

// Error Handling
process.on("uncaughtException", (err) => {
  console.error("Uncaught Exception:", err);
  logError(err);
  process.exit(1); // Exit the process with failure
});

process.on("unhandledRejection", (reason, promise) => {
  console.error("Unhandled Rejection at:", promise, "reason:", reason);
  logError(reason);
  setTimeout(() => {
    process.exit(1);
  }, 1000); // Delay for 1 second
});

async function logError(error) {
  const errorLog = {
    timestamp: new Date().toISOString(),
    message: error.message,
    stack: error.stack,
  };

  const logsDir = path.join(__dirname, "logs");
  const logFilePath = path.join(logsDir, "error-log.json");

  try {
    await fs.mkdir(logsDir);
  } catch (err) {
    if (err.code !== "EEXIST") {
      throw err;
    }
  }

  try {
    await fs.appendFile(logFilePath, JSON.stringify(errorLog) + os.EOL);
  } catch (err) {
    console.error("Error while writing error log:", err);
  }

  console.error("Error logged:", errorLog);

  return errorLog;
}

async function cacheAllCollections() {
  const startTime = Date.now();
  const db = client.db("messages");
  const collections = await db.listCollections().toArray();
  
  const collectionData = [];
  let totalMessages = 0;

  for (const collection of collections) {
    const collectionName = collection.name;
    const messages = await db.collection(collectionName)
      .aggregate(
        [
          { $sort: { timestamp_ms: 1 } },
          { $addFields: { timestamp: { $toDate: "$timestamp_ms" } } },
        ]
      )
      .toArray();
    totalMessages += messages.length;
    
    // Cache the messages for each collection
    cache.set(`messages-${collectionName}`, messages);

    const count = await db.collection(collectionName).countDocuments();
    collectionData.push({
      name: collectionName,
      messageCount: count
    });
  }

  // Sort collections by message count in descending order
  collectionData.sort((a, b) => b.messageCount - a.messageCount);

  // Cache the sorted list of collection data (name and message count)
  cache.set("collections", collectionData);
  
  const endTime = Date.now();
  const timeTaken = (endTime - startTime) / 1000; // in seconds
  
  // Calculate the total size of the cache in bytes
  let totalSize = 0;
  cache.forEach((value) => {
    totalSize += sizeof(value);
  });
  // totalSize in MB as integer (rounded down)
  const totalSizeMB = Math.floor(totalSize / 1024 / 1024);

  console.log(`Cached ${collections.length} collections with ${totalMessages} messages in ${timeTaken} seconds. Total cache size: ${totalSizeMB} MB`);
}


cacheAllCollections();

// Endpoint to get collections
app.get("/collections", async (req, res) => {
  const cacheKey = "collections";
  const cachedData = cache.get(cacheKey);

  if (cachedData) {
    return res.status(200).json(cachedData);
  }

  const db = client.db("messages");x
  const collections = await db.listCollections().toArray();
  
  const collectionData = [];
  for (const collection of collections) {
    const count = await db.collection(collection.name).countDocuments();
    collectionData.push({
      name: collection.name,
      messageCount: count
    });
  }

  console.log(collectionData);
  // Sort collections by message count
  collectionData.sort((a, b) => b.messageCount - a.messageCount);

  cache.set(cacheKey, collectionData);

  logEndpointInfo(req, res, "GET /collections");
  res.status(200).json(collectionData);
});



// Endpoint to get messages by collection name

app.get("/messages/:collectionName", async (req, res) => {
  const collectionName = decodeURIComponent(req.params.collectionName);
  const cacheKey = `messages-${collectionName}`;
  const cachedData = cache.get(cacheKey);

  if (cachedData) {
    return res.status(200).json(cachedData);
  }

  const db = client.db("messages");
  const collection = db.collection(collectionName);
  const messages = await collection
    .aggregate(
      [
        { $sort: { timestamp_ms: 1 } },
        { $addFields: { timestamp: { $toDate: "$timestamp_ms" } } },
      ]
    )
    .toArray();

  cache.set(cacheKey, messages);

  logEndpointInfo(req, res, `GET /messages/${req.params.collectionName}`);
  res.status(200).json(messages);
});

// Endpoint to upload messages
app.post("/upload", upload.array("files"), async (req, res) => {
  const combinedJson = await combine_and_convert_json_files(req.files.map((file) => file.path));
  const { participants, messages } = combinedJson;
  const collectionName = participants[0].name;

  const db = client.db("messages");
  const collections = await db.listCollections({ name: collectionName }).toArray();
  if (collections.length > 0) {
    logEndpointInfo(req, res, "POST /upload");
    res.status(409).json({
      message: `A collection with the name "${collectionName}" already exists.`,
    });
    return;
  }

  const collection = db.collection(collectionName);
  await collection.insertMany(messages);

  logEndpointInfo(req, res, "POST /upload");
  res.status(200).json({
    message: `Messages uploaded to collection: ${collectionName}`,
    collectionName: collectionName,
    messageCount: messages.length,
  });
  // After inserting messages
  const count = await collection.countDocuments();
  const cachedCollections = cache.get("collections") || [];
  const updatedCollections = cachedCollections.filter(col => col.name !== collectionName);
  updatedCollections.push({
    name: collectionName,
    messageCount: count
  }); 
cache.set("collections", updatedCollections);

  
});

// Endpoint to delete a collection
app.delete("/delete/:collectionName", async (req, res) => {
  const collectionName = decodeURIComponent(req.params.collectionName);

  const db = client.db("messages");
  const collection = db.collection(collectionName);
  await collection.drop();

  logEndpointInfo(req, res, `DELETE /delete/${req.params.collectionName}`);
  res.status(200).json({
    message: `Collection "${collectionName}" deleted.`,
    collectionName: collectionName,
  });
  // After dropping the collection
  const cachedCollections = cache.get("collections") || [];
  const updatedCollections = cachedCollections.filter(col => col.name !== collectionName);
  cache.set("collections", updatedCollections);
});

// Endpoint to check if a photo is available for a collection
app.get("/messages/:collectionName/photo", async (req, res) => {
  const collectionName = decodeURIComponent(req.params.collectionName);

  const db = client.db("messages");
  const collection = db.collection(collectionName);
  const result = await collection.findOne({ photo: true });

  if (!result) {
    logEndpointInfo(req, res, `GET /messages/${req.params.collectionName}/photo`);
    res.status(200).json({ isPhotoAvailable: false, photoUrl: null });
    return;
  }

  const photoUrl = `${req.protocol}://${req.get("host")}/serve/photo/${collectionName}`;
  logEndpointInfo(req, res, `GET /messages/${req.params.collectionName}/photo`);
  res.status(200).json({ isPhotoAvailable: true, photoUrl: photoUrl });
});

// Endpoint to upload a photo for a collection
app.post("/upload/photo/:collectionName", upload_photo.single("photo"), async (req, res) => {
  if (!req.file) {
    logEndpointInfo(req, res, `POST /upload/photo/${req.params.collectionName}`);
    res.status(400).json({ message: "No photo provided" });
    return;
  }

  const db = client.db("messages");
  const collection = db.collection(decodeURIComponent(req.params.collectionName));
  await collection.updateOne({}, { $set: { photo: true } }, { upsert: true });

  logEndpointInfo(req, res, `POST /upload/photo/${req.params.collectionName}`);
  res.status(200).json({ message: "Photo uploaded successfully" });
});

// Endpoint to serve a photo for a collection
app.get("/serve/photo/:collectionName", async (req, res) => {
  const collectionName = sanitizeName(decodeURIComponent(req.params.collectionName));
  const photoDir = path.join(__dirname, "photos");
  const files = await fs.readdir(photoDir);
  const photoFile = files.find((file) => file.startsWith(collectionName));

  if (!photoFile) {
    logEndpointInfo(req, res, `GET /serve/photo/${req.params.collectionName}`);
    res.status(404).json({ message: "Photo not found" });
    return;
  }

  const photoPath = path.join(photoDir, photoFile);
  logEndpointInfo(req, res, `GET /serve/photo/${req.params.collectionName}`);
  res.sendFile(photoPath);
});

// Endpoint to rename a collection
app.put("/rename/:currentCollectionName", async (req, res) => {
  const currentCollectionName = decodeURIComponent(req.params.currentCollectionName);
  const newCollectionName = req.body.newCollectionName.trim();

  if (!newCollectionName || !/^[a-zA-Z0-9_]+$/.test(newCollectionName)) {
    logEndpointInfo(req, res, `PUT /rename/${req.params.currentCollectionName}`);
    res.status(400).json({
      message: "Invalid collection name: Does not match naming convention",
    });
    return;
  }

  const db = client.db("messages");
  const currentCollection = db.collection(currentCollectionName);
  await currentCollection.rename(newCollectionName);

  logEndpointInfo(req, res, `PUT /rename/${req.params.currentCollectionName}`);
  res.status(200).json({ message: `Collection renamed to ${newCollectionName}` });
  // After renaming the collection
  const count = await db.collection(newCollectionName).countDocuments();
  const cachedCollections = cache.get("collections") || [];
  const updatedCollections = cachedCollections.filter(col => col.name !== currentCollectionName);
  updatedCollections.push({
    name: newCollectionName,
    messageCount: count
  });
  cache.set("collections", updatedCollections);

});

// Endpoint to delete a photo for a collection
app.delete("/delete/photo/:collectionName", async (req, res) => {
  const collectionName = sanitizeName(decodeURIComponent(req.params.collectionName));
  const photoDir = path.join(__dirname, "photos");
  const files = await fs.readdir(photoDir);
  const photoFile = files.find((file) => file.startsWith(collectionName));

  if (!photoFile) {
    logEndpointInfo(req, res, `DELETE /delete/photo/${req.params.collectionName}`);
    res.status(404).json({ message: "Photo not found" });
    return;
  }

  const photoPath = path.join(photoDir, photoFile);
  await fs.unlink(photoPath);

  logEndpointInfo(req, res, `DELETE /delete/photo/${req.params.collectionName}`);
  res.status(200).json({ message: "Photo deleted successfully" });
});

app.get("/cross-search/:searchTerm", async (req, res) => {
  const searchTerm = req.params.searchTerm;
  const allResults = [];

  cache.forEach((messages, collectionName) => {
    const matchingMessages = messages.filter((message) =>
      message.content.includes(searchTerm)
    );
    allResults.push(...matchingMessages);
  });

  // Sort the results by timestamp
  allResults.sort((a, b) => a.timestamp_ms - b.timestamp_ms);

  logEndpointInfo(req, res, `GET /cross-search/${searchTerm}`);
  res.status(200).json(allResults);
});
// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('Something broke!');
});

app.listen(port, () => {
  console.log(`Server listening on port number: ${port}`);
});
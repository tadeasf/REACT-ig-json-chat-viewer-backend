/** @format */

require("dotenv").config();
const express = require("express");
const { MongoClient } = require("mongodb");
const cors = require("cors");
const morgan = require("morgan");
let generate, count;
import("random-words").then((randomWords) => {
  ({ generate, count } = randomWords);
});
const app = express();
const port = process.env.PORT || 5555;
const multer = require("multer");
const fs = require("fs").promises;
const path = require("path");
const os = require("os");
const bodyParser = require("body-parser");
const { combine_and_convert_json_files } = require("./json_combiner");
const { LRUCache } = require("lru-cache");
const { v4: uuidv4 } = require("uuid");
const compression = require("compression");
const diacritics = require("diacritics");

// Database Connection Management
const uri = process.env.MONGODB_URI;
const client = new MongoClient(uri, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
  connectTimeoutMS: 3600,
  socketTimeoutMS: 3600,
  maxPoolSize: 50,
  minPoolSize: 10,
  maxConnecting: 5,
  maxIdleTimeMS: 60000,
  waitQueueTimeoutMS: 30000,
  retryReads: true,
  retryWrites: true,
  directConnection: false,
  writeConcern: { w: "majority", wtimeout: 5000 },
});

const MESSAGE_DATABASE = "kocouratciMessenger";

function sizeof(object) {
  const stringifiedObject = JSON.stringify(object);
  const bytes = Buffer.from(stringifiedObject).length;
  return bytes;
}

const cacheOptions = {
  maxSize: 12 * 1024 * 1024 * 1024, // 8
  ttl: 1 * 24 * 60 * 60 * 1000, // 1 day
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
  },
};

const cache = new LRUCache(cacheOptions);

client.connect();

// app.use(cors({
//   origin: [
//     "https://kocouratko.cz",
//     "https://server.kocouratko.eu",
//     "http://localhost:5009",
//     "http://193.86.152.148:5009",
//     "http://193.86.152.148:3000",
//     "http://localhost:3000",
//     "http://localhost:3001",
//     "http://localhost:3335",
//     "app://.",
//     "tauri://localhost",
//   ],
// }));

//ALLOW CORS FOR LOAD BALANCER
app.use(
  cors({
    origin: "*",
  })
);

app.use(morgan("combined")); // Using Morgan for logging
app.use(compression());
app.use(bodyParser.json());

app.get("/", (req, res) => {
  res.send("Hi, Blackbox, grab some data! omnomnomnom...");
});

// Function to sanitize collection names
const sanitizeName = (name) => {
  return name
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, "")
    .replace(/[^a-zA-Z0-9]/g, "");
};
// Middleware for file uploads with structured directory
const storage = multer.diskStorage({
  destination: async function (req, file, cb) {
    // Generate a UUID for the subdirectory
    const uniqueSubdir = uuidv4();

    const dir = `uploads/${uniqueSubdir}/${req.get("host")}`;
    await fs.mkdir(dir, { recursive: true });
    cb(null, dir);
  },
  filename: function (req, file, cb) {
    cb(null, file.originalname);
  },
});

// Middleware for photo uploads with structured naming
const photoStorage = multer.diskStorage({
  destination: function (req, file, cb) {
    const dir = path.join(__dirname, "photos");
    cb(null, dir);
  },
  filename: function (req, file, cb) {
    const collectionName = decodeURIComponent(req.params.collectionName);
    const sanitizedCollectionName = sanitizeName(collectionName);
    const extension = path.extname(file.originalname); // Get the extension of the original file
    const filename = `${sanitizedCollectionName}${extension}`; // Construct the filename using only the sanitized collection name and extension
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

function logEndpointInfo(req, res, endpoint) {
  const timeTaken = formatTimeDifference(req.startTime);
  const requesterIP = req.ip; // Get the IP address of the requester
  console.log(
    `Endpoint: ${endpoint}, Request Contents: ${JSON.stringify(
      req.body
    )}, Requester IP: ${requesterIP}, Time Taken: ${timeTaken}`
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
  const db = client.db(MESSAGE_DATABASE);
  const collections = await db.listCollections().toArray();

  const collectionData = [];
  let totalMessages = 0;

  for (const collection of collections) {
    const collectionName = collection.name;
    const messages = await db
      .collection(collectionName)
      .aggregate([
        { $sort: { timestamp_ms: 1 } },
        { $addFields: { timestamp: { $toDate: "$timestamp_ms" } } },
      ])
      .toArray();
    totalMessages += messages.length;

    // Cache the messages for each collection
    cache.set(`messages-${collectionName}`, messages);

    const count = await db.collection(collectionName).countDocuments();
    collectionData.push({
      name: collectionName,
      messageCount: count,
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

  console.log(
    `Cached ${collections.length} collections with ${totalMessages} messages in ${timeTaken} seconds. Total cache size: ${totalSizeMB} MB`
  );
}

// cacheAllCollections(); // -> too heavy now, turn of for perf testing

async function sanitizeCollections() {
  try {
    await client.connect();
    const db = client.db(MESSAGE_DATABASE);

    // Fetch all collection names
    const collections = await db.listCollections().toArray();
    const collectionNames = collections.map((c) => c.name);

    const promises = collectionNames.map(async (collectionName) => {
      // Get the total count of documents that meet the criteria
      const totalCount = await db.collection(collectionName).countDocuments({
        content: { $exists: true, $ne: null },
        sanitizedContent: { $exists: false },
      });

      // Process all documents that meet the criteria using bulk updates
      const bulkOps = [];
      const batchSize = 100; // Adjust the batch size as needed

      for (let skip = 0; skip < totalCount; skip += batchSize) {
        const documents = await db
          .collection(collectionName)
          .find({
            content: { $exists: true, $ne: null },
            sanitizedContent: { $exists: false },
          })
          .skip(skip)
          .limit(batchSize)
          .toArray();

        for (const doc of documents) {
          const sanitizedContent = diacritics.remove(doc.content);
          bulkOps.push({
            updateOne: {
              filter: { _id: doc._id },
              update: { $set: { sanitizedContent } },
            },
          });
        }
      }

      if (bulkOps.length > 0) {
        await db.collection(collectionName).bulkWrite(bulkOps);
      }
    });

    // Execute all promises in parallel
    await Promise.all(promises);

    console.log("Collections sanitized successfully.");
  } catch (error) {
    console.error("Error during sanitization:", error);
  }
}

// Start the sanitization process when the server starts
sanitizeCollections();

// Endpoint to get collections
app.get("/collections", async (req, res) => {
  const db = client.db(MESSAGE_DATABASE);
  const collections = await db.listCollections().toArray();

  const collectionData = [];
  for (const collection of collections) {
    const count = await db.collection(collection.name).countDocuments();
    collectionData.push({
      name: collection.name,
      messageCount: count,
    });
  }

  // Sort collections by message count
  collectionData.sort((a, b) => b.messageCount - a.messageCount);

  logEndpointInfo(req, res, "GET /collections");
  res.status(200).json(collectionData);
});

// Endpoint to get collections sorted alphabetically
app.get("/collections/alphabetical", async (req, res) => {
  const db = client.db(MESSAGE_DATABASE);
  const collections = await db.listCollections().toArray();

  const collectionData = [];
  for (const collection of collections) {
    const count = await db.collection(collection.name).countDocuments();
    collectionData.push({
      name: collection.name,
      messageCount: count,
    });
  }

  // Sort collections alphabetically
  collectionData.sort((a, b) => a.name.localeCompare(b.name));

  logEndpointInfo(req, res, "GET /collections/alphabetical");
  res.status(200).json(collectionData);
});

// Endpoint to get messages by collection name

app.get("/messages/:collectionName", async (req, res) => {
  const collectionName = decodeURIComponent(req.params.collectionName);
  const fromDate = req.query.fromDate
    ? new Date(`${req.query.fromDate}T00:00:00Z`).getTime()
    : null;
  const toDate = req.query.toDate
    ? new Date(`${req.query.toDate}T23:59:59Z`).getTime()
    : null;
  const cacheKey = `messages-${collectionName}-${fromDate}-${toDate}`;
  const cachedData = cache.get(cacheKey);

  if (cachedData) {
    return res.status(200).json(cachedData);
  }
  console.log(`fromDate timestamp: ${fromDate}, toDate timestamp: ${toDate}`);
  const db = client.db(MESSAGE_DATABASE);
  const collection = db.collection(collectionName);

  const pipeline = [
    // Add the match stage to filter by date
    ...(fromDate !== null || toDate !== null
      ? [
          {
            $match: {
              ...(fromDate !== null && { timestamp_ms: { $gte: fromDate } }),
              ...(toDate !== null && { timestamp_ms: { $lte: toDate } }),
            },
          },
        ]
      : []),
    { $sort: { timestamp_ms: 1 } },
    {
      $project: {
        _id: 0,
        timestamp: 1,
        timestamp_ms: 1,
        sender_name: 1,
        content: 1,
        photos: 1,
      },
    },
  ];

  const messages = await collection.aggregate(pipeline).toArray();

  cache.set(cacheKey, messages);

  logEndpointInfo(req, res, `GET /messages/${req.params.collectionName}`);
  res.status(200).json(messages);
});

// Endpoint to upload messages
const normalizeAndSanitize = (str) => {
  return str
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, "");
};

app.post("/upload", upload.array("files"), async (req, res) => {
  const combinedJson = await combine_and_convert_json_files(
    req.files.map((file) => file.path)
  );
  const { participants, messages } = combinedJson;
  let collectionName = normalizeAndSanitize(participants[0].name);

  const db = client.db(MESSAGE_DATABASE);

  let index = 0;
  let originalCollectionName = collectionName;
  let collections;

  do {
    collections = await db.listCollections({ name: collectionName }).toArray();

    if (collections.length > 0) {
      index++;
      collectionName = `${originalCollectionName}_${index}`;
    }
  } while (collections.length > 0);

  const collection = db.collection(collectionName);
  await collection.insertMany(messages);

  logEndpointInfo(req, res, "POST /upload");
  res.status(200).json({
    message: `Messages uploaded to collection: ${collectionName}`,
    collectionName: collectionName,
    messageCount: messages.length,
  });
});

// Endpoint to delete a collection
app.delete("/delete/:collectionName", async (req, res) => {
  const collectionName = decodeURIComponent(req.params.collectionName);

  const db = client.db(MESSAGE_DATABASE);
  const collection = db.collection(collectionName);
  await collection.drop();

  logEndpointInfo(req, res, `DELETE /delete/${req.params.collectionName}`);
  res.status(200).json({
    message: `Collection "${collectionName}" deleted.`,
    collectionName: collectionName,
  });
  // After dropping the collection
  const cachedCollections = cache.get("collections") || [];
  const updatedCollections = cachedCollections.filter(
    (col) => col.name !== collectionName
  );
  cache.set("collections", updatedCollections);
});

// Endpoint to check if a photo is available for a collection
app.get("/messages/:collectionName/photo", async (req, res) => {
  const collectionName = decodeURIComponent(req.params.collectionName);
  const sanitizedCollectionName = sanitizeName(collectionName); // Sanitize the collection name

  const db = client.db(MESSAGE_DATABASE);
  const collection = db.collection(sanitizedCollectionName); // Use sanitized name for MongoDB collection
  const result = await collection.findOne({ photo: true });

  if (!result) {
    // logEndpointInfo(req, res, `GET /messages/${req.params.collectionName}/photo`);
    res.status(200).json({ isPhotoAvailable: false, photoUrl: null });
    console.log("Photo not found");
    return;
  }

  // Use sanitized name for photo URL
  const photoUrl = `https://${req.get(
    "host"
  )}/serve/photo/${sanitizedCollectionName}`;

  // logEndpointInfo(req, res, `GET /messages/${req.params.collectionName}/photo`);
  res.status(200).json({ isPhotoAvailable: true, photoUrl: photoUrl });
  console.log("Photo found");
  console.log(photoUrl);
});

// Endpoint to upload a photo for a collection
app.post(
  "/upload/photo/:collectionName",
  upload_photo.single("photo"),
  async (req, res) => {
    if (!req.file) {
      // logEndpointInfo(req, res, `POST /upload/photo/${req.params.collectionName}`);
      res.status(400).json({ message: "No photo provided" });
      return;
    }

    const sanitizedCollectionName = sanitizeName(
      decodeURIComponent(req.params.collectionName)
    );
    const db = client.db(MESSAGE_DATABASE);
    const collection = db.collection(sanitizedCollectionName);
    await collection.updateOne({}, { $set: { photo: true } }, { upsert: true });

    // logEndpointInfo(req, res, `POST /upload/photo/${req.params.collectionName}`);
    res.status(200).json({ message: "Photo uploaded successfully" });
  }
);

// Endpoint to serve a photo for a collection
app.get("/serve/photo/:collectionName", async (req, res) => {
  const sanitizedCollectionName = sanitizeName(
    decodeURIComponent(req.params.collectionName)
  );

  const photoDir = path.join(__dirname, "photos");
  const files = await fs.readdir(photoDir);

  const photoFile = files.find((file) =>
    file.startsWith(sanitizedCollectionName)
  );

  if (!photoFile) {
    // logEndpointInfo(req, res, `GET /serve/photo/${req.params.collectionName}`);
    res.status(404).json({ message: "Photo not found" });
    console.log("Photo not found");
    return;
  }

  const photoPath = path.join(photoDir, photoFile);
  // logEndpointInfo(req, res, `GET /serve/photo/${req.params.collectionName}`);
  res.sendFile(photoPath);
  console.log("Photo found");
});

// Endpoint to delete a photo for a collection
app.delete("/delete/photo/:collectionName", async (req, res) => {
  const sanitizedCollectionName = sanitizeName(
    decodeURIComponent(req.params.collectionName)
  );

  const photoDir = path.join(__dirname, "photos");
  const files = await fs.readdir(photoDir);
  const db = client.db(MESSAGE_DATABASE);
  const collection = db.collection(sanitizedCollectionName);
  const photoFile = files.find((file) =>
    file.startsWith(sanitizedCollectionName)
  );

  if (photoFile) {
    const photoPath = path.join(photoDir, photoFile);
    await fs.unlink(photoPath);
    await collection.updateOne(
      {},
      { $set: { photo: false } },
      { upsert: true }
    );
    res
      .status(200)
      .json({ message: "Photo deleted successfully and database updated" });
    return;
  } else {
    const doc = await collection.findOne({});
    if (doc && doc.photo === true) {
      await collection.updateOne(
        {},
        { $set: { photo: false } },
        { upsert: true }
      );
      res
        .status(200)
        .json({ message: "Photo not found, but database updated" });
      return;
    }
    res
      .status(404)
      .json({ message: "Photo not found and nothing to update in database" });
  }
});

// Serving static photos
app.use("/photos", express.static(path.join(__dirname, "photos")));
app.use("/inbox", express.static(path.join(__dirname, "inbox")));
// Endpoint to rename a collection
app.put("/rename/:currentCollectionName", async (req, res) => {
  const currentCollectionName = decodeURIComponent(
    req.params.currentCollectionName
  );
  const newCollectionName = req.body.newCollectionName.trim();

  if (!newCollectionName || !/^[a-zA-Z0-9_]+$/.test(newCollectionName)) {
    logEndpointInfo(
      req,
      res,
      `PUT /rename/${req.params.currentCollectionName}`
    );
    res.status(400).json({
      message: "Invalid collection name: Does not match naming convention",
    });
    return;
  }

  const db = client.db(MESSAGE_DATABASE);
  const currentCollection = db.collection(currentCollectionName);
  await currentCollection.rename(newCollectionName);

  logEndpointInfo(req, res, `PUT /rename/${req.params.currentCollectionName}`);
  res
    .status(200)
    .json({ message: `Collection renamed to ${newCollectionName}` });
  // After renaming the collection
  const count = await db.collection(newCollectionName).countDocuments();
  const cachedCollections = cache.get("collections") || [];
  const updatedCollections = cachedCollections.filter(
    (col) => col.name !== currentCollectionName
  );
  updatedCollections.push({
    name: newCollectionName,
    messageCount: count,
  });
  cache.set("collections", updatedCollections);
});

app.post("/search", express.json(), async (req, res) => {
  const query = req.body.query;
  const db = client.db(MESSAGE_DATABASE);

  try {
    // Fetch all collection names
    const collections = await db.listCollections().toArray();
    const collectionNames = collections.map((c) => c.name);

    // Construct the initial pipeline with $match and $addFields for the first collection
    const initialPipeline = [
      {
        $match: {
          sanitizedContent: {
            $regex: new RegExp(diacritics.remove(query), "i"),
          },
        },
      },
      {
        $addFields: {
          collectionName: collectionNames[0], // <-- Add the collection name here
        },
      },
    ];

    // Dynamically add $unionWith stages for the remaining collections
    const unionWithStages = collectionNames.slice(1).map((collectionName) => ({
      $unionWith: {
        coll: collectionName,
        pipeline: [
          {
            $match: {
              sanitizedContent: {
                $regex: new RegExp(diacritics.remove(query), "i"),
              },
            },
          },
          {
            $addFields: {
              collectionName: collectionName, // <-- Add the collection name here
            },
          },
        ],
      },
    }));

    const finalPipeline = initialPipeline.concat(unionWithStages);

    const potentialMatches = await db
      .collection(collectionNames[0])
      .aggregate(finalPipeline)
      .toArray();

    // Filter out sanitizedContent and convert to lowercase
    const actualMatches = potentialMatches.map((doc) => {
      const { sanitizedContent, ...rest } = doc;
      return { ...rest };
    });

    res.json(actualMatches);
  } catch (error) {
    console.error("Error during aggregation:", error);
    res
      .status(500)
      .json({ error: "An error occurred while performing the search." });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send("Something broke!");
});

// ----------------- STRESS TESTING ----------------- //
app.get("/load-cpu", (req, res) => {
  let total = 0;

  // Simulate CPU-intensive task
  for (let i = 0; i < 7000000; i++) {
    total += Math.sqrt(i) * Math.random();
  }

  res.send(`The result of the CPU intensive task is ${total}\n`);
});

app.get("/stress-test", async (req, res) => {
  try {
    const startTime = Date.now();

    // Generate a random czech word and sanitize it
    const randomWord = generate();

    const sanitizedRandomWord = sanitizeName(randomWord);

    // Trigger the cross-collection search
    const db = client.db(MESSAGE_DATABASE);

    // Fetch all collection names
    const collections = await db.listCollections().toArray();
    const collectionNames = collections.map(c => c.name);

    // Construct the initial pipeline with $match and $addFields for the first collection
    const initialPipeline = [
      {
        $match: {
          content: {
            $regex: new RegExp(sanitizedRandomWord, "i"),
          },
        },
      },
      {
        $addFields: {
          collectionName: collectionNames[0],
        },
      },
    ];

    // Dynamically add $unionWith stages for the remaining collections
    const unionWithStages = collectionNames.slice(1).map(collectionName => ({
      $unionWith: {
        coll: collectionName,
        pipeline: [
          {
            $match: {
              content: {
                $regex: new RegExp(sanitizedRandomWord, "i"),
              },
            },
          },
          {
            $addFields: {
              collectionName: collectionName,
            },
          },
        ],
      },
    }));

    const finalPipeline = initialPipeline.concat(unionWithStages);

    const potentialMatches = await db
      .collection(collectionNames[0])
      .aggregate(finalPipeline)
      .toArray();

    const endTime = Date.now();
    const duration = endTime - startTime;

    // Respond with the time taken to complete the stress test
    res.json({
      message: 'Stress test completed successfully',
      searchString: randomWord,
      duration: `${duration} ms`,
      searchMatches: potentialMatches.length,
    randomMatch: potentialMatches[Math.floor(Math.random() * potentialMatches.length)],
    data: potentialMatches
    });
  } catch (error) {
    console.error("Error during stress-test:", error);
    res.status(500).json({ error: "An error occurred during the stress test." });
  }
});

app.listen(port, () => {
  console.log(`Server listening on port number: ${port}`);
});

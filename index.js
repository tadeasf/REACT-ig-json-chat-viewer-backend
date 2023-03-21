/** @format */

const express = require("express");
const { MongoClient } = require("mongodb");
const cors = require("cors");
const app = express();
const port = process.env.PORT || 3000; // use Heroku-provided port or default to 3000
const multer = require("multer");
const fs = require("fs").promises;
const upload = multer({ dest: "uploads/" }).array("files");

app.use(
  cors({
    origin: [
      "https://kocouratko.cz",
      "http://localhost:5009",
      "http://193.86.152.148:5009",
      "http://193.86.152.148:3000",
      "http://localhost:3000",
    ],
  })
);

const uri = process.env.MONGODB_URI; // load uri from environment variable
const client = new MongoClient(uri, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

app.get("/collections", async (req, res) => {
  try {
    await client.connect();
    const db = client.db("messages");
    const collections = await db.listCollections().toArray();

    const collectionNames = collections
      .map((collection) => collection.name)
      .sort((a, b) => {
        // sort collections by name
        if (a < b) {
          return -1;
        }
        if (a > b) {
          return 1;
        }
        return 0;
      });
    console.log(collectionNames);
    res.status(200).json(collectionNames);
  } catch (error) {
    console.error(error);
    res.status(500).send("Error fetching collections");
  } finally {
    await client.close();
  }
});

app.get("/messages/:collectionName", async (req, res) => {
  const collectionName = req.params.collectionName;

  try {
    await client.connect();
    const db = client.db("messages");
    const collection = db.collection(collectionName);

    const messages = await collection
      .aggregate(
        [
          {
            $sort: {
              timestamp_ms: 1,
            },
          },
          {
            $addFields: {
              timestamp: {
                $toDate: "$timestamp_ms",
              },
            },
          },
        ],
        { allowDiskUse: true }
      )
      .toArray();
    res.status(200).json(messages);
  } catch (error) {
    console.error(error);
    res.status(500).send("Error querying messages");
  } finally {
    await client.close();
  }
});

app.post("/upload", upload, async (req, res) => {
  if (!req.files || req.files.length === 0) {
    res.status(400).send("No files provided");
    return;
  }

  let uploadResults = [];

  // Process each file in a loop
  for (const file of req.files) {
    let fileContent;

    try {
      fileContent = await fs.readFile(file.path, "utf-8");
    } catch (error) {
      console.error("Error reading file:", error);
      uploadResults.push({
        fileName: file.originalname,
        status: "Error reading file",
      });
      continue;
    }

    let jsonData;
    try {
      jsonData = JSON.parse(fileContent);
    } catch (error) {
      console.error("Error parsing JSON:", error);
      uploadResults.push({
        fileName: file.originalname,
        status: "Invalid JSON file",
      });
      continue;
    }

    const { participants, messages } = jsonData;
    if (!participants || !messages) {
      uploadResults.push({
        fileName: file.originalname,
        status: "Invalid JSON structure",
      });
      continue;
    }

    const collectionName = participants[0].name;

    try {
      await client.connect();
      const db = client.db("messages");
      const collection = db.collection(collectionName);

      await collection.insertMany(messages);
      uploadResults.push({
        fileName: file.originalname,
        status: `Messages uploaded to collection: ${collectionName}`,
      });
    } catch (error) {
      console.error(error);
      uploadResults.push({
        fileName: file.originalname,
        status: "Error uploading messages",
      });
    } finally {
      await client.close();
      // Delete the temporary file
      await fs.unlink(file.path);
    }
  }

  res.status(200).json(uploadResults);
});

app.delete("/delete/:collectionName", async (req, res) => {
  const collectionName = req.params.collectionName;

  try {
    await client.connect();
    const db = client.db("messages");
    const collection = db.collection(collectionName);

    await collection.drop();
    res.status(200).send(`Collection dropped: ${collectionName}`);
  } catch (error) {
    console.error(error);
    res.status(500).send("Error dropping collection");
  } finally {
    await client.close();
  }
});

app.listen(port, () => {
  console.log(`Server listening on port number: ${port}`);
});

/** @format */
require("dotenv").config();
const express = require("express");
const { MongoClient } = require("mongodb");
const cors = require("cors");
const app = express();
const port = process.env.PORT || 5555;
const multer = require("multer");
const fs = require("fs").promises;
const upload = multer({ dest: "uploads/" }).array("files");
const path = require("path");
const os = require("os");
const { combine_and_convert_json_files } = require("./json_combiner");

app.use(
  cors({
    origin: [
      "https://kocouratko.cz",
      "https://www.kocouratko.cz",
      "https://kocouratko.cz:5009",
      "https://www.kocouratko.cz:5009",
      "https://kocouratko.cz:3000",
      "https://www.kocouratko.cz:3000",
      "http://kocouratko.cz",
      "http://www.kocouratko.cz",
      "http://kocouratko.cz:5009",
      "http://www.kocouratko.cz:5009",
      "http://kocouratko.cz:3000",
      "http://www.kocouratko.cz:3000",
      "http://localhost:5009",
      "http://193.86.152.148:5009",
      "http://193.86.152.148:3000",
      "http://localhost:3000",
      "http://localhost:3001",
      "http://localhost:3335",
      "http://localhost:3336",
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
    res.status(500).json({ error: error });
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
    res.status(500).json({ error: error });
  } finally {
    await client.close();
  }
});

app.post("/upload", upload, async (req, res) => {
  if (!req.files || req.files.length === 0) {
    res.status(400).json({ message: "No files provided" });
    return;
  }

  try {
    // Combine, convert, and decode the JSON files
    const combinedJson = await combine_and_convert_json_files(
      req.files.map((file) => file.path)
    );

    const { participants, messages } = combinedJson;
    if (!participants || !messages) {
      res.status(400).json({ message: "Invalid JSON structure" });
      return;
    }

    const collectionName = participants[0].name;

    await client.connect();
    const db = client.db("messages");

    // Check if the collection already exists
    const collections = await db
      .listCollections({ name: collectionName })
      .toArray();
    if (collections.length > 0) {
      res.status(409).json({
        message: `A collection with the name "${collectionName}" already exists.`,
      });
      return;
    }

    const collection = db.collection(collectionName);
    await collection.insertMany(messages);

    res.status(200).json({
      message: `Messages uploaded to collection: ${collectionName}`,
      collectionName: collectionName,
      messageCount: messages.length,
    });
  } catch (error) {
    console.error(error);
    res
      .status(500)
      .json({ message: "Error uploading messages", error: error.message });
  } finally {
    await client.close();

    // Delete the temporary files
    for (const file of req.files) {
      await fs.unlink(file.path);
    }
  }
});

app.delete("/delete/:collectionName", async (req, res) => {
  const collectionName = req.params.collectionName;

  try {
    await client.connect();
    const db = client.db("messages");
    const collection = db.collection(collectionName);
    await collection.drop();
    res.status(200).json({
      message: `Collection "${collectionName}" deleted.`,
      collectionName: collectionName,
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: error.message });
  } finally {
    await client.close();
  }
});

app.get("/messages/:collectionName/photo", async (req, res) => {
  const collectionName = req.params.collectionName;

  try {
    await client.connect();
    const db = client.db("messages");
    const collection = db.collection(collectionName);

    const result = await collection
      .aggregate([
        {
          $match: { photo: { $exists: true } },
        },
        {
          $project: { _id: 0, photo: 1 },
        },
      ])
      .toArray();

    if (result.length === 0) {
      res.status(404).json({ message: "Photo not found" });
      return;
    }

    console.log(result[0].photo);

    // Return the photo
    res.status(200).json(result[0].photo);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: error.message });
  } finally {
    await client.close();
  }
});

app.listen(port, () => {
  console.log(`Server listening on port number: ${port}`);
});

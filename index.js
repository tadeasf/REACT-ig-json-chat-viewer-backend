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
  })
);

const uri = process.env.MONGODB_URI; // load uri from environment variable
const client = new MongoClient(uri, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, "photos/");
  },
  filename: function (req, file, cb) {
    const fileExtension = path.extname(file.originalname); // Get the file's original extension
    const sanitizedCollectionName = req.params.collectionName.replace(
      /\s+/g,
      ""
    ); // Remove spaces from collection name
    cb(null, `${sanitizedCollectionName}${fileExtension}`);
  },
});

const upload_photo = multer({ storage: storage });

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
    console.log("Messages sent");
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
    console.log("No files provided");
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
    console.log("Messages uploaded");
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
    console.log("Collection deleted");
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

    const result = await collection.findOne({ photo: true });

    if (!result) {
      res.status(200).json({ isPhotoAvailable: false, photoUrl: null });
      return;
    }

    // Return that a photo is available and its URL
    const photoUrl = `${req.protocol}://${req.get(
      "host"
    )}/serve/photo/${collectionName}`;
    res.status(200).json({ isPhotoAvailable: true, photoUrl: photoUrl });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: error.message });
  } finally {
    await client.close();
  }
});

app.post(
  "/upload/photo/:collectionName",
  upload_photo.single("photo"),
  async (req, res) => {
    if (!req.file) {
      res.status(400).json({ message: "No photo provided" });
      return;
    }

    try {
      await client.connect();
      const db = client.db("messages");
      const collection = db.collection(req.params.collectionName);

      // Update the collection to indicate that a photo exists
      await collection.updateOne(
        {},
        { $set: { photo: true } },
        { upsert: true }
      );

      res.status(200).json({ message: "Photo uploaded successfully" });
    } catch (error) {
      console.error(error);
      res.status(500).json({ error: error.message });
    } finally {
      await client.close();
    }
  }
);

app.get("/serve/photo/:collectionName", async (req, res) => {
  const collectionName = req.params.collectionName.replace(/\s+/g, ""); // Remove spaces from collection name
  const photoDir = path.join(__dirname, "photos");

  try {
    const files = await fs.readdir(photoDir);
    const photoFile = files.find((file) => file.startsWith(collectionName)); // Find the file that starts with the collection name

    if (!photoFile) {
      res.status(404).json({ message: "Photo not found" });
      return;
    }

    const photoPath = path.join(photoDir, photoFile);
    res.sendFile(photoPath);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(port, () => {
  console.log(`Server listening on port number: ${port}`);
});

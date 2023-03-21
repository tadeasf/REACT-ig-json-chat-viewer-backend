/** @format */

const express = require("express");
const { MongoClient } = require("mongodb");
const cors = require("cors");
const app = express();
const port = process.env.PORT || 3000; // use Heroku-provided port or default to 3000
const multer = require("multer");
const fs1 = require("fs").promises;
const fs2 = require("fs/promises");
const upload = multer({ dest: "uploads/" }).array("files");
const path = require("path");
const os = require("os");
const moment = require("moment");
const iconv = require("iconv-lite");

class FacebookIO {
  static async decodeFile(filePath) {
    const data = await fs2.readFile(filePath, "utf-8");
    let newData = "";
    let i = 0;
    while (i < data.length) {
      if (data.startsWith("\\u00", i)) {
        let newChar = "";
        while (data.startsWith("\\u00", i)) {
          const hex = parseInt(data.slice(i + 4, i + 6), 16);
          newChar += String.fromCharCode(hex);
          i += 6;
        }
        newData += newChar;
      } else {
        newData += data[i];
        i += 1;
      }
    }
    return newData;
  }
}

async function combine_and_convert_json_files(filePaths) {
  let combinedJson = {
    participants: [],
    messages: [],
    title: "",
    is_still_participant: true,
    thread_path: "",
    magic_words: [],
  };

  for (const filePath of filePaths) {
    const decodedFile = await FacebookIO.decodeFile(filePath);
    const data = JSON.parse(decodedFile);
    if (!combinedJson.participants.length) {
      combinedJson.participants = data.participants;
      combinedJson.title = data.title;
      combinedJson.is_still_participant = data.is_still_participant;
      combinedJson.thread_path = data.thread_path;
      combinedJson.magic_words = data.magic_words;
    }
    combinedJson.messages.push(...data.messages);
  }

  combinedJson.messages.forEach((message) => {
    if (message.timestamp_ms) {
      message.timestamp = moment(message.timestamp_ms).format(
        "HH:mm DD/MM/YYYY"
      );
    }
  });

  combinedJson.messages.sort((a, b) => {
    return moment(a.timestamp, "HH:mm DD/MM/YYYY").diff(
      moment(b.timestamp, "HH:mm DD/MM/YYYY")
    );
  });

  return combinedJson;
}

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

const fs1 = require("fs").promises;
const { FacebookIO } = require("./FacebookIO");
const { combine_and_convert_json_files } = require("./json_combiner");

app.post("/upload", upload, async (req, res) => {
  if (!req.files || req.files.length === 0) {
    res.status(400).json({ message: "No files provided" });
    return;
  }

  try {
    // Decode, combine, and convert the JSON files
    const decodedFilePaths = await Promise.all(
      req.files.map(async (file) => {
        const decodedContent = await FacebookIO.decodeFile(file.path);
        await fs1.writeFile(file.path, decodedContent);
        return file.path;
      })
    );

    const combinedJson = await combine_and_convert_json_files(decodedFilePaths);

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
      await fs1.unlink(file.path);
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

app.listen(port, () => {
  console.log(`Server listening on port number: ${port}`);
});

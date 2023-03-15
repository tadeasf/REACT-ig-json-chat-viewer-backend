/** @format */

const express = require("express");
const { MongoClient } = require("mongodb");
const cors = require("cors");
const app = express();
const port = process.env.PORT || 3000; // use Heroku-provided port or default to 3000

app.use(
  cors({
    origin: "https://kocouratko.cz",
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
      .aggregate([
        { $set: { timestamp_ms: { $toInt: "$timestamp_ms.$numberLong" } } },
        { $sort: { timestamp_ms: 1 } },
      ])
      .toArray();

    res.status(200).json(messages);
  } catch (error) {
    console.error(error);
    res.status(500).send("Error querying messages");
  } finally {
    await client.close();
  }
});

app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});

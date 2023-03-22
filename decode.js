/** @format */
const fs = require("fs").promises;
const path = require("path");
const iconv = require("iconv-lite");

class FacebookIO {
  static async decodeFile(filePath) {
    const data = await fs.readFile(filePath);

    // Replace all \u00hh JSON sequences with the byte the last two hex digits represent
    const binaryData = data
      .toString()
      .replace(/\\u00([0-9a-fA-F]{2})/g, (_, hex) => {
        return String.fromCharCode(parseInt(hex, 16));
      });

    // Convert the binary data from 'binary' encoding to 'utf-8' using iconv-lite
    const utf8Data = iconv.decode(Buffer.from(binaryData, "binary"), "utf-8");

    // Decode as JSON
    const decodedData = JSON.parse(utf8Data);

    return decodedData;
  }
}

async function main() {
  const inputPath = path.join(__dirname, "input.json");
  const outputPath = path.join(__dirname, "output.json");

  try {
    // Read and decode the input JSON
    const decodedJson = await FacebookIO.decodeFile(inputPath);

    // Dump the decoded JSON to output.json
    await fs.writeFile(
      outputPath,
      JSON.stringify(decodedJson, null, 2),
      "utf-8"
    );
    console.log("Decoded JSON written to output.json");
  } catch (error) {
    console.error("Error:", error);
  }
}

main();

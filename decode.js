/** @format */

const fs = require("fs").promises;
const iconv = require("iconv-lite");
const entities = require("entities");

class FacebookIO {
  static async decodeFile(filePath) {
    const data = await fs.readFile(filePath, "utf-8");
    const decodedData = entities.decodeHTML(data);
    return decodedData;
  }
}

async function main() {
  const inputFilePath =
    "/Users/tadeasfort/Documents/pythonJSprojects/gitHub/REACT-ig-json-chat-viewer-backend/input.json"; // Replace with the path to your input JSON file
  const outputFilePath =
    "/Users/tadeasfort/Documents/pythonJSprojects/gitHub/REACT-ig-json-chat-viewer-backend/output.json"; // Replace with the path to your output JSON file

  try {
    const decodedContent = await FacebookIO.decodeFile(inputFilePath);
    const jsonData = JSON.parse(decodedContent);
    await fs.writeFile(outputFilePath, JSON.stringify(jsonData, null, 2));
    console.log("Decoded JSON file saved as:", outputFilePath);
  } catch (error) {
    console.error("Error:", error.message);
  }
}

main();

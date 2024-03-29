/** @format */

const moment = require("moment");
const fs = require("fs");
const iconv = require("iconv-lite");

class FacebookIO {
  static async decodeFile(filePath) {
    const data = await fs.promises.readFile(filePath);

    // Replace all \u00hh JSON sequences with the byte the last two hex digits represent
    const binaryData = data
      .toString()
      .replace(/\\u00([0-9a-fA-F]{2})/g, (_, hex) => {
        return String.fromCharCode(parseInt(hex, 16));
      });

    // Convert the binary data from 'binary' encoding to 'utf-8' using iconv-lite
    let utf8Data = iconv.decode(Buffer.from(binaryData, "binary"), "utf-8");

    // Now it's safe to reassign utf8Data
    utf8Data = utf8Data.replace(/[\u0000-\u0019\u007F-\u009F]+/g, "");

    return utf8Data;
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

  try {
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
  } catch (error) {
    console.error("Error while combining JSON files: ", error);
  }
}

module.exports = {
  combine_and_convert_json_files,
};

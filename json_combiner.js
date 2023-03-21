/** @format */

const fs = require("fs/promises");
const moment = require("moment");
const iconv = require("iconv-lite");

class FacebookIO {
  static async decodeFile(filePath) {
    const data = await fs.readFile(filePath);
    const decodedData = iconv.decode(data, "utf-8");
    return decodedData;
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

module.exports = {
  combine_and_convert_json_files,
};

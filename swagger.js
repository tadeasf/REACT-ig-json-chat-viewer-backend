const swaggerAutogen = require("swagger-autogen")({ openapi: "3.0.0" });

const doc = {
  info: {
    version: "0.9.8",
    title: "Meta Messenger API",
    description:
      "API for my Meta chat history viewer: https://github.com/tadeasf/tauri-chat-viewer",
  },
  servers: [
    {
      url: "secondary.dev.tadeasfort.com",
      description:
        "main instance of the server run via pm2 in cluster mode for high availability",
    },
  ],
  tags: [
    // by default: empty Array
    {
      name: "meta",
      description: "Meta Messenger API",
    },
    {
      name: "messages",
      description: "Messages API",
    },
    {
      name: "conversations",
      description: "Conversations API",
    },
    {
      name: "users",
      description: "Users API",
    },
  ],
  components: {},
};

const outputFile = "./swagger-output.json";
const routes = ["index.js"];

swaggerAutogen(outputFile, routes, doc).then(() => {
  require("./index.js");
});

/** @format */

module.exports = {
  apps: [
    {
      name: "a-messenger-backend",
      script: "./index.js",
      instances: "1",
      env: {
        NODE_ENV: "production",
      },
    },
  ],
};

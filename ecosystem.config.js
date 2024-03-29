/** @format */

module.exports = {
  apps: [
    {
      name: "a-messenger-backend",
      script: "./index.js", // Replace with the path to your server file
      instances: "1", // This will use all available CPU cores
      env: {
        NODE_ENV: "production",
      },
    },
  ],
};

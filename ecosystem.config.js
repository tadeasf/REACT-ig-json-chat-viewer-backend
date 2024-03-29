/** @format */

module.exports = {
  apps: [
    {
      name: "a-messenger-backend",
      script: "./index.js",
      instances: "1",
      exec_mode: "fork",
      env: {
        NODE_ENV: "production",
      },
    },
  ],
};

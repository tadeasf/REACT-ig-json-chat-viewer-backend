/** @format */

module.exports = {
  apps: [
    {
      name: "a-messenger-backend",
      script: "./swagger.js",
      instances: "2",
      exec_mode: "cluster",
      env: {
        NODE_ENV: "production",
      },
    },
  ],
};

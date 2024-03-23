/** @format */

module.exports = {
  apps: [
    {
      name: "fb-cache-warmer",
      script: "./cacheWarmer.js", // Replace with the path to your server file
      instances: "1", // This will use all available CPU cores
      env: {
        NODE_ENV: "production",
      },
    },
  ],
};

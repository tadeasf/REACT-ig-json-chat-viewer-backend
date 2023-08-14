module.exports = {
    apps: [
      {
        name: "kocouratko-messenger-backend",
        script: "./index.js", // Replace with the path to your server file
        instances: "max", // This will use all available CPU cores
        exec_mode: "cluster",
        env: {
          NODE_ENV: "production",
        },
      },
    ],
  };
  
const swaggerAutogen = require('swagger-autogen')();

const outputFile = './swagger-fb-messenger-viewer-express.json';
const endpointsFiles = ['./index.js'];

swaggerAutogen(outputFile, endpointsFiles);
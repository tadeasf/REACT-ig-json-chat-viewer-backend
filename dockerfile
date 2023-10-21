# Use an official Node runtime as the base image
FROM node:14

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json to the container
COPY package*.json ./

# Install dependencies inside the container
RUN npm install

# Copy the entire project to the container
COPY . .

# Expose the port the app runs on
EXPOSE 5555

# Run the application
CMD ["npm", "start"]

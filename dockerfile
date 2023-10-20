# Use an official Node runtime as the base image
FROM node:14 AS build

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json to the container
COPY package*.json ./

# Install dependencies inside the container
RUN npm install

# Copy the entire project to the container
COPY . .

# Install Caddy
FROM caddy:2 AS caddy

# Final stage
FROM node:14

# Copy from build stage
COPY --from=build /usr/src/app /usr/src/app

# Copy Caddy binary from Caddy stage
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

# Set the working directory
WORKDIR /usr/src/app

# Copy Caddyfile
COPY Caddyfile /etc/caddy/Caddyfile

# Expose the port the app runs on
EXPOSE 5555

# Run Caddy and the application
CMD caddy run --config /etc/caddy/Caddyfile & npm start

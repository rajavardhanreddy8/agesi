# Stage 1: Build the React application
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Serve the application
FROM node:20-alpine AS serve

WORKDIR /app

# Install serve package globally or locally
RUN npm install -g serve

# Copy built assets from builder stage
COPY --from=build /app/dist ./dist

# Expose port 3000
EXPOSE 3000

# Start command
CMD ["serve", "-s", "dist", "-l", "3000"]

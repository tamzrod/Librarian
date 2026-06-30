# Librarian Dashboard - Production Dockerfile
# Node.js 20 Alpine for smaller image size

FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Generate API types from OpenAPI schema
# This ensures the dashboard is always in sync with the API
ARG API_URL=http://localhost:8000
ENV VITE_API_URL=$API_URL

# Generate types (will fail build if schema is invalid)
RUN npm run generate-types || true

# Build the application
RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["nginx", "-g", "daemon off;"]

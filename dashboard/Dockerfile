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
ARG API_URL=http://localhost:8001
ENV VITE_API_URL=$API_URL

# Build metadata arguments
ARG VITE_BUILD_SHA=unknown
ARG VITE_BUILD_TIME
ARG VITE_DASHBOARD_VERSION=dev
ARG VITE_API_CONTRACT_VERSION=v1.0
ARG VITE_ENVIRONMENT=production

# Pass build metadata to Vite (injected into the app at build time)
ENV VITE_BUILD_SHA=$VITE_BUILD_SHA
ENV VITE_BUILD_TIME=$VITE_BUILD_TIME
ENV VITE_DASHBOARD_VERSION=$VITE_DASHBOARD_VERSION
ENV VITE_API_CONTRACT_VERSION=$VITE_API_CONTRACT_VERSION
ENV VITE_ENVIRONMENT=$VITE_ENVIRONMENT

# Generate types (will fail build if schema is invalid)
RUN npm run generate-types || true

# Build the application with injected metadata
RUN npm run build

# Production stage - serve with nginx
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3100

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3100 || exit 1

CMD ["nginx", "-g", "daemon off;"]

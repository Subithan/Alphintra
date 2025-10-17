# Optimized multi-stage build for Next.js application
# This Dockerfile is optimized for Cloud Build with Node.js dependency caching
# It expects node_modules to be already available from the build process

# Base stage with system dependencies
FROM node:20-alpine AS base
# Add compatibility for native deps (e.g., sharp for Next.js images)
RUN apk add --no-cache libc6-compat

# Dependencies stage - optimized for Cloud Build
FROM base AS deps
WORKDIR /app

# Assume node_modules is already built and available from Cloud Build
# Copy package files for layer caching benefits
COPY package.json package-lock.json* ./

# Copy pre-built node_modules if available (from Cloud Build cache)
COPY node_modules ./node_modules

# Verify installation integrity and fix if needed
RUN npm ls --silent >/dev/null 2>&1 || \
    (echo "Reinstalling missing dependencies..." && npm ci --prefer-offline --no-audit --no-fund)

# Clean up npm cache to reduce image size
RUN npm cache clean --force

# Build stage with optimized layer caching
FROM base AS builder
WORKDIR /app

# Copy dependencies with layer caching optimization
COPY --from=deps /app/node_modules ./node_modules
COPY package.json package-lock.json* ./

# ========================================================================
# ===               THIS IS THE CORRECTED SECTION                      ===
# ========================================================================
# Copy the rest of the application source code.
# The '.' copies everything from the build context (respecting .dockerignore)
# into the current WORKDIR (/app). This includes your 'app', 'public',
# 'components' directories, and all config files.
COPY . .
# ========================================================================

# Set build-time environment variables for optimized builds
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
ENV SKIP_ENV_VALIDATION=1
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Build the application with optimizations
RUN npm run build

# Production stage - minimal and secure
FROM base AS production
WORKDIR /app

# Install only runtime dependencies
RUN apk add --no-cache \
    curl \
    && rm -rf /var/cache/apk/*

# Production environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application with optimized layer ordering
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Set proper permissions
USER nextjs

# Expose port
EXPOSE 3000

# Health check with optimized timing
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Start the application
CMD ["node", "server.js"]

# Development stage (unchanged for local development)
FROM base AS development
WORKDIR /app

# Install all dependencies including dev dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY . .

# Set development environment
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# Expose port
EXPOSE 3000

# Start application
CMD ["npm", "start"]
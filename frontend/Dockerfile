FROM node:20-alpine AS build

WORKDIR /app

# Build arguments passed from GitHub Actions
ARG NEXT_API_URL
ARG NEXT_PUBLIC_POSTHOG_KEY
ARG NEXT_PUBLIC_POSTHOG_HOST

# Expose them as ENV for NEXT
ENV NEXT_API_URL=$NEXT_API_URL
ENV NEXT_PUBLIC_POSTHOG_KEY=$NEXT_PUBLIC_POSTHOG_KEY
ENV NEXT_PUBLIC_POSTHOG_HOST=$NEXT_PUBLIC_POSTHOG_HOST

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- NGINX STAGE ----

FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Copy nginx.conf from within this folder only
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf
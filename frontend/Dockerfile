FROM node:20-alpine AS build

WORKDIR /app
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
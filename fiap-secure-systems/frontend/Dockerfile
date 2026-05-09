# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS build
WORKDIR /workspace
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_GATEWAY_BASE_URL=http://localhost:8080
ARG VITE_GATEWAY_WS_URL=ws://localhost:8080
ENV VITE_GATEWAY_BASE_URL=$VITE_GATEWAY_BASE_URL
ENV VITE_GATEWAY_WS_URL=$VITE_GATEWAY_WS_URL
RUN npm run build

FROM nginx:1.27-alpine
RUN apk add --no-cache curl
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /workspace/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=5s --timeout=3s --retries=20 --start-period=10s \
  CMD curl -fs http://localhost/ || exit 1

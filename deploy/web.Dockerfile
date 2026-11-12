FROM node:22-bookworm-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci
COPY apps/web apps/web
COPY apps/extension apps/extension
COPY apps/browser/vendor apps/browser/vendor
COPY scripts/package_extension.py scripts/package_extension.py
ENV NEXT_PUBLIC_API_URL=/api NEXT_TELEMETRY_DISABLED=1
RUN npm run build --workspace @omnisight/web -- --webpack
FROM nginxinc/nginx-unprivileged:1.28-alpine
COPY --from=build /app/apps/web/out /usr/share/nginx/html
EXPOSE 8080

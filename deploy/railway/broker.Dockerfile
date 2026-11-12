FROM node:22-bookworm-slim
ENV NODE_ENV=production
WORKDIR /broker
COPY apps/browser-broker/package.json apps/browser-broker/package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts
COPY apps/browser-broker/src ./src
COPY --chown=node:node apps/browser ./omnisight-browser
USER node
EXPOSE 9000
CMD ["npm", "start"]

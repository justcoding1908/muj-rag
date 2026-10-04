# Build stage: compile the Vite/React app to static files.
FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Baked in at build time, not runtime — Vite replaces import.meta.env.VITE_API_URL
# with this literal value when it builds the static JS bundle. Pass the real backend
# URL as a Railway build-time variable (not a regular env var) for this to take effect.
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Serve stage: a tiny static file server for the built output.
FROM node:22-slim
WORKDIR /app
RUN npm install -g serve@14
COPY --from=build /app/dist ./dist
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "serve -s dist -l ${PORT}"]

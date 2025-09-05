FROM node:18-alpine

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend .

EXPOSE 5173

# Ensure Vite binds to 0.0.0.0 for container access
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]


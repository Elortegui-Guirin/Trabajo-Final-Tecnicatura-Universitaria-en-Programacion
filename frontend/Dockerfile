# GeoForraje Frontend - Dockerfile desarrollo
FROM node:20-alpine

WORKDIR /app

# Instalar dependencias del sistema para node-gyp si needed
RUN apk add --no-cache python3 make g++

# Copiar package files
COPY package*.json ./

# Instalar dependencias
RUN npm ci

# Copiar código
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
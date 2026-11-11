# GeoForraje Frontend - Dockerfile desarrollo
FROM node:20-alpine

WORKDIR /app

# Instalar dependencias del sistema para node-gyp si needed
RUN apk add --no-cache python3 make g++

# Copiar package files
COPY package*.json ./

# Instalar dependencias
# No hay package-lock.json en el repo: npm ci fallaría. Usar npm install.
RUN npm install

# Copiar código
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
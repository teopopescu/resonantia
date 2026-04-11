FROM node:20-alpine

WORKDIR /app

# Copy dependency files first for layer caching
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

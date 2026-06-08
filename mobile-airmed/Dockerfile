FROM node:20-alpine

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN corepack enable && corepack prepare pnpm@latest --activate && pnpm install

COPY . .

EXPOSE 8081

CMD ["pnpm", "run", "start"]

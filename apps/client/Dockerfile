# dev
FROM docker.io/node:22.20.0-slim AS dev

WORKDIR /app
RUN npm install --ignore-scripts --location=global pnpm@10.17.1
COPY ./package.json ./
RUN pnpm install --ignore-scripts
COPY . .
CMD ["pnpm", "run", "dev"]


# build
FROM dev AS build

RUN pnpm run build


# prod
FROM docker.io/nginxinc/nginx-unprivileged:1.28.0-alpine AS prod

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/50x.html /usr/share/nginx/html
COPY nginx/40x.html /usr/share/nginx/html
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]

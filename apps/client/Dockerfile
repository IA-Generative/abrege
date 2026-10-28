# dev
FROM docker.io/node:24.22.1-slim AS dev

RUN npm install --ignore-scripts --location=global pnpm@10.17.1

WORKDIR /app
# Single, non-recursive chown of the empty directory: switching to `node` before
# installing anything means node_modules and the copied source are owned by `node`
# from the moment they're created, instead of a slow `chown -R` afterwards.
RUN chown node:node /app

USER node

COPY --chown=node:node ./package.json ./
RUN pnpm install --ignore-scripts
COPY --chown=node:node . .
CMD ["pnpm", "run", "dev"]


# build
FROM dev AS build

RUN pnpm run build


# prod
FROM docker.io/nginxinc/nginx-unprivileged:1.28.0-alpine AS prod

# The base image's CA bundle still trusts the eMudhra emSign ECC Root CA - G3, whose
# intermediates have publicly recoverable private keys. Alpine's ca-certificates
# 20261020-r0 removes it; both packages are upgraded because the `ca-certificates` trigger
# regenerates the bundle from its own copy. `USER 101` restores the numeric user the base
# image ends on.
USER root
RUN apk upgrade --no-cache ca-certificates ca-certificates-bundle
USER 101

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/50x.html /usr/share/nginx/html
COPY nginx/40x.html /usr/share/nginx/html
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf

# Deliberately no `USER` here. nginx-unprivileged already ends on `USER 101`, and the
# numeric form is what `runAsNonRoot: true` needs to verify - re-declaring it as `USER
# nginx` would replace a verifiable user with an unverifiable name. The base image also
# already owns /var/cache/nginx and /etc/nginx by group root for arbitrary UIDs, and
# these assets are only ever read, never written.

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]

# Stage 1: build do Vue com Vite
FROM node:20-alpine AS builder

WORKDIR /app

# Atualiza ca-certificates no build para garantir TLS seguro ao baixar pacotes npm
RUN apk update && apk add --no-cache ca-certificates && update-ca-certificates

COPY package*.json .
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline

COPY . .
RUN npm run build

# Stage 2: serve estático com nginx
FROM nginx:alpine

# Atualiza certificados e pacotes básicos da imagem Nginx
RUN apk update && apk add --no-cache ca-certificates && update-ca-certificates

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Permite que o nginx rode sem root ajustando permissões de logs e cache
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /usr/share/nginx/html

USER nginx

EXPOSE 80
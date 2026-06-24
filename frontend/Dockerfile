FROM node:26-alpine@sha256:a2dc166a387cc6ca1e62d0c8e265e49ca985d6e60abc9fe6e6c3d6ce8e63f606 AS builder

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app
COPY --chown=app:app package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY --chown=app:app . .
RUN npm run build
RUN npm cache clean --force

FROM nginx:1.31-alpine@sha256:54f2a904c251d5a34adf545a72d32515a15e08418dae0266e23be2e18c66fefa AS runner

RUN addgroup --system app && adduser --system --ingroup app app

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
RUN chown -R app:app /usr/share/nginx/html /var/cache/nginx /var/log/nginx

USER app

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

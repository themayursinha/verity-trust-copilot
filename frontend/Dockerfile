FROM node:26-alpine AS builder

RUN addgroup --system app && adduser --system --ingroup app app

WORKDIR /app
COPY --chown=app:app package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY --chown=app:app . .
RUN npm run build
RUN npm cache clean --force

FROM nginx:1.31-alpine AS runner

RUN addgroup --system app && adduser --system --ingroup app app

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
RUN chown -R app:app /usr/share/nginx/html /var/cache/nginx /var/log/nginx

USER app

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

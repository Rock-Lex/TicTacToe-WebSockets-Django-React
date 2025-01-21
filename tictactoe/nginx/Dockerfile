FROM nginx:1.25

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d

COPY ssl /home/app/web/ssl
RUN chmod -R 755 /home/app/web/ssl
# Use official NGINX image
FROM nginx:alpine

# Remove default config and add custom reverse proxy config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy your static frontend files
COPY index.html /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/


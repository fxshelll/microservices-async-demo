FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY src ./src
ENV PORT=3002
EXPOSE 3002
CMD ["npm", "start"]
COPY wait-for-rabbit.sh /wait-for-rabbit.sh
RUN chmod +x /wait-for-rabbit.sh
ENTRYPOINT ["/wait-for-rabbit.sh"]
CMD ["npm", "start"]

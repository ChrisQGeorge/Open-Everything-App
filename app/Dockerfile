FROM node:latest
WORKDIR /app
COPY . /app
RUN npm install
RUN npm run build
RUN npx next telemetry disable
EXPOSE 3000
CMD ["npm", "start"]
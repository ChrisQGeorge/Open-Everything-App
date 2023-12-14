# Open-Everything-App
A quantified self data aggregator, analyzer, and dashboard that is open source and self-hostable.
Currently WIP

# Running
To run the application, clone the git repository and run the following command

```
docker-compose up -d
```
The app is hosted at locahost:3000

From there, follow the prompts and create a root password (NOTE: You will need this password if the API restarts. Please save it or you will lose your data!)
After that, register an account and log in.

# Development

## Front End
For development of the front end, ensure you have node.js and npm installed. 
Next, run the appication as described above
After this, stop the "web" container and cd into the "app" directory.
From there running "npm run dev" will start the front end locally and will update as you save your files

## Back End
For back end development, first run the application using Docker.
At this point, make whatever changes you like and then save
To run the application with your changes, use the command ```docker-compose up -d --build --force-recreate api```
From here, type in your selected root password and login

You can also directly access the API by adding 
```
ports:
  - "5000:5000"
```
to the docker-compose.yml api container. Fom there, you can directly test the API by going to locahost:5000/docs

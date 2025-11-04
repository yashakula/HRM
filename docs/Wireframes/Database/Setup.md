# Postgresql database setup
This document describes how you can use a containerized postgres database with your local application for development

## Steps to follow

1. Pull the official Postgres docker image and run it

``` 
docker run --name my_postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -p 5432:5432 \
  -d postgres
```
- --name my_postgres assigns a name to the container.

- -e POSTGRES_PASSWORD=mysecretpassword sets the password for the default postgres user.

- -p 5432:5432 maps port 5432 of the container to port 5432 on your host machine.

- -d postgres runs the container in detached mode using the official PostgreSQL image.

2. Open the psql cli to interact with the databse 

```
docker exec -it my_postgres psql -U postgres
```
 
3. Verify the Connection:

Once connected, you can run SQL commands. For example, to list all databases:​ `\l`

To exit the psql session:​ `\q`

4. Do Stuff

- `create database hrms;` to create a database
- `\c hrms` to switch to the created database 

# Calculator API

## Overview

This is a RESTful API built using FastAPI, PostgreSQL, and Docker. It provides a simple calculator service that allows users to perform basic arithmetic operations.

## Features

* Perform addition, subtraction, multiplication, and division operations
* API documentation available at `/docs`
* CORS enabled for cross-origin requests

## Requirements

* Python 3.8+
* PostgreSQL 12+
* Docker 20+

## Running the API

1. Clone the repository
2. Create a PostgreSQL database with the following credentials:
	* User: `user`
	* Password: `password`
	* Database: `db`
	* Host: `localhost`
	* Port: `5432`
3. Build the Docker image: `docker build -t calculator-api .`
4. Run the Docker container: `docker run -p 8000:8000 calculator-api`
5. Access the API at `http://localhost:8000/docs`

## Testing the API

1. Install the required dependencies: `pip install -r requirements.txt`
2. Run the tests: `pytest`
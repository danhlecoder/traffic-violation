MongoDB API Service
===================

REST API gateway for MongoDB operations.

Deploy:
-------
./deploy-mongo.sh

Endpoints:
----------
GET  /health                    - Health check
GET  /cameras                   - List cameras
GET  /cameras/{id}              - Get camera
POST /cameras                   - Create camera
GET  /violations                - List violations
POST /violations                - Create violation

Port: 8002

Config:
-------
Environment variables:
  MONGO_HOST=mongo (hoặc IP server MongoDB)
  MONGO_PORT=27017
  MONGO_DATABASE=traffic

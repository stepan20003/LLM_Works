#!/bin/bash

# Connect to database
psql -U task_management_api_user -d task_management_api -f db/schema.sql
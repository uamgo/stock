#!/bin/sh
sudo supervisorctl update 
sudo supervisorctl stop all
sudo supervisorctl restart all

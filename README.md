# Udacity FSND Project 3 - Item Catalog

## Overview
Udacity FSND Project 3 - Item Catalog. This project allows for a list of items to be stored within varieties and subcategories. This project replicates the functionality of a classified site, or a department store. Visitors can login through the Google+ OAuth API.

## Features
- Google+ Authentication
- Registered users can create, read, update and delete products/ads and subcategories 
- Users can only edit and delete their own posts
- Registered users can upload and edit images 

## Installation
* You will need to install the pre-configured Vagrant VM for the Full Stack Foundations Course from Udacity. For instructions on how to do this, visit [https://www.udacity.com/wiki/ud088-nd/vagrant]
(https://www.udacity.com/wiki/ud088-nd/vagrant)

## Requirements
- [Flask](http://flask.pocoo.org/)
- [SQLAlechemy](http://docs.sqlalchemy.org/en/rel_0_8/) 
- [oauth2client](https://github.com/google/oauth2client) 

## Usage
To reset the database:

- Run python database_setup.py. *Note: rm catalog.db before this command. 
- Run products.py to populate the database

To run the project:

- start the Vagrant VM
- Run python project.py from the Vagrant machine
- Visit http://localhost:5000/
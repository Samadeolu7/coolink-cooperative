from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import models
import app as main_app
from queries import Queries  # Replace 'your_module' with the actual module where your Queries class is defined

# Create a SQLAlchemy database instance


def create_app():
    
    db = models.db
    app = models.app
    # Create an instance of the Queries class
    query = main_app.query

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)

    # Register blueprints, middleware, and other components as needed
    context ={
        "query": query,
        "login_manager": login_manager,
        "app": app,
        "db": db,
        }
    return context

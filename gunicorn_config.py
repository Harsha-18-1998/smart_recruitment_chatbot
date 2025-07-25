# gunicorn_config.py

workers = 5   
workers_class = "eventlet" # Use eventlet worker class to support Flask-SocketIO     
bind = "0.0.0.0:" + os.environ.get("PORT", "10000")    # Bind to the port Render provides 
timeout = 180  
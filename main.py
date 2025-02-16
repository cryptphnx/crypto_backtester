# main.py
from dashboard import app

# Expose the underlying Flask server (the WSGI callable)
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)

from flask import Flask

# Create a Flask web server
app = Flask(__name__)

# Define a route for the root URL
@app.route('/')
def hello_world():
    return 'Hello, World!, This is Vechalapu Rajendra Simhadri Appala Naidu'

# Run the application if executed as the main script
if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask

# Create a Flask web server
app = Flask(__name__)

# Define a route for the root URL
@app.route('/')
def hello_world():
    return 'ఓం నమో విఘ్నేశ్వరాయ నమః'

# Run the application if executed as the main script
if __name__ == '__main__':
    app.run(debug=True)

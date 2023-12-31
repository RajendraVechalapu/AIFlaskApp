at deployment 
#gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

Test and Demo
#fastapi
#uvicorn main:app --host 127.0.0.1 --port 8000 --reload

#Terminal
python -m venv rajenv
.\rajenv\Scripts\activate
pip freeze > requirements.txt

#pip install streamlit
#pip install -r requirements.txt

#pip install spacy
#python -m spacy download en_core_web_sm


#streamlit run calculator_app.py

#to uninstall all pip from system
pip freeze | ForEach-Object { pip uninstall -y $_.split('==')[0] }

Create a virtual environment to deploy in Azure

In the same directory run the following commands to create a virtual environment to be able to integrate with Azure:

python3 -m venv venv
venv\Scripts\Activate or
$ source venv/bin/activate
$ pip install -r requirements.txt
$ export FLASK_APP=app.py   or in windows $env:FLASK_APP = "app.py"
$ flask run

$env:FLASK_APP = "app.py"
flask run
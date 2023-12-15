Test and Demo

#Terminal
python -m venv venv
.\venv\Scripts\activate
pip install streamlit
pip install -r requirements.txt

pip install spacy
python -m spacy download en_core_web_sm


streamlit run calculator_app.py

#to uninstall all pip from system
pip freeze | ForEach-Object { pip uninstall -y $_.split('==')[0] }


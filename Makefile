streamlit run  ./main.py
python scraper/getproperties.py
python logo_scraper/logos.py


docker build -f ./Dockerfile -t lizproject:latest .
docker run -p 8501:8501 lizproject:latest


setup a python virtual env
pip install virtualenv
python3.11 -m venv .purple

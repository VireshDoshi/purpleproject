FROM python:3.11

# Expose port you want your app on
EXPOSE 8501

# Upgrade pip and install requirements
COPY requirements.txt requirements.txt
RUN pip install -U pip
RUN pip install -r requirements.txt

# Copy app code and set working directory
COPY . ./app
WORKDIR /app

# Run
ENTRYPOINT ["streamlit", "run", "/app/main.py"]

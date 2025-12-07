FROM ubuntu:latest

WORKDIR /src

COPY install_system_requirements.sh .
RUN bash ./install_system_requirements.sh

RUN pip --version

COPY requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["./start.sh"]

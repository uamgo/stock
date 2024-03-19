FROM python:3
RUN mkdir -p /app
WORKDIR /app
RUN echo 'alias ll="ls -ltr" >> ~/.bashrc'
RUN git clone https://github.com/uamgo/stock.git
RUN pip3 install akshare
CMD sleep 360000


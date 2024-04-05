FROM python:3
RUN mkdir -p /app
WORKDIR /app
RUN echo 'alias ll="ls -ltr" >> ~/.bashrc'
RUN git clone https://github.com/uamgo/stock.git
WORKDIR /app/stock
RUN pip3 install akshare --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip3 install exchange_calendars
#apt-get源 使用163的源
RUN touch /etc/apt/sources.list
RUN mv /etc/apt/sources.list /etc/apt/sources.list.bak && \
    echo "deb http://mirrors.163.com/debian/ jessie main non-free contrib" >/etc/apt/sources.list && \
    echo "deb http://mirrors.163.com/debian/ jessie-proposed-updates main non-free contrib" >>/etc/apt/sources.list && \
    echo "deb-src http://mirrors.163.com/debian/ jessie main non-free contrib" >>/etc/apt/sources.list && \
    echo "deb-src http://mirrors.163.com/debian/ jessie-proposed-updates main non-free contrib" >>/etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y vim
CMD sleep 360000


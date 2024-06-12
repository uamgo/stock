FROM bitnami/git:2.45.2 as git_repo
WORKDIR /app
RUN git clone https://github.com/uamgo/stock.git stock
ADD "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache
RUN git pull -r origin main

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY --from=git_repo /app/stock /app

RUN pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple
RUN pip3 config set install.trusted-host mirrors.aliyun.com
# Install any needed packages specified in requirements.txt
RUN pip3 install -r requirements.txt

# Make port 5070 available to the world outside this container
EXPOSE 5070

# Define environment variable
#ENV NAME World

# Run app.py when the container launches
CMD ["python", "stock_ui.py"]

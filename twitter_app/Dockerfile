FROM ubuntu:latest

RUN apt-get update -y; apt-get upgrade -y
RUN apt-get install wget xz-utils -y
RUN mkdir development
WORKDIR development
RUN wget https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_2.2.1-stable.tar.xz -P .
RUN tar xf flutter_linux_2.2.1-stable.tar.xz
RUN echo "export PATH=\"$PATH:`pwd`/flutter/bin\"" >> ~/.bashrc
RUN export PATH="$PATH:`pwd`/flutter/bin"
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get install git cmake ninja-build clang pkg-config build-essential libgtk-3-dev -y
RUN apt-get install curl unzip
#RUN source ~/.bashrc
#RUN flutter config --enable-linux-desktop

WORKDIR /
RUN mkdir /app
COPY . /app
WORKDIR /app
#ENTRYPOINT ['flutter upgrade; flutter config --enable-linux-desktop']

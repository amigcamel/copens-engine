FROM python:2.7.14 
RUN apt-get update && apt-get install -y wget
RUN wget https://nchc.dl.sourceforge.net/project/cwb/cwb/cwb-3.0.0/cwb-3.0.0-linux-x86_64.tar.gz &&\
    tar xvfz cwb-3.0.0-linux-x86_64.tar.gz &&\
    cd cwb-3.0.0-linux-x86_64 &&\
    ./install-cwb.sh
RUN mkdir -p /usr/local/share/cwb/registry
ADD . /copens-engine

ARG VARIANT=ubuntu-22.04
FROM mcr.microsoft.com/vscode/devcontainers/base:0-${VARIANT}

# Base utilities
USER root
RUN apt-get update
RUN apt-get install -y python3-pip
RUN apt install -y python3.10-venv

# Git large file system
RUN apt install git-lfs

# Poetry
USER root
RUN python3 -m venv /opt/poetry
RUN /opt/poetry/bin/pip install -U pip setuptools
RUN /opt/poetry/bin/pip install poetry
RUN /opt/poetry/bin/poetry completions bash >> ~/.bash_completion
USER vscode
RUN echo 'alias poetry=/opt/poetry/bin/poetry' >> ~/.bashrc

# Python 3.11
USER root
RUN apt install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt install -y python3.11
RUN apt install -y python3.11-venv
RUN apt install -y python3.11-distutils

# Gurobi
USER root
WORKDIR /opt/gurobi
RUN wget https://packages.gurobi.com/11.0/gurobi11.0.1_linux64.tar.gz
RUN tar -xzvf gurobi11.0.1_linux64.tar.gz
RUN rm gurobi11.0.1_linux64.tar.gz
RUN touch /opt/gurobi/gurobi1101/gurobi.lic
# Gurobi licensing and installation is done by running gurobi-lic.sh as su

# GLPK
RUN apt-get install -y glpk-utils

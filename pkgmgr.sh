#!/usr/bin/bash

# Creastes the environment and installs all dependencies
build() {
    clean 

    python -m venv .venv

    source .venv/Scripts/activate

    pip install pipenv
    pipenv install
}

# Cleans the project directory of unnecessary files
clean() {
    if [ -d ./.venv ]; 
    then
        deactivate
        rm -rf ./.venv
    fi
}

# Cleans and then builds the project
rebuild() {
    clean
    build
}

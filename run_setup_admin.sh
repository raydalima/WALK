#!/bin/bash
PYTHON=python3

# Opcional: caminho absoluto para python se necessário
# PYTHON=/Library/Frameworks/Python.framework/Versions/3.11/bin/python3

$PYTHON manage.py setup_admin --username admin --email admin@walk.com --password 'WALK123@'

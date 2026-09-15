#!/bin/bash

cd /root/ai-daily

source /root/.config/ai-daily.env

python3 fetch.py
python3 select.py
python3 generate.py

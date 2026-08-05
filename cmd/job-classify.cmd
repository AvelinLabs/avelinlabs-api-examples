@echo off
setlocal
if "%BASE_URL%"=="" set "BASE_URL=https://api.avelinlabs.com"
py -3 python\job_classify.py

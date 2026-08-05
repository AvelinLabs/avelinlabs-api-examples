@echo off
setlocal
if "%BASE_URL%"=="" set "BASE_URL=https://api.avelinlabs.com"
py -3 python\market_technologies_trending.py

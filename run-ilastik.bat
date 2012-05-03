@echo off
set PYTHONPATH=%cd%
set PATH=%cd%\dlls;%PATH%
.\Scripts\python.exe ilastik\ilastikMain.py
sleep 3
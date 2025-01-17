@echo off
REM Activate the virtual environment
cd "C:\Users\Nitin\Desktop\straddle chart\iv_chart"
call Scripts\activate

REM Run the Python script
cd "C:\Users\Nitin\Desktop\straddle chart\straddle_chart_v2"
python "Fina code.py"

REM Deactivate the virtual environment
deactivate

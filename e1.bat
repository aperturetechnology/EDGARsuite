del /q "%~2FilingSummary.xml"
del /q "%~2$F"
del /q "%~4"
"%~1python\python.exe" "%~1ere\arelleCmdLine.py" --plugins "%~1ere\arelle\plugin\EdgarRenderer" -f "%~2%~3" --disclosureSystem efm-extended-pragmatic-all-years --logFile "%~4"
ren "%~2Reports\FilingSummary.xml" $F
move /Y "%~2Reports\*.*" "%~2"
rd /s /q "%~2Reports"
ren "%~2$F" FilingSummary.xml

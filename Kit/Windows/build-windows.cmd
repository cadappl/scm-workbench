setlocal
call build-app.cmd
    if errorlevel 1 goto :error
call build-kit.cmd %1
    if errorlevel 1 goto :error
goto :eof
:error
    echo Error: Build failed
endlocal

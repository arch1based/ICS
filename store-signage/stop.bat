@echo off
wmic process where "CommandLine like '%%ICS-Signage%%'" call terminate >nul 2>nul
wmic process where "CommandLine like '%%server.py%%'" call terminate >nul 2>nul

#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# ===========================================================================================
# Description: Program to check status of remote servers using SSH for troubleshooting
# Author: Zeljko Milinovic, MSc
#
# Parameters: param[0] text   - Hostname or IP
#             param[1] text   - Password
# USAGE:
# python3 program.py 1.1.1.1 password
#
# !!!Important the program need the Paramiko Library and Python Version 3 to be installed on the local PC
# !!!Instruction on how to install the PARAMIKO Library
#   http://www.paramiko.org/installing.html
# !!! THE PARAMIKO SCRIPT CAN BE EASILY INSTALLED ON A WINDOWS PC WITH PYTHON §
# !!! 1. THE COMMAND PROMPT IN WINDOWS START WITH ADMIN RIGHTS
# !!! 2. TYPE IN TO CMD INSTALL: pip install paramiko
#############################################################################################
import atexit
import paramiko
import sys

if len(sys.argv) < 2:
    print("args missing")
    sys.exit(1)

hostname = sys.argv[1]
password = sys.argv[2]
# user = sys.argv[3]
username = "root"

# Check Vendor
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port=22, username=username, password=password)
stdin, stdout, stderr = client.exec_command("dmidecode | egrep Vendor | awk '{print $2}'")
vendor = stdout.read().decode('utf-8')
vendor = vendor.strip('\n')
client.close()


# finish check vendor

class myssh:

    def __init__(self, hostname, username, password, port=22):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, port=port, username=username, password=password)
        atexit.register(client.close)
        self.client = client

    def __call__(self, command):
        stdin, stdout, stderr = self.client.exec_command(command)
        sshdata = stdout.readlines()
        for line in sshdata:
            # end = '' -  to  loose space after the loops new lines
            print(line, end='')


remote = myssh(hostname, username, password)

# CHECK HARDWARE COMMANDS
if vendor == "Dell":
    print("1. HARDWARE VENDOR:" + vendor)
    print("2. CPU INFO")
    remote("cat /proc/cpuinfo | grep -e 'model name' -e 'physical id' | cut -c 1- | sort | uniq -c")
    remote("cat /etc/release | grep PLATFORM")
    print("3. PHYSICAL DISK SMART PREDICABLE STATUS: NO is Ok!")
    remote("omreport storage pdisk controller=0 | egrep '^ID|Status|State|Failure|Capacity' | grep -v Power | grep -v 'Status' | grep 'Failure Predicted'")
    print("4. BATERRY STATUS:")
    remote("omreport storage battery | grep H740 -A 4  | grep -oh 'Ok'")
    remote("omreport storage battery | grep H740 -A 4  | grep -oh 'Ready'")
    print("5. Bios Version:")
    remote("omreport chassis bios | grep 'Version' | awk '{print $3}'")

elif vendor == "HP":
    print("1. HARDWARE VENDOR:" + vendor)
    print("2. CPU INFO")
    remote("cat /proc/cpuinfo | grep -e 'model name' -e 'physical id' | cut -c 1- | sort | uniq -c")
    remote("cat /etc/release | grep PLATFORM")
    print("3. PHYSICAL DISK STATUS")
    remote("hpssacli ctrl all show config | egrep -i '(ok|failed|error|offline|rebuild|ignoring|degraded|skipping|nok)'")
    print("4. BATERRY STATUS")
    remote("hpssacli ctrl all show status | grep 'OK'")
    print("5. Bios Version:")
    remote("dmidecode --type bios | grep -e Version -e 'Release Date'")

else:
    print("1. HARDWARE VENDOR:" + vendor)
    print(vendor + " is this")

# Potential output remote commands could be added

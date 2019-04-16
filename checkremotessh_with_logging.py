#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#SERVER check parse XML and execute Commands to TESTLINK PYTHON API

import atexit
import shutil
import fileinput
import paramiko
import sys
import xmltodict
import lxml.etree as etree
import dicttoxml
import logging
import json
import os, subprocess
import base64
#from xml.dom.minidom import parse, parseString
import socket
import glob
import time
import logging
#from xml.etree import ElementTree as et
#from xml.etree import ElementTree
import xml.etree.ElementTree as ET
#import lxml.etree as ET
#import xml.etree.ElementTree


#import untangle


if len(sys.argv) < 2:
    print("args missing")
    sys.exit(1)


password = sys.argv[1]
testproject = sys.argv[2]
hostname = sys.argv[3]
hostname1 = sys.argv[4]

username = "root"

# Check Vendor
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port=22, username=username, password=password)
stdin, stdout, stderr = client.exec_command("dmidecode | egrep Vendor | awk '{print $2}'")
vendor = stdout.read().decode('utf-8')
vendor = vendor.strip('\n')
stdin, stdout, stderr = client.exec_command("hostname")
host = stdout.read().decode('utf-8')
host = host.strip('\n')
client.close()

#!! Important adjust the folder according to linux or windows folder schema
#delete output files to avoid double data 
#delete the file if exists no to append twice the same results inside the same file
if os.path.exists(os.path.join('./outputxml','hp_output-{}.xml'.format(host))): 
    os.remove(os.path.join('./outputxml','hp_output-{}.xml'.format(host)))
    print("### Earlier HP XML results are deleted and checks will be overwritten. ###")
elif os.path.exists(os.path.join('./outputxml','dell_output-{}.xml'.format(host))):
    os.remove(os.path.join('./outputxml','dell_output-{}.xml'.format(host)))
    print("### Earlier DELL XML results are deleted and checks will be overwritten. ###")
else:
    print("### There were no earlier results done or XML output files were deleted. ###")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
class myssh:
# finish check vendor
    def __init__(self, hostname, username, password, port=22):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname, port=port, username=username, password=password, gss_auth=False, compress=True)
            #chan = self.ssh.get_transport().open_session()
            #chan.settimeout(108000)
            #time.sleep(1)
            logger.info("Connection Created")
        except: 
            logger.error("Connection refused")
        atexit.register(client.close)
        self.client = client
        #client.close()

    def __call__(self, command):
        stdout_outputs = []
        pre_command = """
        declare -x PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/kisoft/db/product/12.1.0/db_1/bin/:/opt/dell/srvadmin/bin:/opt/dell/srvadmin/sbin:/root/bin";
        declare -x ORACLE_BASE="/kisoft/db";
        declare -x ORACLE_HOME="/kisoft/db/product/12.1.0/db_1";
        . ~/.bash_profile;
        """
        command= pre_command + command
        stdin, stdout, stderr = self.client.exec_command(command,bufsize=-1,timeout=None,get_pty=False,environment=None)
        #for line in stdout.readlines:
        #    new = stdout.readlines().strip()
        #sshdata = stdout.readlines()
        #for line in sshdata:
            # end = '' -  to  loose space after the loops new lines
            #print(line, end='')
            #stdout_outputs.append(sshdata, end='')
        
        novi = stdout.read().decode('utf-8').strip("\n")
        stdout_outputs.append(novi)
        #stdout_outputs.append(stdout.readlines)
        #for p in stdout_outputs:
        #    print("LOKALNA", p)
        return stdout_outputs


def xml_to_dict(xml_doc):
    with open(xml_doc) as f:
        #data = xmltodict.parse(f.read(), force_list={})
        data = xmltodict.parse(f.read())

        #print(json.dumps(data, indent=4)) #check dict
    return data

def get_output_dict():    
    if vendor == 'HP':    
        data = xml_to_dict(xml_doc='hp_input.xml')  
    elif vendor == 'Dell':
        data = xml_to_dict(xml_doc='dell_input.xml')          
    for test in data['platform']['vendor']['tests']:
        time.sleep(2)
        #kupim komandu iz rjecnika koji sam konvertovao i parsirao
        command = test.get('command') #continue if command is not present 
        print("komanda", str(command))
        #output = list(dict(command=remote(command)))              
        #output = dict(command=remote(command))
        #!Output dobijam kao listu i moram konvertovati u string
        output = remote(command)
        print("OUTPUT KOMANDE:", output)
        #print("3.6", output)
        #!Konvertujem listu u string - string ima b\ na pocektu
        #!TO-DO vidjeti kako uraditi byte konverziju na utf-8
        str1 = ''.join(str(e) for e in output)
        #print("Konvertovana",str1)
        #print("isinstance (str1, string)", isinstance(str1, str))
        
        for key in test.keys():
          if key == 'command':
             #if str1 == test['@equals']:
                
             #print(str1)
             print("Going trough TESTLINK category: ",(test['@name']))
             test[key] = str1
             #Change command key name with result using .pop
             test['Result'] = test.pop('command')

        

        ####TRANSITION DATA INTO API####
        command1 = test.get('question')
        output1 = remote(command1)
        #print("TEST OUTPUT", output1)
        str2 = ''.join(str(e) for e in output1)
        #print("Rezultat:",str2)
        #print("TEST", str1)
        #apiresult = []
        for key1 in test.keys():
            if test['@condition'] == "ge" and str2 >= test['@equals']:
                   #print("moj equals je ge ", test['@equals'])
                   #print("TRUE GE RESULT", str2)
                   test['@pass'] = 'p'
                   #print("Test PASSED: ",(test['@name']))
            elif test['@condition'] == "e" and test['@equals'] == str2:  
                   test['@pass'] = 'p'
                   #print("Test PASSED:",(test['@name']))
            #elif test['@condition'] == "empty" and test['@equals'] == str2:
                   #print("TRUE E RESULT", str2)
            else: 
                   test['@pass'] = 'f'    
                   #print("Test FAILED: ",(test['@name']))
                   #print("FALSE RESULT", str2)
                   #print("FALSE")
        
            #if test['@condition'] == "eq" and test['@equals'] == str2:
            #      print("moj equals je eq ", test['@equals'])
                  #print("moj TEST", str2)
            #      test['@pass'] = 'p' 
            #else:
            #       test['@pass'] = 'f'
            #       print("FALSE")
               #apiresult.append(str1)
            
            #else:
            #   print("moj equals nije: ", test['@equals'])
               #test['@pass'] = 'f'
               #apiresult.append(str1)
        #print("OVO je string:", apiresult)   
         
        #print("finalni test-bas-finalni", test)
    #print("MOJE JSON.DUMP:DATA", json.dumps(data))
    return json.loads(json.dumps(data))





def get_output_xml(output_dict, hostime):
    #debug dict error with xml in Log
    #dicttoxml.set_debug()
    #deparse the dict bactk to xml
    output_xml = dicttoxml.dicttoxml(output_dict, custom_root='output', attr_type=False, root=False)
    if vendor == 'HP':
        filename = 'hp_output-{}.xml'.format(host)
    elif vendor == 'Dell':
        filename = 'dell_output-{}.xml'.format(host)
    tree = etree.fromstring(output_xml)
    output_xml_string = etree.tostring(tree, pretty_print=True)
    #print("TEST123", output_xml_string)
    
    #with open(filename, 'wb') as f:
    #with open(os.path.join('./output',filename), "wb") as f:
    #MERGE with "ab" EVERY ITERATION OF XML FILE READ FROM the FUNCTION in one FILE
    with open(os.path.join('./outputxml',filename), "ab") as f:
        f.write(output_xml_string)
    print('Output for hostname server: {} written to: {}'.format(host, filename))        
    return output_xml
#example check of which type is the instance
#isinstance (str1, string)", isinstance(str1, str))

#Check HP iLo License file and create the file in /tmp 
#!! Important adjust the folder according to linux or windows folder schema
def writehpilofile(tohost):
    if vendor == "HP": 
       client1 = paramiko.SSHClient()
       client1.load_system_host_keys()
       client1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
       client1.connect(tohost, port=22, username=username, password=password)
       sftp = client1.open_sftp()
       sftp.put('Get_ILO_Firmware_Version', '/tmp/Get_ILO_Firmware_Version.xml')
       sftp.close()
       client1.close
       print("HP ILO file was written on host:", tohost)
    else: 
       print("We could not recognize HP Vendor and did not write the iLo check file in /tmp")

for x in range(3, len(sys.argv)):
    print("Checking Server: %s" % (sys.argv[x]))
    writehpilofile(sys.argv[x])
    remote = myssh(sys.argv[x], username, password)
    data = get_output_dict()
    xml = get_output_xml(data, sys.argv[x])


#check if the XML files exists (dell or hp) and parse them to XML for further checks and import in API TESTLINK
if os.path.exists(os.path.join('./outputxml','hp_output-{}.xml'.format(host))): 
     inputfile=os.path.join('./outputxml','hp_output-{}.xml'.format(host)) 

elif os.path.exists(os.path.join('./outputxml','dell_output-{}.xml'.format(host))):
     inputfile=os.path.join('./outputxml','dell_output-{}.xml'.format(host))

else:
    print("### There are no INPUT Files to parse the XML !!! ###")
    print('dell_output-{}.xml'.format(host))


#open a summarized xml file and add the new edge root tags to have a complete one XML merged file
original_xml = open(inputfile, "r")
firstline = "<serverchecks>\n"
lines = original_xml.readlines()
# Here, we prepend the string we want to on first line
lines.insert(0, firstline)
original_xml.close()
# We again open the file in WRITE mode and the writelines goes to the end of the file
src = open(inputfile, "w")
src.writelines(lines)
src.write("\n</serverchecks>") # we add a new line at the end and add the final root tag
src.close()

#PARSE the merged XML FILE
tree = ET.parse(inputfile)
root = tree.getroot()


#GET the "p" and "f" items from the MERGED XML and sort the FALSE or PASSED results for python API subprocess.call
### NESTO KAO NAPRIMER IF sys.argv(4) je prazan onda pass_list = sorted_list a ako ne onda je vise IP i sortira se
pass_list = []
for my_pass in root.findall("./platform/vendor/tests/item/key/[@name='@pass']"):
    pass_list.append(my_pass.text)
    #print("True or false", my_pass.text, sep='\n')
#CUT the list of all tests in two halfs and will be later sorted in another pass_list_sorted list
#!!!  We need the logic to check if only one IP with IF not to cut the list in two !!!
pass1 = pass_list[-len(pass_list)//2:]
pass2 = pass_list[:len(pass_list)//2]
#SORT the results from both lists (two XML files with checks) and check for Failed "f" results and sort inside pass_list_sorted
pass_list_sorted = []
for x,y in zip(pass1, pass2):
    if x == y:
        pass_list_sorted.append(x)
    else:
        pass_list_sorted.append("f")
#print("Final PASS List:", pass_list_sorted)



#FIND all @NAME subelements in MERGED XML - to use as TEST Categories in TESTLINK API CALL
my_list = []
for sshcommand in root.findall("./platform/vendor/tests/item/key/[@name='@name']"):
    #print('Going trough TESTLINK category: {}'.format(sshcommand.text))
    my_list.append(sshcommand.text)
    #print("Länge: %d" % len(my_list))

#USE SET to SORT out the DOUBLE VALUES from MULTIPLE Servers
#new_list = sorted(set(my_list))

#new_list = set(list(my_list)) --- SET is unordered and the ORDER did not work
#!! SINCE THE SET is not ordered by NATURE we needed to get it ordered from list(dict.fromkeys(list_with_double_results)
#!! The order of categories is important for API CALL insertion in TestLink
new_list = list(dict.fromkeys(my_list))
#print("number of elements after sort and uniq: %d" % len(new_list))
#print("sortirana lista", new_list)

api_bug_list = ['bios version','iLo', 'hard disks', 'storage', 'network cards']
my_pass = []
#ITERATION trough two lists. The new_list from @name Key and pass_list_sorted from @pass key
#to get the values as input parameter for both PARAMETER (my_key, summpas) in the API CALL subprocess.call
for my_key,summpas in zip(new_list,pass_list_sorted):
    summarized_result = []
    #iterate over all results for a given check-name and store it to a list
    for single_result in root.findall("./platform/vendor/tests/item/[key='%s']/Result" % my_key):       
        summarized_result.append(single_result.text)
        #print("Rezultati pojedinacno:", my_key)
    
    summstr = '\n'.join(str(e) for e in summarized_result)#join the result as string and start a new line
   
    #API CALL TESTLINK WITH PARAMETERS FILTERED OUT FROM THE MERGED XML FILE
    #print("OVO unosimo kao Passed/Failed u API: " ,summpas)
     
    if summpas == 'p':
       print("Test passed: ", my_key)
    else: 
       print("Test is FAILED: ", my_key)
    ##PYTHON API HAS A BUGERROR INDEX OUT OF RANGE if the VENDOR continues as HP so I need to replace it as number 1
    if vendor == "HP" and my_key in api_bug_list:
       vendor="HP"
       #print("Vendor petlja", vendor)
    #elif vendor == "Dell":
    #   vendor="Dell"
    #   print("Vendor petlja", vendor)
    else:
        vendor="1"
        #print("Vendor petlja", vendor)
    #print("Ovo su kategorije ", my_key)
    #!!!IMPORTANT - summpas and summstr have to have the same VALUE LENGTH to insert the same result in the API CALLs
    subprocess.call(["python", "./testlink_poc/build_tools-master/tools/testlinkAPI/executeTestcase_stefan.py", "CTP", testproject, my_key, summpas, vendor, "SXA", summstr])
    #subprocess.call(["python", "./testlink_poc/build_tools-master/tools/testlinkAPI/executeTestcase_stefan.py", "CTP", "test_hp", my_key, "p", "HP", "SXA", summstr])









#for line in file:
#     if '<platform>' in line:
#         for _ in range(4): # skip this line and next 4 lines
#             next(file, None)
#     else:
#         print(line)

#for pathname in glob.glob("*.xml"):
#   print(pathname)
    
#with open('hp_output-de00949-dhl-bonn-srv2.xml', 'r') as file:
    # read a list of lines into data
#    data = file.readlines()

#print(data)
#print("TESTFAJLOVI: " + data[0])

# now change the 2nd line, note that you have to add a newline
#data[1] = '<platform>\n'

# and write everything back
#with open('hp_output-de00949-dhl-bonn-srv2.xml', 'w') as file:
#    file.writelines(data)


#import lxml.etree as ET
#tree = ET.parse('hp_output-de00949-dhl-bonn-srv2.xml')   
#root = tree.getroot()
#newroot = ET.Element("root")
#newroot.insert(0, root) 
#print(ET.tostring(newroot, pretty_print=True))




    

#https://docs.python.org/3.5/library/xml.etree.elementtree.html#xml.etree.ElementTree.Element.iter
#dir = './output'
#for file in glob.iglob(os.path.join(dir, '*.xml')):
#   with open(file) as f:
#      tree = ET.parse(f)
#      root = tree.getroot()
      #print(root.attrib)
      #for child in root:
      #  print(child.tag, child.attrib)
      #for result in root.iter('tests'):
      #  print(result.attrib)
      #result = root.findall('Result')
#      for sshcommand in root.findall("./vendor/tests/item/key/[@name='@type']/.../Result"):
 #         print("KOMANDA:", sshcommand.text)

      
      
      
      #data = ET.parse(f)
      #root = data.getroot()
      #data = etree.parse(f)
      #print(ET.tostring(root, encoding='utf8').decode('utf8'))
      #output_xml_string1 = ET.tostring(root, encoding='utf8').decode('utf8')
   #with open("mergedfile1.xml", "wb") as xz:
      #xz.write(output_xml_string1.encode('utf8'))
      #for sshcommand in output_xml_string1.findall("./vendor/tests/item/key/[@name='@type']/.../pass"):
       #   print("KOMANDA:", sshcommand.text)
   #print("OUTPUT BOTH FILES", data)
   
   #root.write('hp_output-{}.xml'.format(host))
   




#dom1 = parse('hp_output-de00949-dhl-bonn-srv1.xml')



#def xml_to_dict1(xml_doc):
#    with open(xml_doc) as f:
        #data = xmltodict.parse(f.read(), force_list={})
#        tree = ET.parse(xml_doc)
#        data1 = xmltodict.parse(f.read())

        #print(json.dumps(data1, indent=4)) #check dict
#    return data1

#xml_to_dict1("hp_output-de00949-dhl-bonn-srv1.xml")

#!!! TO-DO 
# for sshcommand in root.findall("./vendor/tests/item/key/[@name='@type']/.../Result"):
#    print(sshcommand.text)
#kako pronaci neki kljuc pa dalje raditi 


#!!! TO-DO provjeriti kako atribute menjati za validaciju u velikom XML-u 
###  https://www.datacamp.com/community/tutorials/python-xml-elementtree
### guglati za lxml.etree merging two xml files



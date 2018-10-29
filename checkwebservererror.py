#!/usr/bin/env python
import sys
import httplib

# loope over sites and if anython but 200 or 301 shows sound alarm

for site_name in ["www.example.com", "my.example.com"]:
    try:
        conn = httplib.HTTPConnection(site_name)
        conn.request("HEAD", "/")
        r1 = conn.getresponse()
        conn.close()
        website_return = r1.status
        if website_return == 200 or website_return == 301:
            print site_name + " OK"
           
        else:
            print "Problem with " + site_name
           
      
    except Exception as e:
        print "Possibly server down " + site_name

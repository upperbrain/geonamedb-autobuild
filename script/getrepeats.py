#!/usr/bin/python

#This script gets list of geonameId has recorded over once.
#Python getrepeats.py

import sys
import re
import codecs
import requests
import json
import datetime
import os
import time
import pymysql

start_time = time.time()


def parse(conn):
    #get list of geonameid, name, countryCode
    global cur
    cur = conn.cursor()

    sql = "SELECT geonameId FROM geoinformation_cms.wikiinfo GROUP BY geonameId HAVING COUNT(*) > 1"
    data = cur.execute(sql)
    print data
    results = cur.fetchall()
    
    for row in results:
       print("====")
       print row
       
    cur.close()
    print("--- %s seconds ---" % str(datetime.timedelta(seconds=round(time.time() - start_time))))


def get_mysql_connection():
    #fill host, user, passwd and db with your access info.
    conn = pymysql.connect(host="HOSTNAME", user="USERNAME", passwd="PASSWORD", db="DBNAME", use_unicode=True, charset='utf8')
    return conn


if __name__ == '__main__':
    conn = get_mysql_connection()
    parse(conn)
    conn.close()
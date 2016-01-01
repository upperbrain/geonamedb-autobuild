#!/usr/bin/python
#This script looks up geonames database based on texfile.txt. Basically, this is automating searching location on search.php.
#As an output, this will create attraction_include.html.
#Input data is textfile_normalize.txt, and this needs to be normalized by fuzzy.py.
#Python getlocations.py GB_normalize.txt

import sys
import re
import codecs
import os
import time
import datetime
import pymysql

GEONAME = r"geonameid=([0-9]+)"
ERROR = r"Error"
PARENTHESE = r'\(.+\)'
SQRBRACKET = r'^\[.+\]?'
SQRBRACKETDOUBLE = r'^\[\[.+\]\]?'
CURLYBRACKET = r'\{\{(.+)\}\}'
COMMA = r',+'

def listParser(textFile, conn):
    readfile = codecs.open(textFile, 'r', 'utf-8')
    lines = [line.rstrip('\n') for line in readfile]
    
    global cur
    cur = conn.cursor()
    
    try:
        htmlOut = codecs.open("../attraction_inlcudes/attraction_inlcude.html", "wr", "utf-8")
        
        tempTXT = None
        countryCode = None
        for lin in lines:
            if lin:
                tempTXT = unicode(lin)
                
                print tempTXT
                if re.findall(PARENTHESE, unicode(tempTXT), flags=re.IGNORECASE):
                    get_result(tempTXT.split('(')[0],countryCode,htmlOutIndi)
                elif re.findall(SQRBRACKETDOUBLE, unicode(tempTXT), flags=re.IGNORECASE):
                    #create new file
                    filenamepart = tempTXT.split('[[')[1].split(']]')[0].replace(" ","_")
                    filename = "../attraction_inlcudes/%s/%s_%s.html" % (countryCode,countryCode,filenamepart)
                    dirname = "../attraction_inlcudes/%s" % (countryCode)
                    if not os.path.exists(dirname):
                        os.makedirs(dirname)
                    htmlOutIndi = codecs.open(filename, "wr", "utf-8")
                    print "created htmlOutIndi"
                elif re.findall(SQRBRACKET, unicode(tempTXT), flags=re.IGNORECASE):
                    #this going to be title which is name of country
                    countryCode = get_country_code(tempTXT.split('[')[1].split(']')[0],htmlOut)
                    htmlOut.write("<h2>"+unicode(tempTXT.split('[')[1].split(']')[0])+"</h2>")
                elif re.findall(CURLYBRACKET, unicode(tempTXT), flags=re.IGNORECASE):
                    #this going to be an additional info of source of list
                    print re.findall(CURLYBRACKET, unicode(tempTXT), flags=re.IGNORECASE)[0]
                    htmlOutIndi.write("<h3>"+re.findall(CURLYBRACKET, unicode(tempTXT), flags=re.IGNORECASE)[0]+"</h3>")
                elif re.findall(COMMA, unicode(tempTXT), flags=re.IGNORECASE):
                    get_result(tempTXT.replace(',','%82').split(',')[0],countryCode,htmlOutIndi)
                else:
                    get_result(tempTXT,countryCode,htmlOutIndi)
                    
    except:
        print 'error'
        print "tempTXT=> " + tempTXT
        readfile.close()
        htmlOut.close()
        htmlOutIndi.close()
        
    readfile.close()
    htmlOut.close()
    htmlOutIndi.close()
    

def get_result(tempTXT, tempCountryCode, htmlOut):
    htmlOut.write("<h4>"+unicode(tempTXT)+"</h4>")
    
    sqlSelect = """SELECT * FROM all_countries WHERE MATCH(name) AGAINST ("+%s" IN NATURAL LANGUAGE MODE) LIMIT 1""" % unicode(tempTXT)
    
    data = cur.execute(sqlSelect)
    if data > 0:
        results = cur.fetchall()
        for row in results:
            geonameId = row[0]
            locationName = row[1]
            #print "locationname is %s" % locationName
            countryCode = row[8].encode('utf-8')
            #print "countrycode is %s" % countryCode
            #print "Found for %s: %s(%s), %s" % (unicode(tempTXT),unicode(locationName).encode(),geonameId,str(countryCode))
            if countryCode == tempCountryCode:
                htmlOut.write("<div><span>Found for "+unicode(tempTXT)+":"+unicode(locationName)+"\
                (<a target='_blank' href='../../manage.php?geonameid="+str(geonameId)+"'>"+str(geonameId)+"</a>), "+str(countryCode)+"</span></div>")
            else:
                htmlOut.write("<div>Can not find "+unicode(tempTXT)+" in "+str(tempCountryCode)+", \
                instead we found it in "+str(countryCode)+". \
                please use different location name.</div>")
                htmlOut.write("<div>Add <a target='_blank' href=\"../../addattraction.php?locationname="+unicode(tempTXT)+"&countrycode="+str(tempCountryCode)+"\">"+unicode(tempTXT)+"</a></div>")
        #os._exit(1)
    else:
        #print 'Cant find exact match for %s' % unicode(tempTXT)
        htmlOut.write("<div>Can not find exact match for " + unicode(tempTXT) + "</div>")
        #NATURAL LANGUAGE MODE option cant find it, then lets use BOOLEAN MODE,
        #So we can get some more variations.
        sqlSelectBoolean = """SELECT * FROM all_countries WHERE MATCH(name) AGAINST ("+%s*" IN BOOLEAN MODE) LIMIT 10""" % tempTXT
        dataBool = cur.execute(sqlSelectBoolean)
        #create list of possible matches
        if dataBool > 0:
            print 'Here are list of possible matches:'
            htmlOut.write("<div>Here are list of possible matches:</div>")
            tempLocation = ""
            resultsBool = cur.fetchall()
            for rowBool in resultsBool:
                geonameIdBool = rowBool[0]
                locationNameBool = rowBool[1]
                countryCodeBool = rowBool[8].encode('utf-8')
                #print "Do you mean %s(%s) in %s?" % (locationNameBool,geonameIdBool,countryCodeBool)
                tempLocation+="%s(%s), " % (unicode(locationNameBool),str(countryCodeBool))
            print tempLocation
            htmlOut.write("<div>"+tempLocation+"</div>")
        else:
            #There is no such a thing.
            #print 'Cant find %s, please use different location name.' % tempTXT
            htmlOut.write("<div>Can not find possible match of "+unicode(tempTXT)+", \
            please use different location name.</div>")


def get_country_code(tempTXT, htmlOut):
    sqlSelectCountry = """SELECT * FROM countryinfo WHERE name LIKE "%s" """ % unicode(tempTXT)
    dataCountry = cur.execute(sqlSelectCountry)
    if dataCountry > 0:
        resultsCountry = cur.fetchall()
        return resultsCountry[0][0]
    else:
        return "(Country not found)"
        

def get_mysql_connection():
    #fill host, user, passwd and db with your access info.
    conn = pymysql.connect(host="HOSTNAME", user="USERNAME", passwd="PASSWORD", db="DBNAME", use_unicode=True, charset='utf8')
    return conn
    
if __name__ == "__main__":
    start_time = time.time()
    
    conn = get_mysql_connection()
    listParser(sys.argv[1], conn)
    conn.close()
    
    print("--- %s seconds ---" % str(datetime.timedelta(seconds=round(time.time() - start_time))))
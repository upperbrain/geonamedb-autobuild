#!/usr/bin/python
#This script is for checking any repeated location names in raw location file.
#Also this is checking possible fuzzy match of locations.
#Input is raw txt file(file.txt), and output is normalized txt file(file_normalize.txt) and report file(file_nomalize_report.txt).
#Python fuzzy.py file.txt

import sys
import re
import codecs
import os
import time
import datetime
import Levenshtein

METAINFOTAG = r"^\{+"

def strParser(strTXT):
	
	txtfile = codecs.open(strTXT, 'r', 'utf-8')
	outfile = '../popularlocation/'+os.path.splitext(strTXT)[0]+'_normalize.txt'
	outreportfile = '../popularlocation/'+os.path.splitext(strTXT)[0]+'_normalize_report.txt'
	lines = [line.rstrip('\n') for line in txtfile]
	
	outreportfileOpen = codecs.open(outreportfile, 'wr', 'utf-8')
	outfileOpen = codecs.open(outfile, 'wr', 'utf-8')
	
	try:
		fuzzyTXT = None
		fuzzyIdx = None
		idxKill = None
		newLines = ''
		outreportfileOpen.write('#Automation report#####################################\n')
		for idx, lin in enumerate(lines):
			
			if lin and not re.findall(METAINFOTAG,unicode(lin),flags=re.IGNORECASE):
				maxFuzzyMatchRate = 0
				fuzzyMatchRate = 0
				source = unicode(lin)
				lines[idx] = ''
				chkedLines = lines[:idx]
				tempLines = chkedLines + lines[idx:]
				
				for sidx, slin in enumerate(tempLines):
					if slin and not re.findall(METAINFOTAG,unicode(slin),flags=re.IGNORECASE):
						if lin == slin:
							if idx is not sidx:
								#print '%s(%s) and %s(%s) are repleated in diffetent position' % (lin,idx+1,slin,sidx+1)
								#print 'Removing %s from line %s...' % (slin,sidx+1)
								outreportfileOpen.write('# %s(%s) and %s(%s) are repeated in different position\n' % (lin,idx+1,slin,sidx+1))
								outreportfileOpen.write('# Removing %s from line %s...\n#\n' % (slin,sidx+1))
								idxKill = sidx
						else:
							target = unicode(slin)
							fuzzyMatchRate = Levenshtein.ratio(source,target)
							if fuzzyMatchRate > maxFuzzyMatchRate:
								maxFuzzyMatchRate = fuzzyMatchRate
								fuzzyTXT = target
								fuzzyIdx = sidx
				#0.8 is alomost exact match
				if maxFuzzyMatchRate >= 0.9:
					#print '%s(%s) and %s(%s) are fuzzy match in diffetent position' % (source,idx+1,fuzzyTXT,fuzzyIdx+1)
					outreportfileOpen.write('# %s(%s) and %s(%s) are fuzzy match in different position\n#\n' % (source,idx+1,fuzzyTXT,fuzzyIdx+1))
			#Kill repeats
			if idxKill:
				lines[idxKill] = ''
			
			if lin.strip() != '':
				newLines += lin + '\n'
		outreportfileOpen.write('#######################################################\n')
		print(newLines)
		outfileOpen.write(newLines)
		
		
	except:
		print 'error'
		print "source=> " + source
		txtfile.close()
		outfileOpen.close()
		outreportfileOpen.close()

	txtfile.close()
	outfileOpen.close()
	outreportfileOpen.close()


if __name__ == "__main__":
	start_time = time.time()
	
	strParser(sys.argv[1])
	
	print("--- %s seconds ---" % str(datetime.timedelta(seconds=round(time.time() - start_time))))
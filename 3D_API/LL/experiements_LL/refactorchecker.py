import subprocess
import sys

argv = sys.argv
if len(argv) < 2:
    print "Comand Line arg missing\nEnter: \n1 for original hotspot\n2 for refactored Hotspot\n3 to compare outputs"
    sys.exit(0)
#print len(argv)
if int(argv[1]) == 1:
    try:
        run_hotpsot = "python hotspot.py test.data air --no_images"
        #print run_hotpsot
        proc = subprocess.Popen(run_hotpsot, stdout=subprocess.PIPE, shell=True)
    except:
        print "Run error in hotspot!"
    hotspot = proc.communicate()[0].rstrip()
    print 'Hotspot',hotspot
elif int(argv[1]) == 2:
    try:
        run_hotpsot = "python hotspot_LL.py test.data air --no_images"
        #print run_hotpsot
        proc = subprocess.Popen(run_hotpsot, stdout=subprocess.PIPE, shell=True)
    except:
        print "Run error in hotspot!"
    hotspot = proc.communicate()[0].rstrip()
    print 'Hotspot_LL',hotspot
elif int(argv[1]) == 3:
    try:
        run_hotpsot = "python hotspot.py test.data air --no_images"
        run_hotpsot_LL = "python hotspot_LL.py test.data air --no_images"
        #print run_hotpsot
        proc = subprocess.Popen(run_hotpsot, stdout=subprocess.PIPE, shell=True)
        proc_LL = subprocess.Popen(run_hotpsot_LL, stdout=subprocess.PIPE, shell=True)
    except:
        print "Run error in hotspot!"
    hotspot = float(proc.communicate()[0].rstrip())
    hotspot_LL = float(proc_LL.communicate()[0].rstrip())
    #print 'Hotspot',hotspot
    #print 'Hotspot_LL',hotspot

    if hotspot != hotspot_LL:
        import math
        diff = math.fabs(hotspot_LL - hotspot)
        print '!!!difference of ', diff
        print 'hotspot is ',hotspot
        print 'hotspot_LL is ', hotspot_LL
    else:
        print "GOOD!!!!!!!!!!!"
"""
elif int(arg[1] == 4):
    try:

    except:
"""

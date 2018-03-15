#!/usr/bin/python
# -*- coding: utf-8 -*-

import os #order says it should be placed before from flask import Flask
import sys #order says it should be placed before from flask import Flask
from collections import OrderedDict #order says it should be placed before from flask import Flask
from flask import Flask, render_template   # redirect, url_for, request are not used in this file
import requests #order says it should be placed before Freezer
from flask_optimize import FlaskOptimize #order says it should be placed before Freezer
from PIL import Image #order says it should be placed before Freezer
from flask_frozen import Freezer #No matching distribution found for flask_frozen, only Freezer
import uucsv

BUILDURL = "/SunshineScorecard18/"     # Also need to patch in static/app.js at homeurl
BASEURL = "http://interactive.orlandosentinel.com" + BUILDURL
COUNTYDICT = {}
MASTERDICT = {}
LISTOFVOTES = []
DICTOFVOTES = {}
HIGHESTSCORE = 0
SCORESDICT = {}
IMGORIGINALPATH = "./static/imgoriginals/"
IMGTHUMBPATH = "./static/imgthumbs/"
TARGETWIDTH = 132
TARGETHEIGHT = 176
BRACKETLU = {
    0: "F--",
    1: "F-", 2: "F", 3: "F+", 4: "D-", 5: "D", 6: "D+",
    7: "C-", 8: "C", 9: "C+", 10: "B-", 11: "B", 12: "B+",
    13: "A-", 14: "A", 15: "A+",
    16: "A++"
    }


application = Flask(__name__)
CONFIG_UPDATE = {'html': {'htmlmin': True, 'izip': False, 'cache': False},
                 'json': {'htmlmin': True, 'izip': False, 'cache': False},
                 'text': {'htmlmin': True, 'izip': False, 'cache': False}}

FLASK_OPTIMIZE = FlaskOptimize(config_update=CONFIG_UPDATE)
# flask_optimize = FlaskOptimize()
freezer = Freezer(application)


@application.route('/')
# @flask_optimize.optimize('html')
def index():
    template = 'index.html'
    global MASTERDICT
    global COUNTYDICT
    return render_template(template, masterdict=MASTERDICT, counties=COUNTYDICT, baseurl=BASEURL, buildurl=BUILDURL)


@application.route('/scorecard/<slug>/')
# @flask_optimize.optimize('html')
def scorecard(slug):
    template = 'pol.html'
    global MASTERDICT
    for polslug in MASTERDICT:
        pol = MASTERDICT[polslug]
        if polslug == slug:
            return render_template(template, pol=pol, baseurl=BASEURL, buildurl=BUILDURL)

def get_neighbors(key,sourcelist): #https://stackoverflow.com/questions/18453290/funcargs-kwargs-x-throwing-invalid-syntax        
    if(len(sourcelist)) == 0:
        newlist = []  # If blank list, return blank list.
    else:
        newlist = []

        for i, value in enumerate(sourcelist):  # Doing 2x lookups. Whatever.
            newlist.append({})
            if i == 0:  # If the first value, previous is the last one in the list
                newlist[i]["previous"] = sourcelist[-1][key]
            else:
                newlist[i]["previous"] = sourcelist[i-1][key]
            if i == len(sourcelist) - 1:  # If the last one in the list, next is the first one
                newlist[i]["next"] = sourcelist[0][key]
            else:
                newlist[i]["next"] = sourcelist[i+1][key]
    return newlist                        
         
def get_bracket(max, instancevalue):
    lengthofrange = 2 * max
    spread = lengthofrange / 15.0
    # print(spread)
    brackets = []
    for i in range(0, 15):    # Get 15 results, 0-14
        target = 0 - max + (i * spread)
        brackets.append(target)
    brackets.append(1000.0)
    bracketnumber = sys.maxsize
    if instancevalue < (0 - max):         # If off the charts low, assign F--
        bracketnumber = 0
    elif instancevalue > max:               # If off the charts high, assign A++
        bracketnumber = 16
    else:
        for i in range(0, 15):
            # print(str(i + 1) + ": " + str(brackets[i]))
            # print(str(instancevalue) + " instancevalue")
            # print("bracket range " + str(brackets[i]) + " to " + str(brackets[i+1]))
            if instancevalue >= brackets[i] and instancevalue < brackets[i+1]:
                bracketnumber = i + 1   # Show brackets as 1-15 rather than 0-14
                # break
        if bracketnumber == sys.maxsize:
            print("Something broke on value" + str(instancevalue))
    return bracketnumber

# Call like this: bracket = get_bracket(maxvalue, person's score)


def structure_data():
    with open('pols.csv', 'r') as csvfile:
        global pols
        global COUNTYDICT
        global MASTERDICT
        global LISTOFVOTES
        global DICTOFVOTES
        global HIGHESTSCORE
        global SCORESDICT
        pols = uucsv.UnicodeDictReader(csvfile)
        
        #sorted(pols, key=lambda k: k['alphaname']) in Python2 works, but in Python3 TypeError: list indices must be integers or slices, not str
        sortedpols = sorted(pols) #happens to be sorted by alphanames
        pols = sortedpols[0] #remove outer list...
        sortedpols = None
        
        neighbortitles = get_neighbors("title", pols)
        neighbornames = get_neighbors("name", pols)
        neighborslugs = get_neighbors("slug", pols)
        for i, pol in enumerate(pols):
            pols[i]["nextname"] = neighbortitles[i]["next"] + " " + neighbornames[i]["next"]
            pols[i]["previousname"] = neighbortitles[i]["previous"] + " " + neighbornames[i]["previous"]
            pols[i]["nextslug"] = neighborslugs[i]["next"]
            pols[i]["previousslug"] = neighborslugs[i]["previous"]
        
        namelist = {}
        namelist['Senate'] = []
        namelist['House'] = []
        for pol in pols:
            namelist[pol['chamber']].append(pol['last'])
        dupslist = {}
        dupslist['House'] = sorted(set([x for x in namelist['House'] if namelist['House'].count(x) > 1]))
        dupslist['Senate'] = sorted(set([x for x in namelist['Senate'] if namelist['Senate'].count(x) > 1]))
        if len(dupslist['House']) > 0:
            print("House dups: " + "; ".join(dupslist['House']))
        if len(dupslist['Senate']) > 0:
            print("Senate duplicated last names: " + "; ".join(dupslist['Senate']))
        for pol in pols:
            last = pol['last']  # check for lastname overlaps
            if last not in dupslist[pol['chamber']]:
                pol['legname'] = last.replace("NuÌ±ez", "Nunez").replace("Nuñez", "Nunez")
            else:
                pol['legname'] = last + ", " + pol['first'][0] + "."
                if pol['legname'] == "Cortes, R.":
                    pol['legname'] = "Cortes, B."   # Robert goes by Bob, and wants his initials to go that way too.
                #if pol['legname'] == "Miller":
                    #pol['legname'] == "Miller, M."    
            for county in pol['counties'].split("|"):
                if county not in COUNTYDICT:
                    COUNTYDICT[county] = []
                COUNTYDICT[county].append(pol)
    COUNTYDICTsorted = OrderedDict()
    for county in sorted(COUNTYDICT):
        COUNTYDICTsorted[county] = COUNTYDICT[county]      # Use sorted list of keys to build ordered dictionary
    COUNTYDICT = COUNTYDICTsorted
    for county in COUNTYDICT:
        for pol in COUNTYDICT[county]:
            process_images(photourl=pol["photourl"], slug=pol["slug"])
    print(str(len(COUNTYDICTsorted)) + " counties found")
    with open('billlist.csv') as billlistfile:  # Let's build a lookup table
        billlistreader = uucsv.UnicodeDictReader(billlistfile)
        sortedbillistreader = sorted(billlistreader)
        billlistreader = sortedbillistreader[0] #to remove extra outer list, not sure where the outer list came from
        sortedbillistreader = None
        billlu = {}       
        for row in billlistreader:
            billlu[row['billno']] = row
           
    csvmembers = []
    print("listofvotes size: " + str(len(LISTOFVOTES)))
    with open('autovotes.csv', 'r') as autovotesfile:
        autovotesreader = uucsv.UnicodeDictReader(autovotesfile)
        sortedautovotesreader = sorted(autovotesreader)
        autovotesreader = sortedautovotesreader[0] #to remove extra outer list, not sure where the outer list came from
        sortedautovotesreader = None
        
        for row in autovotesreader: 
            memberid = row['chamber'] + "|" + row['member']
            row['memberid'] = memberid
            LISTOFVOTES.append(row)            
            csvmembers.append(memberid)
            if memberid not in SCORESDICT:
                SCORESDICT[memberid] = 0
            SCORESDICT[memberid] += int(row["points"])

    print("listofvotes size: " + str(len(LISTOFVOTES)))
    with open('extracredits.csv', 'r') as extrasfile:
        extrasreader = uucsv.UnicodeDictReader(extrasfile)
        sortedextrasreader = sorted(extrasreader)
        extrasreader = sortedextrasreader[0]
        sortedextrasreader = None
        
        for row in extrasreader:
            memberid = row['chamber'] + "|" + row['member']
            row['memberid'] = memberid

            LISTOFVOTES.append(row)
            csvmembers.append(memberid)

            if memberid not in SCORESDICT:
                SCORESDICT[memberid] = 0
            SCORESDICT[memberid] += int(row["points"])
    for memberid in SCORESDICT:
        if HIGHESTSCORE < abs(SCORESDICT[memberid]):
            HIGHESTSCORE = abs(SCORESDICT[memberid])
    print("Highest score found: " + str(HIGHESTSCORE))
    

    for row in LISTOFVOTES:
        row['billnono'] = int(row['billno'][2:])
        row['description'] = billlu[row['billno']]['description']
        row['url'] = billlu[row['billno']]['url']
        if row["vote"] == "Y":
            row["vote"] = "Voted Yes"
        if row["vote"] == "N":
            row["vote"] = "Voted No"
        if row["vote"] == "-":
            row["vote"] = "Missed vote"
           
    exportset = {}  # because we needed more data structures
    for county in COUNTYDICT:
        for polindex, pol in enumerate(COUNTYDICT[county]):
            legid = pol['chamber'] + "|" + pol["legname"]
            if legid not in SCORESDICT:
                print("****************** Hey! Missing " + legid)
            else:
                numericscore = SCORESDICT[legid]
                bracket = get_bracket(HIGHESTSCORE, numericscore)
                lettergrade = BRACKETLU[bracket]
                COUNTYDICT[county][polindex]["numericscore"] = numericscore
                COUNTYDICT[county][polindex]["lettergrade"] = lettergrade
                exportset[legid] = [legid, pol['alphaname'], pol['chamber'], pol['party'], str(numericscore), str(bracket), lettergrade, pol['counties']]
                
    with open('report.csv', 'wb') as reportfile:
        put = uucsv.UnicodeWriter(reportfile)
        put.writerow(["legid", "alphaname", "chamber", "party", "numericscore", "bracket", "lettergrade", "counties"])
        for pol in exportset:
            put.writerow(exportset[pol])
    temp = sorted(LISTOFVOTES, key=lambda row: row["billnono"])
    listofvotes = temp  # Sort by numerical part of bill number
    for row in listofvotes:  # Now, build a list keyed to each member
        memberid = row['memberid']
        if memberid not in DICTOFVOTES:
            DICTOFVOTES[memberid] = []
        DICTOFVOTES[memberid].append(row)
    polmembers = []
    for pol in pols:
        polmembers.append(pol['legname'])    # .decode("latin-1").encode('utf-8'))
        if pol['legname'] not in polmembers:
            print(pol['legname'] + " not found from scraped CSV tallies.")
    for member in csvmembers:
        if member not in polmembers:
            # print(member + " not found from scraped membership")
            pass
    print("Didn't see any missing members? We looked at " + str(len(pols)) + " scraped members, " + str(len(set(csvmembers))) + " members from CSV and " + str(len(csvmembers)) + " votes in csvtallies")
    
    for county in COUNTYDICT:        # build person-by-person dictionary.
        for pol in COUNTYDICT[county]:
            legid = pol['chamber'] + "|" + pol["legname"]
            votes = DICTOFVOTES[legid]
            pol["votes"] = votes
            MASTERDICT[pol["slug"]] = pol
    return


@freezer.register_generator
def generate_slugs():
    yield "/"
    print("Pols found: " + str(len(pols)))
    for pol in pols:
        yield "/scorecard/" + pol['slug'] + "/"
    return


def process_images(photourl, slug):
    global IMGORIGINALPATH
    global IMGTHUMBPATH
    global TARGETHEIGHT
    global TARGETWIDTH
    filename = slug + ".jpg"
    original = IMGORIGINALPATH + filename
    thumb = IMGTHUMBPATH + filename
    for directory in (IMGORIGINALPATH, IMGTHUMBPATH):   # Make photo folders if they don't exist
        if not os.path.exists(directory):
            os.makedirs(directory)
    if not os.path.exists(original):  # if we don't have the original photo
        print("\tDownloading image ..." + original)
        response = requests.get(photourl)   # download
        with open(original, 'wb') as f:
            f.write(response.content)   # save
    if not(os.path.exists(thumb)):
        print("\tBuilding thumbnail ...")
        im = Image.open(original)
        im.resize((TARGETWIDTH, TARGETHEIGHT), Image.LANCZOS).convert('RGB').save(thumb, optimize=True)

    return


if __name__ == '__main__':
    print("Running structure_data")
    structure_data()
    generate_slugs()
    application.url_map.strict_slashes = False
    if (len(sys.argv) > 1) and (sys.argv[1] == "build"):
        application.config.update(FREEZER_RELATIVE_URLS=False, FREEZER_DESTINATION="../openflorida-frozen")
        #application.config.update(FREEZER_BASE_URL=BUILDURL, FREEZER_RELATIVE_URLS=False, FREEZER_DESTINATION="..\openflorida-frozen")
        try:
            freezer.freeze()
        except OSError:
            print("\tGot that OS error about deleting Git stuff. Life goes on.")
        #except WindowsError:
            #print("\tGot that standard Windows error about deleting Git stuff. Life goes on.")    
        print("\tAttempting to run post-processing script.")
        print("We need an upload script here, eh?")
        print("\tProcessing should be complete.")
    elif len(sys.argv) > 1 and sys.argv[1] == "webbuild":
        application.config.update(FREEZER_BASE_URL="/", FREEZER_RELATIVE_URLS=True)
        freezer.run(debug=True, host="0.0.0.0")
    else:
        application.config.update(FREEZER_BASE_URL="/", FREEZER_RELATIVE_URLS=True)
        application.run(debug=True, use_reloader=True, host="0.0.0.0")

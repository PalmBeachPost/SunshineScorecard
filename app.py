#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, render_template   # redirect, url_for, request are not used in this file
import requests
from flask_optimize import FlaskOptimize
from PIL import Image
from flask_frozen import Freezer

import os
import sys
from collections import OrderedDict
import uucsv
import csv

BUILDURL = "/projects/SunshineScorecard19" #for prod
#BUILDURL = "" #for dev
BASEURL = "https://content-static.naplesnews.com" + BUILDURL #for prod
#BASEURL = "localhost:8000" + BUILDURL #for dev
EDITION = "2019"
COUNTYDICT = {}
MASTERDICT = {}
LISTOFVOTES = []
DICTOFVOTES = {}
HIGHESTSCORE = 0
FLOORVOTEPOINTS = 3
COMMITTEEVOTEPOINTS = 3
SCORESDICT = {}
POTENTIALSCORESDICT = {}
MEMBERCOMMITTEESDICT = {}
IMGORIGINALPATH = "./static/imgoriginals/"
IMGTHUMBPATH = "./static/imgthumbs/"
TARGETWIDTH = 132
TARGETHEIGHT = 176
#BRACKETLU = {
    #0: "F--",
    #1: "F-", 2: "F", 3: "F+", 4: "D-", 5: "D", 6: "D+",
    #7: "C-", 8: "C", 9: "C+", 10: "B-", 11: "B", 12: "B+",
    #13: "A-", 14: "A", 15: "A+",
    #16: "A++"
    #}
BRACKETLU = {
    1: "F", 2: "D-", 3: "D", 4: "D+",
    5: "C-", 6: "C", 7: "C+", 8: "B-", 9: "B", 10: "B+",
    11: "A-", 12: "A", 13: "A+"
}
    #16: "A++"
    #}


application = Flask(__name__)
CONFIG_UPDATE = {'html': {'htmlmin': True, 'izip': False, 'cache': False},
                 'json': {'htmlmin': True, 'izip': False, 'cache': False},
                 'text': {'htmlmin': True, 'izip': False, 'cache': False}}

FLASK_OPTIMIZE = FlaskOptimize()
# flask_optimize = FlaskOptimize()
freezer = Freezer(application)


@application.route('/')
# @flask_optimize.optimize('html')
def index():
    template = 'index.html'
    global MASTERDICT
    global COUNTYDICT
    return render_template(template, masterdict=MASTERDICT, counties=COUNTYDICT, baseurl=BASEURL, buildurl=BUILDURL, edition=EDITION)

def bill_list():
    template = 'bill-list.html'
    global MASTERDICT
    return render_template(template, masterdict=MASTERDICT, baseurl=BASEURL, buildurl=BUILDURL, edition=EDITION)

@application.route('/scorecard/<slug>/')
# @flask_optimize.optimize('html')
def scorecard(slug):
    template = 'pol.html'
    global MASTERDICT
    for polslug in MASTERDICT:
        pol = MASTERDICT[polslug]
        if polslug == slug:
            return render_template(template, pol=pol, baseurl=BASEURL, buildurl=BUILDURL, edition=EDITION)

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
    lengthofrange = 2 * max #create full range, negative and positive
    spread = lengthofrange / 13.0 #divide that range into 15 parts
    # print(spread)
    brackets = []
    for i in range(0, 13):    # Get 15 results, 0-14 get 15 potential results
        target = 0 - max + (i * spread)
        brackets.append(target)
    brackets.append(1000.0)
    bracketnumber = sys.maxsize
    if instancevalue < (0 - max):         # If off the charts low, assign F
        bracketnumber = 1
    #elif instancevalue > max:               # If off the charts high, assign A++
        #bracketnumber = 16
    else:
        for i in range(0, 13):
            # print(str(i + 1) + ": " + str(brackets[i]))
            # print(str(instancevalue) + " instancevalue")
            # print("bracket range " + str(brackets[i]) + " to " + str(brackets[i+1]))
            if instancevalue >= brackets[i] and instancevalue < brackets[i+1]: #if actual score is greater than bracket score, and actual score is less than bracket score above it, then make that the bracket
                bracketnumber = i + 1   # Show brackets as 1-15 rather than 0-14
                # break
        if bracketnumber == sys.maxsize:
            print("Something broke on value" + str(instancevalue))
    return bracketnumber

# Call like this: bracket = get_bracket(maxvalue, person's score)


def structure_data():
    with open('pols2.csv', 'r') as csvfile:
        global pols
        global COUNTYDICT
        global MASTERDICT
        global LISTOFVOTES
        global DICTOFVOTES
        global HIGHESTSCORE
        global SCORESDICT
        global POTENTIALSCORESDICT
        global FLOORVOTEPOINTS
        global COMMITTEEVOTEPOINTS
        global MEMBERSCOMMITTEESDICT
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
                if pol['alphaname'] == "Rodriguez, Ana Maria":
                    pol['legname'] = "Rodriguez, A. M."
                if pol['legname'] == "Cortes, R.":
                    pol['legname'] = "Cortes, B."   # Robert goes by Bob, and wants his initials to go that way too.
                #if pol['legname'] == "Miller":
                    #pol['legname'] == "Miller, M."  
            if pol['alphaname'] == "Rodrigues, Ray Wesley":
                pol['legname'] = "Rodrigues, R."  
            for county in pol['counties'].split("|"):
                if county not in COUNTYDICT:
                    COUNTYDICT[county] = []
                COUNTYDICT[county].append(pol)
            MEMBERCOMMITTEESDICT[pol['chamber'] + '|' + pol['legname']] = {}
                
    COUNTYDICTsorted = OrderedDict()
    for county in sorted(COUNTYDICT):
        COUNTYDICTsorted[county] = COUNTYDICT[county]      # Use sorted list of keys to build ordered dictionary
    COUNTYDICT = COUNTYDICTsorted
    for county in COUNTYDICT:
        for pol in COUNTYDICT[county]:
            process_images(photourl=pol["photourl"], slug=pol["slug"])
    print(str(len(COUNTYDICTsorted)) + " counties found")
    with open('billlist2.csv', encoding='utf-8-sig') as billlistfile:  # Let's build a lookup table
        billlistreader = uucsv.UnicodeDictReader(billlistfile)
        sortedbillistreader = sorted(billlistreader)
        billlistreader = sortedbillistreader[0] #to remove extra outer list, not sure where the outer list came from
        sortedbillistreader = None
        billlu = {}       
        for row in billlistreader:
            billlu[row['billno']] = row
           
    csvmembers = []
    latevotes = []
    print("listofvotes size before data load: " + str(len(LISTOFVOTES)))
    with open('extracredits2.csv', 'r', encoding='utf-8-sig') as extrasfile:
        extrasreader = uucsv.UnicodeDictReader(extrasfile)
        sortedextrasreader = sorted(extrasreader)
        extrasreader = sortedextrasreader[0]
        sortedextrasreader = None
        
        for row in extrasreader:
            memberid = row['chamber'] + "|" + row['member']
            row['memberid'] = memberid

            LISTOFVOTES.append(row)
            csvmembers.append(memberid)

            if 'Late' in row['vote']:
                latevotes.append([memberid, row['billno']])

            if memberid not in SCORESDICT:
                SCORESDICT[memberid] = 0
            SCORESDICT[memberid] += int(row["points"])

            if memberid not in POTENTIALSCORESDICT:
                POTENTIALSCORESDICT[memberid] = 0
            if 'cmte vote' not in row:
                print("No 'cmte vote' field found in extrasreader")
            else:
                if row['cmte vote'] == "cmte vote":
                    POTENTIALSCORESDICT[memberid] += COMMITTEEVOTEPOINTS
                    if memberid not in MEMBERCOMMITTEESDICT:
                        print("Found " + memberid + " in extracredits2.csv, but didn't have that ID in master politican scrape.")
                    else:                    
                        MEMBERCOMMITTEESDICT[memberid][row['slug'][-3:]] = row['cmte name']

    print("listofvotes size after extracredits: " + str(len(LISTOFVOTES)))  

    with open('autovotes2.csv', 'r', encoding='utf-8-sig') as autovotesfile:
        autovotesreader = uucsv.UnicodeDictReader(autovotesfile)
        sortedautovotesreader = sorted(autovotesreader)
        autovotesreader = sortedautovotesreader[0] #to remove extra outer list, not sure where the outer list came from
        sortedautovotesreader = None
        
        for row in autovotesreader:
            memberid = row['chamber'] + "|" + row['member']
            row['memberid'] = memberid
            #remove missed votes if replaced by late vote
            if [memberid, row['billno']] not in latevotes:
                LISTOFVOTES.append(row)            
            csvmembers.append(memberid)
            if memberid not in SCORESDICT:
                SCORESDICT[memberid] = 0
            SCORESDICT[memberid] += int(row["points"])
            if memberid not in POTENTIALSCORESDICT:
                POTENTIALSCORESDICT[memberid] = 0
            POTENTIALSCORESDICT[memberid] += FLOORVOTEPOINTS    

    print("listofvotes size after autovotes: " + str(len(LISTOFVOTES)))

    for memberid in SCORESDICT:
        if HIGHESTSCORE < abs(SCORESDICT[memberid]):
            HIGHESTSCORE = abs(SCORESDICT[memberid])
    print("Highest score found: " + str(HIGHESTSCORE))
    

    for row in LISTOFVOTES:
        row['billnono'] = int(row['billno'][2:])
        row['description'] = billlu[row['billno']]['description']
        row['url'] = billlu[row['billno']]['url']
        if (row['billno'] == 'SB186') or (row['billno'] == 'SB342') or (row['billno'] =='HB1249'):
            row['billno'] = row['billno'] + ": " + row['chamber']
        elif row['billno'] == 'HB7124': #weird hack to get in bill with two floor votes
            row['billno'] = 'HB7125' + ": " + row['chamber'] + " Floor"
        elif row['billno'] == 'HB7125' and row['chamber'] == 'House':
            row['billno'] = 'HB7125' + ": " + row['chamber'] + " Floor (second vote)"
        else:
            row['billno'] = row['billno'] + ": " + row['chamber'] + " Floor"
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
                potentialscore = POTENTIALSCORESDICT[legid]
                committeesdict = MEMBERCOMMITTEESDICT[legid]
                # bracket = get_bracket(HIGHESTSCORE, numericscore)
                bracket = get_bracket(potentialscore, numericscore)
                lettergrade = BRACKETLU[bracket]
                COUNTYDICT[county][polindex]["numericscore"] = numericscore
                COUNTYDICT[county][polindex]["lettergrade"] = lettergrade
                COUNTYDICT[county][polindex]["potentialscore"] = potentialscore
                COUNTYDICT[county][polindex]["committeesdict"] = committeesdict
                exportset[legid] = [legid, pol['alphaname'], pol['chamber'], pol['party'], numericscore, potentialscore, bracket, lettergrade, pol['counties'], committeesdict]
                
                
    with open('report2.csv', 'w', newline='', encoding='utf-8-sig') as reportfile:
        # put = uucsv.UnicodeWriter(reportfile)
        put = csv.writer(reportfile)
        put.writerow(["legid", "alphaname", "chamber", "party", "numericscore", "potentialscore", "bracket", "lettergrade", "counties", "committesdict"])
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

#just finding legislature score total
#print("***Total score: " + str(get_bracket(3198, -963)))

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
        im.resize((TARGETWIDTH, TARGETHEIGHT), Image.LANCZOS).convert('RGB').save(thumb, optimize=True, quality=70)

    return


if __name__ == '__main__':
    print("Running structure_data")
    structure_data()
    generate_slugs()
    application.url_map.strict_slashes = False
    if (len(sys.argv) > 1) and (sys.argv[1] == "build"):
        application.config.update(FREEZER_RELATIVE_URLS=False, FREEZER_DESTINATION="../openflorida-frozen")
        # application.config.update(FREEZER_BASE_URL=BUILDURL, FREEZER_RELATIVE_URLS=False, FREEZER_DESTINATION="..\openflorida-frozen")
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
        freezer.run(debug=True, host="localhost")
    else:
        application.config.update(FREEZER_BASE_URL="/", FREEZER_RELATIVE_URLS=True)
        application.run(debug=True, use_reloader=True, host="0.0.0")

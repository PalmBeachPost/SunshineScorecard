#!/c:/python27/python
# -*- coding: utf-8 -*-
from flask import Flask, render_template, redirect, url_for, request   # External dependency
from flask_frozen import Freezer
from PIL import Image
import requests
import uucsv
from collections import OrderedDict
import os
import sys
from flask_optimize import FlaskOptimize

"""
Ideal to-do list:

-- Rebuild for Python 3
-- Rework data structure approach. This was ... not ... optimal.


"""


buildurl = "/SunshineScorecard17"     # Also need to patch in static/app.js at homeurl
baseurl = "http://apps.mypalmbeachpost.com" + buildurl
countydict = {}
masterdict = {}
listofvotes = []
dictofvotes = {}
highestscore = 0
scoresdict = {}
imgoriginalpath = u"./static/imgoriginals/"
imgthumbpath = u"./static/imgthumbs/"
targetwidth = 132
targetheight = 176
bracketlu = {
    1: "F-", 2: "F", 3: "F+", 4: "D-", 5: "D", 6: "D+",
    7: "C-", 8: "C", 9: "C+", 10: "B-", 11: "B", 12: "B+",
    13: "A-", 14: "A", 15: "A+"
    }


app = Flask(__name__)
config_update = {'html': {'htmlmin': True,  'izip': False, 'cache': False},
                            'json': {'htmlmin': True, 'izip': False, 'cache': False},
                            'text': {'htmlmin': True, 'izip': False, 'cache': False}}
flask_optimize = FlaskOptimize(config_update=config_update)
# flask_optimize = FlaskOptimize()
freezer = Freezer(app)


@app.route('/')
# @flask_optimize.optimize('html')
def index():
    template = 'index.html'
    global masterdict
    global countydict
    return render_template(template, masterdict=masterdict, counties=countydict, baseurl=baseurl)


@app.route('/scorecard/<slug>/')
# @flask_optimize.optimize('html')
def scorecard(slug):
    template = 'pol.html'
    global masterdict
    for polslug in masterdict:
        pol = masterdict[polslug]
        if polslug == slug:
            return render_template(template, pol=pol, baseurl=baseurl)


def get_neighbors(sourcelist, key):
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
    lengthofrange = 2*max
    spread = lengthofrange / 15.0
    # print(spread)
    brackets = []
    for i in range(0, 15):    # Get 15 results, 0-14
        target = 0 - max + (i * spread)
        brackets.append(target)
    brackets.append(1000.0)
    bracketnumber = sys.maxint
    for i in range(0, 15):
        # print(str(i + 1) + ": " + str(brackets[i]))
        # print(str(instancevalue) + " instancevalue")
        # print("bracket range " + str(brackets[i]) + " to " + str(brackets[i+1]))
        if instancevalue >= brackets[i] and instancevalue < brackets[i+1]:
            bracketnumber = i + 1   # Show brackets as 1-15 rather than 0-14
            # break
    if bracketnumber == sys.maxint:
        print("Something broke on value" + str(instancevalue))
    return bracketnumber

# Call like this: bracket = get_bracket(maxvalue, person's score)


def structure_data():
    with open('pols.csv', 'r') as csvfile:
        global pols
        global countydict
        global masterdict
        global listofvotes
        global dictofvotes
        global highestscore
        global scoresdict
        pols = list(uucsv.UnicodeDictReader(csvfile))
        sortedpols = sorted(pols, key=lambda k: k['alphaname'])
        pols = sortedpols
        sortedpols = None
        neighbortitles = get_neighbors(pols, "title")
        neighbornames = get_neighbors(pols, "name")
        neighborslugs = get_neighbors(pols, "slug")
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
                pol['legname'] = last.replace(u"NuÃ±ez", u"Nunez").replace(u"Nuñez", u"Nunez")
            else:
                pol['legname'] = last + ", " + pol['first'][0] + "."
                if pol['legname'] == "Cortes, R.":
                    pol['legname'] = "Cortes, B."   # Robert goes by Bob, and wants his initials to go that way too.
            for county in pol['counties'].split("|"):
                if county not in countydict:
                    countydict[county] = []
                countydict[county].append(pol)
    countydictsorted = OrderedDict()
    for county in sorted(countydict):
        countydictsorted[county] = countydict[county]      # Use sorted list of keys to build ordered dictionary
    countydict = countydictsorted
    for county in countydict:
        for pol in countydict[county]:
            process_images(photourl=pol["photourl"], slug=pol["slug"])
    print(str(len(countydictsorted)) + " counties found")
    with open('billlist.csv') as billlistfile:  # Let's build a lookup table
        billlistreader = uucsv.UnicodeDictReader(billlistfile)
        billlu = {}
        for row in billlistreader:
            billlu[row['billno']] = row
    csvmembers = []
    print("listofvotes size: " + str(len(listofvotes)))
    with open('autovotes.csv', 'r') as autovotesfile:
        autovotesreader = uucsv.UnicodeDictReader(autovotesfile)
        for row in autovotesreader:
            memberid = row['chamber'] + "|" + row['member'].replace(u"NuÃ±ez", u"Nunez").replace(u"Nuñez", u"Nunez")
            row['memberid'] = memberid
            listofvotes.append(row)
            csvmembers.append(memberid)
            if memberid not in scoresdict:
                scoresdict[memberid] = 0
            scoresdict[memberid] += int(row["points"])

    print("listofvotes size: " + str(len(listofvotes)))
    with open('extracredits.csv', 'r') as extrasfile:
        extrasreader = uucsv.UnicodeDictReader(extrasfile)
        for row in extrasreader:
            memberid = row['chamber'] + "|" + row['member'].replace(u"NuÃ±ez", u"Nunez").replace(u"Nuñez", u"Nunez")
            row['memberid'] = memberid
            listofvotes.append(row)
            csvmembers.append(memberid)
            if memberid not in scoresdict:
                scoresdict[memberid] = 0
            scoresdict[memberid] += int(row["points"])
    for memberid in scoresdict:
        if highestscore < abs(scoresdict[memberid]):
            highestscore = abs(scoresdict[memberid])
    print("Highest score found: " + str(highestscore))

    for row in listofvotes:
        if u'\ufeffbillno' in row:  # Horrible unicode workaround
            row['billno'] = row[u'\ufeffbillno']
        row["billnono"] = int(row["billno"][2:])
        row["description"] = billlu[row['billno']]['description']
        row["url"] = billlu[row['billno']]['url']
        if row["vote"] == "Y":
            row["vote"] = "Voted Yes"
        if row["vote"] == "N":
            row["vote"] = "Voted No"
        if row["vote"] == "-":
            row["vote"] = "Missed vote"
    exportset = {}  # because we needed more data structures
    for county in countydict:
        for polindex, pol in enumerate(countydict[county]):
            legid = pol['chamber'] + "|" + pol["legname"]
            if legid not in scoresdict:
                print("****************** Hey! Missing " + legid)
            else:
                numericscore = scoresdict[legid]
                bracket = get_bracket(highestscore, numericscore)
                lettergrade = bracketlu[bracket]
                # print(legname + ": score of " + str(numericscore) + " with grade " + lettergrade)
                # print(countydict[county])
                countydict[county][polindex]["numericscore"] = numericscore
                countydict[county][polindex]["lettergrade"] = lettergrade
                # print(legname + ": Score of " + lettergrade + " for " + str(numericscore))
                exportset[legid] = [legid, pol['alphaname'], pol['chamber'], pol['party'], str(numericscore), str(bracket), lettergrade, pol['counties']]
    
    with open('report.csv', 'wb') as reportfile:
        put = uucsv.UnicodeWriter(reportfile)
        put.writerow(["legid", "alphaname", "chamber", "party", "numericscore", "bracket", "lettergrade", "counties"])
        for pol in exportset:
            put.writerow(exportset[pol])
    temp = sorted(listofvotes, key=lambda row: row["billnono"])
    listofvotes = temp  # Sort by numerical part of bill number
    for row in listofvotes:  # Now, build a list keyed to each member
        memberid = row['memberid']
        # print(row['chamber'])
        if memberid not in dictofvotes:
            dictofvotes[memberid] = []
        dictofvotes[memberid].append(row)
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
    
    for county in countydict:        # build person-by-person dictionary.
        for pol in countydict[county]:
            legid = pol['chamber'] + "|" + pol["legname"]
            votes = dictofvotes[legid]
            pol["votes"] = votes
            masterdict[pol["slug"]] = pol
    return


@freezer.register_generator
def generate_slugs():
    yield "/"
    for pol in pols:
        yield "/scorecard/" + pol['slug'] + "/"
    return


def process_images(photourl, slug):
    global imgoriginalpath
    global imgthumbpath
    global targetheight
    global targetwidth
    filename = slug.encode("utf-8") + ".jpg".encode("utf-8")
    original = imgoriginalpath.encode("utf-8") + filename
    thumb = imgthumbpath.encode("utf-8") + filename
    for directory in (imgoriginalpath, imgthumbpath):   # Make photo folders if they don't exist
        if not os.path.exists(directory):
            os.makedirs(directory)
    if not os.path.exists(original):  # if we don't have the original photo
        print("\tDownloading image ...".encode("utf-8") + original)
        response = requests.get(photourl)   # download
        with open(original, 'wb') as f:
            f.write(response.content)   # save
    if not(os.path.exists(thumb)):
        print("\tBuilding thumbnail ...")
        im = Image.open(original)
        width, height = im.size
        im.resize((targetwidth, targetheight), Image.LANCZOS).convert('RGB').save(thumb, optimize=True)
    return


if __name__ == '__main__':
    structure_data()
    generate_slugs()
    app.url_map.strict_slashes = False
    if (len(sys.argv) > 1) and (sys.argv[1] == "build"):
        app.config.update(FREEZER_BASE_URL=buildurl, FREEZER_RELATIVE_URLS=False, FREEZER_DESTINATION="..\openflorida-frozen")
        try:
            freezer.freeze()
        except WindowsError:
            print("\tGot that standard Windows error about deleting Git stuff. Life goes on.")
        print("\tAttempting to run post-processing script.")
#        p = Popen("postbake.bat", cwd=r"d:\data\homicides")
#        stdout, stderr = p.communicate()
        print("We need an upload script here, eh?")
        print("\tProcessing should be complete.")
    elif len(sys.argv) > 1 and sys.argv[1] == "webbuild":
        app.config.update(FREEZER_BASE_URL="/", FREEZER_RELATIVE_URLS=True)
        freezer.run(debug=True, host="0.0.0.0")
    else:
        app.config.update(FREEZER_BASE_URL="/", FREEZER_RELATIVE_URLS=True)
        app.run(debug=True, use_reloader=True, host="0.0.0.0")

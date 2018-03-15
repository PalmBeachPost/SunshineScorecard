'''Makes pols.csv'''

# coding: utf-8
import re #place before import requests
from operator import itemgetter #place before import requests
import csv #place before import requests
import requests
from pyquery import PyQuery as pq
from nameparser import HumanName
from slugify import slugify #for python3 requirements module is now python-slugify, but keep from slugify import slugify

HOUSEURL = "http://www.myfloridahouse.gov/Sections/Representatives/representatives.aspx"
SENATEURL = "https://www.flsenate.gov/Senators"
HOUSEPRE = "http://www.myfloridahouse.gov"
SENATEPRE = "http://www.flsenate.gov"

REPLIST = []

SENATE = requests.get(SENATEURL).content
print("Processing senators ...")
SENATORS = pq(SENATE)("table#Senators")
for senator in pq(SENATORS)("tr")[1:-1]:
    countiesraw = pq(senator)("tr").attr('class')
    counties = "|".join(countiesraw.split()[1:])
    counties = counties.replace("St_", "St. ").replace("_", " ")
    personurl = SENATEPRE + pq(senator)("a").attr('href')
    alphaname = pq(senator)("a").text().replace(" , ", ", ").strip().replace("  ", " ") # Tried to fix Braynon, Oscar II
    alphaname = re.sub(r'\"\w+\"', '', alphaname).replace(" ,", " ")    # Kill off nicknames.
    alphaname = alphaname.replace(", MD, ", ", ")   # Sorry Dr. Ralph E. Massullo
    if alphaname == "Vacant":
        party = "vacant"
    else:
        if alphaname.split(", ")[1] == "Jr." or alphaname.split(", ")[1] == "Sr.":
            temp = alphaname.split(", ")
            alphaname = temp[0] + ", " + temp[2] + ", " + temp[1]
        party = pq(senator)("td")[1].text.strip()[:1]
    alphaname = re.sub(r'\s+', ' ', alphaname).replace(" , ", ", ")
    print("\t" + alphaname)
    district = pq(senator)("td")[0].text_content().strip()
    title = "Sen."
    chamber = "Senate"
    parsedname = HumanName(alphaname)
    first = parsedname.first
    last = parsedname.last
    middle = parsedname.middle
    suffix = parsedname.suffix
    if len(first) == 2: # fix for W. Travis
        first = first + " " + middle
        middle = ""
    name = first + " " + middle + " " + last + " " + suffix
    name = " ".join(name.split())       # Replace multiple spaces with one, via Jeremy Bowers and rdmurphy
    slug = slugify(title + " " + first + " " + last + " " + district)
    slug = slug.replace("NuÃ±ez", "Nunez").replace(u"Nuñez", "Nunez")
    slug = slug.lower()
    personhtml = requests.get(personurl).content
    biohtml = str(pq(personhtml)('div#sidebar'))
    m = re.search('(^.+?)(, FL )', biohtml, re.MULTILINE)
    city = m.group(1).strip()
    photourl = SENATEPRE + pq(biohtml)("img").attr('src')
    memberstuff = [alphaname, name, first, last, slug, title, chamber, personurl, photourl, district, party, city, counties]
    REPLIST.append(memberstuff)

HOUSE = requests.get(HOUSEURL).content
print("Processing representatives ...")
REPS = pq(pq(HOUSE)("div.rep_listing1"))
for rep in pq(REPS):
    title = "Rep."
    chamber = "House"
    district = pq(rep)("div")[1].text.strip()
    party = pq(rep)("div")[2].text.strip()
    
    if not party:
        continue

    alphaname = pq(pq(rep)("div")[3])("a").text()
    alphaname = re.sub(r'\"\w+\"', '', alphaname).replace(" ,", " ")    # Kill off nicknames.
    alphaname = alphaname.replace(", MD, ", ", ")   # Sorry Dr. Ralph E. Massullo
    alphaname = re.sub(r'\s+', ' ', alphaname).replace(" , ", ", ")
    if alphaname.split(", ")[1] == "Jr." or alphaname.split(", ")[1] == "Sr.":
        temp = alphaname.split(", ")
        alphaname = temp[0] + ", " + temp[2] + ", " + temp[1]
    alphaname = re.sub(r'\s+', ' ', alphaname).replace(" , ", ", ")
    print("\t" + alphaname)
    personurl = pq(pq(rep)("div")[3])("a").attr('href')
    m = re.search('(MemberId=)(\d+)(&)', personurl)
    memberno = m.group(2)
    photourl = HOUSEPRE + "/FileStores/Web/Imaging/Member/" + memberno + ".jpg"
    personurl = HOUSEPRE + personurl
    # name = alphaname.split(",")[1].strip() + " " + alphaname.split(",")[0].strip()
    parsedname = HumanName(alphaname)
    first = parsedname.first
    last = parsedname.last
    middle = parsedname.middle
    suffix = parsedname.    suffix
    if len(first) == 2: # fix for W. Travis
        first = first + " " + middle
        middle = ""
    name = first + " " + middle + " " + last + " " + suffix
    name = " ".join(name.split())       # Replace multiple spaces with one, via Jeremy Bowers and rdmurphy
    slug = slugify(title + " " + first + " " + last + " " + district)
    slug = slug.replace("NuÃ±ez", "Nunez").replace(u"Nuñez", "Nunez")
    slug = slug.lower()
    countiesraw = pq(rep)("div")[4].text_content().strip()
    # Here begins the ugly
    replacepairs = [
        (" and part of ", ", "),
        ("Part of ", ""),
        ("Parts of ", ""),
        (" and parts of ", ", ")
    ]
    for replacepair in replacepairs:
        rfrom, rto = replacepair
        countiesraw = countiesraw.replace(rfrom, rto)

    counties = countiesraw.split(",")

    for i, item in enumerate(counties):
        counties[i] = item.strip()
    counties = "|".join(counties)
    personhtml = requests.get(personurl).content
    biohtml = pq(personhtml)('div.r_MemberInfo')
    city = ""
    if pq(biohtml)("span")[0].text == "City of Residence:":
        city = pq(biohtml)("span")[1].text
    memberstuff = [alphaname, name, first, last, slug, title, chamber, personurl, photourl, district, party, city, counties]
    REPLIST.append(memberstuff)

# print REPLIST[:5]
print("Writing CSV.")
SORTEDREPS = sorted(REPLIST, key=itemgetter(0))   # Sort by last name then first, using alphaname field
with open('pols.csv', 'w', newline='') as f:
    WRITER = csv.writer(f)
    WRITER.writerow(["alphaname", "name", "first", "last", "slug", "title", "chamber", "personurl", "photourl", "district", "party", "city", "counties"])
    for row in SORTEDREPS:
        newrow = []
        for item in row:
            newrow.append(item)
        # writer.writerows(REPLIST)
        WRITER.writerow(newrow)

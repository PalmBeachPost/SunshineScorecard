# coding: utf-8

import requests
from pyquery import PyQuery as pq
import re
from operator import itemgetter
import csv
from nameparser import HumanName
from slugify import slugify

# To-do:
# Begin building photo scraper, resizer
# Clemons, Burgess in House -- name splits?

houseurl = "http://www.myfloridahouse.gov/Sections/Representatives/representatives.aspx"
senateurl = "https://www.flsenate.gov/Senators"
housepre = "http://www.myfloridahouse.gov"
senatepre = "http://www.flsenate.gov"

replist = []

senate = requests.get(senateurl).content
print("Processing senators ...")
senators = pq(senate)("table#Senators")
for senator in pq(senators)("tr")[1:-1]:
    countiesraw = pq(senator)("tr").attr('class')
    counties = "|".join(countiesraw.split()[1:])
    counties = counties.replace("St_", "St. ").replace("_", " ")
    personurl = senatepre + pq(senator)("a").attr('href')
    alphaname = pq(senator)("a").text().replace(" , ", ", ").strip().replace("  ", " ") # Tried to fix Braynon, Oscar  II 
    alphaname = re.sub(r'\"\w+\"', '', alphaname).replace(" ,", " ")    # Kill off nicknames.
    alphaname = alphaname.replace(", MD, ", ", ")   # Sorry Dr. Ralph E. Massullo
    if alphaname.split(", ")[1] == "Jr." or alphaname.split(", ")[1] == "Sr.":
        temp = alphaname.split(", ")
        alphaname = temp[0] + ", " + temp[2] + ", " + temp[1]
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
    party = pq(senator)("td")[1].text.strip()[:1]
    personhtml = requests.get(personurl).content
    biohtml = str(pq(personhtml)('div#sidebar'))
    m = re.search('(^.+?)(, FL )', biohtml, re.MULTILINE)
    city = m.group(1).strip()
    photourl = senatepre + pq(biohtml)("img").attr('src')
    memberstuff = [alphaname, name, first, last, slug, title, chamber, personurl, photourl, district, party, city, counties]
    replist.append(memberstuff)

house = requests.get(houseurl).content
print("Processing representatives ...")
reps = pq(pq(house)("div.rep_listing1"))
for rep in pq(reps):
    title = "Rep."
    chamber = "House"
    district = pq(rep)("div")[1].text.strip()
    party = pq(rep)("div")[2].text.strip()
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
    photourl = housepre + "/FileStores/Web/Imaging/Member/" + memberno + ".jpg"
    personurl = housepre + personurl
    # name = alphaname.split(",")[1].strip() + " " + alphaname.split(",")[0].strip()
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
    slug = slugify(title + " " + first + " " + last + " " + district).replace("NuÃ±ez", "Nunez").replace(u"Nuñez", "Nunez")
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
    replist.append(memberstuff)

# print replist[:5]
print("Writing CSV.")
sortedreps = sorted(replist, key=itemgetter(0))   # Sort by last name then first, using alphaname field
# print(sortedreps[:10])
with open('pols.csv', 'wb') as f:
    writer = csv.writer(f)
    writer.writerow(["alphaname", "name", "first", "last", "slug", "title", "chamber", "personurl", "photourl", "district", "party", "city", "counties"])
    for row in sortedreps:
        newrow = []
        for item in row:
            newrow.append(item.encode('utf-8'))
        # writer.writerows(replist)
        writer.writerow(newrow)

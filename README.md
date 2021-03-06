# SunshineScorecard

The initial commit here was used to build http://apps.mypalmbeachpost.com/SunshineScorecard17, a scorecard for legislators' votes on bills affecting government openness in Florida in 2017. The project was lead by The Palm Beach Post for the Florida Society of News Editors using bills identified by the Florida First Amendment Foundation.

Converted to Python 3. Here are the moving pieces:

-- votescraper.ipynb, which draws from billlist.csv. It attempt to pull regular voting history on a particular bill and generate scores for the bill. This creates autovotes.csv. It does not scrape late votes or sponsorships. This has been reworked to run in Python 3.

-- billlist.csv, basically a human-readable version of the wantedvotes variable that will be used to generate text for people to describe the bills. This now also feeds votescraper.ipynb. 

-- extracredits.csv, a human-generated tracking file that includes all the stuff autovotes.csv does not include -- bill sponsorships and cosponsorships, late votes, and credits for discussing the bill with the Florida First Amendment Foundation.

-- getpols.py, which downloads politicians' information and generates pols.csv, which contains a list of politicians. Of all the bad code in this project, this is probably the ugliest and hardest to maintain, even though it's a pretty simple scraper. Good enough was good enough.

-- app.py, the major heavy lifter here. This is a Python script for Flask and Frozen Flask, which basically takes the information from the other files and uses templates to generate the site. The data model here was also ... not ... optimal.

-- templates contains the templates for the Flask project. This is where the Madlibs get made.

-- static/imgoriginals is used to generate static/imgthumbs, which actually get posted to the site.

### Installation and usage

Clone the repo.

Create a virtual environment with Python3. Activate it.

pip install -r requirements.txt

### Drawbacks

Realize the correct version of Jupyter is missing from requirements, and possibly some other things

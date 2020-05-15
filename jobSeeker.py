from lxml import html
from itertools import chain
import time
import socket
import os
import webbrowser
import operator
from tqdm import tqdm
import json
import requests
import re
from collections import OrderedDict 
import math

query = "Software Developer"
short = False

def check(title, description, optionalInclude, optionalExclude, exclude, include):
	score = 0
	description = title + "\n" + description
	
	for optIncStr in optionalInclude:
		if optIncStr in description:
			score = score + optionalInclude[optIncStr]

		for optExtStr in optionalExclude:
			if optExtStr in description:
				score = score - optionalExclude[optExtStr]

		for ExStr in exclude:
			if ExStr.lower() in description:
				score -= 1000
		
		for InStr in include:
			if InStr.lower() not in description:
				score -= 1000
				
		# Gets list of all strings with 1-2 y, 1+ y, 6 y, 4-5+ y etc. from the description
		years = re.findall(r"(\d{1,}(-|–)\d{1,}(\+?)y)|(((^-)|(^–))?\d{1,}(\+?)y)", description.replace(' ', ''))
		yearss = years
		experience = -1
		if len(years) != 0:
			# nums = [int(s) for s in list(years[0][2]) if s.isdigit()]
			# nums = list(filter(lambda x: x != "", years)) # remove "" 's from lists
			# re.sub(r"(\+)|y", "", item
			
			nums = [list(filter(lambda x: x != "", match))[0] for match in years] # Removes empty strings and cleans up tuple list nesting
			nums = [re.sub(r"[\+y]", "", match).replace("–", "-").split("-") for match in nums] # Removes 'y's and '+'s, and parses each match to an array of str and also replaces "-" with "–"
			
			# This if else block is to try and gather a rough estimation of which number is the experience,
			# thus: a match like "1-5 years" is more likely to be an experience expectation than
			# "3+ years" which is more likely than "2 years" to be years of experience.
			if "-" in nums:
				nums = [x for x in nums if "-" in x][0]
			elif "+" in nums:
				nums = [x for x in nums if "+" in x][0]
			else:
				nums = nums[-1]
			
			# convert list of str to list of int
			nums = list(map(int, nums))
			
			# get an average of "3-5 years" as 4 or just 3 if "3 years"
			experience = sum(nums) / len(nums)
		
			# These calculations are pretty arbitrary saying that the less experience the better and the more - the worse
			if experience > 9: # Probably not an experience if they're asking for 9+ years so dont count
				experience = -1
				continue
			
			elif experience > 3:
				score = score - experience * 2
			
			else:
				score = score + 3 / experience
		
		return (score, title, experience) #if score > -50 else None

def parse(site):
	
	ListOfJobs = {}
	searchPage = {
		'seek': 'https://www.seek.com.au/jobs-in-information-communication-technology/in-Warranwood-VIC-3134?&salaryrange=40000-80000&salarytype=annual&subclassification=6287%2C6290%2C6299%2C6301%2C6302%2C6296',
		'indeed': 'https://au.indeed.com/jobs?as_and=software+developer&as_phr=%22Include%22&as_any=&as_not=Exclude&as_ttl=&as_cmp=&jt=all&st=&as_src=&salary=&radius=50&l=Ringwood+VIC+3134&fromage=any&limit=22&sort=&psf=advsrch&from=advancedsearch'
	}
	searchPage = requests.get(searchPage[site])
	searchTree = html.fromstring(searchPage.content)
	
	if site == "seek":
		numJobs = int(searchTree.xpath('//*[@data-automation="totalJobsCount"]/text()')[0]),
		numJobs = numJobs[0]
	elif site == "indeed":
		numJobs = int(searchTree.xpath('//*[@id="searchCountPages"]/text()')[0].split()[-2])
	else:
		print("Site identifier error!")
		exit()
	
	jobsPerPage = {
		'seek': 22,
		'indeed': 22
	
	}[site]
	print("Number of Jobs found: " + str(numJobs))
	with tqdm(total=numJobs if not short else jobsPerPage) as pbar: 
		numPages = math.ceil(float(numJobs)/jobsPerPage)
		
		for page in range(numPages):
			searchPage = {
				'seek': 'https://www.seek.com.au/jobs-in-information-communication-technology/in-Warranwood-VIC-3134?page=' + str(page) + '&salaryrange=40000-80000&salarytype=annual&subclassification=6287%2C6290%2C6299%2C6301%2C6302%2C6296',
				'indeed': 'https://au.indeed.com/jobs?q=software+developer&l=Ringwood+VIC+3134&limit=22&radius=50&start=' + str(page * jobsPerPage)
			}
			
			searchPage = requests.get(searchPage[site])
			searchTree = html.fromstring(searchPage.content)
			
			titles = searchTree.xpath({
				'seek': '//a[@data-automation="jobTitle"]/text()',
				'indeed': '//div[contains(@class, "jobsearch-SerpJobCard") and not(@data-ci)]/h2/a/@title'
			}[site])
			
			ids = searchTree.xpath({
				'seek': '//@data-job-id',
				'indeed': '//div[contains(@class, "jobsearch-SerpJobCard")]/@data-jk'
			}[site])
			
			for i, title in enumerate(titles):
				titles[i] = re.sub(r"/|\n|\)|\(|\\", ' ', title) # replaces: / \n ) ( \
			
			for ID in ids:
				pbar.update(1)
				
				url = {
					'seek': "https://www.seek.com.au/job/",
					'indeed': "https://au.indeed.com/viewjob?jk="
				}[site] + ID
				
				jobPage = requests.get(url)
				
				jobTree = html.fromstring(jobPage.content)
				
				description = ''.join(jobTree.xpath({
					'seek': '//*[@data-automation="jobDescription"]/descendant::*/text()',
					'indeed': '//*[@id="jobDescriptionText"]/descendant::*/text()'
				}[site])).lower()
				
				description = re.sub(r'\.|,|:|\n|\)|\(|\\', ' ', description) # replaces: / \n ) ( \ . , :, 
				
				try:
					title = jobTree.xpath({
						'seek': '//span[@data-automation="job-detail-title"]/span/h1/text()',
						'indeed': '//h3[contains(@class, "jobsearch-JobInfoHeader-title")]/text()'
					}[site])[0]
				
				except Exception as e:
					print("ERROR: ")
					print(str(jobTree.xpath({
						'seek': '//span[@data-automation="job-detail-title"]/span/h1/text()',
						'indeed': '//h3[contains(@class, "jobsearch-JobInfoHeader-title")]/text()'
					}[site])))
				
				
				job = check(title, description, *getFilter())
				
				if job != None:
					ListOfJobs[ID] = (*job, site, url, description)
					# ListOfJobs[ID] has format:
					# ListOfJobs[ID] = (
					#										score, 			[0]
					#										title, 			[1]
					#										experience,	[2]
					#										siteName, 	[3]
					#										url					[4]
					#										description [5]
					#										 )
				
			if short:
				break
		
	return ListOfJobs

def getFilter():
	
	with open(os.path.dirname(os.path.realpath(__file__)) + "/filter.json", "r") as f:
		Filter = json.load(f)
		
	Inc = Filter["INCLUDE"]
	Exc = Filter["EXCLUDE"]
	OptExc = Filter["OPTIONAL_EXCLUDE"]
	OptInc = Filter["OPTIONAL_INCLUDE"]
	return (OptInc, OptExc, Exc, Inc)

def writeToHTML(jobs):
	file = os.path.dirname(os.path.realpath(__file__)) + "/jobs.html"
	htmlfile = open(file,"w+")
	htmlfile.write("<style>th{border-top:1px solid black;border-bottom:1px solid black;}</style>")
	htmlfile.write("<table style='text-align:left;font-family:verdana;'>")
	htmlfile.write("<tr style='font-size:18pt;text-align:center;'><th>Score</th><th>Title</th><th>Link</th><th>Years of Experience</th><th>ID</th></tr>")
	for ID in jobs:
			htmlfile.write("<tr>")
			htmlfile.write("<th>" + str(jobs[ID][0]) + "</th>")
			htmlfile.write("<th>" + str(jobs[ID][1]) + "</th>")
			htmlfile.write("<th>" + "<a href='" + str(jobs[ID][4]) + "'>" + str(jobs[ID][3]) + "</a>" + "</th>")
			htmlfile.write("<th style='text-align:center;'>" + ("" if jobs[ID][2] == -1 else str(jobs[ID][2])) + "</th>")
			htmlfile.write("<th>" + str(ID) + "</th>")
			htmlfile.write("</tr>")
	htmlfile.write("</table>")
	htmlfile.close()

def outputJobsToJson(jobs):
	jsonJobs = {}

	for ID in jobs:
		j = [{"title" : jobs[ID][1],
					"score" : jobs[ID][0],
					"url" : jobs[ID][4],
					"site" : jobs[ID][3],
					"description" : jobs[ID][5],
				}]
		
		if jobs[ID][2] > -1:
			j[0]["experience"] = jobs[ID][2]
		
		jsonJobs[ID] = j

	jsonJobsFile = open(os.path.dirname(os.path.realpath(__file__)) + "/jobs.json", "w+")
	jsonJobsFile.write(json.dumps(jsonJobs, indent=2))
	jsonJobsFile.close()

def clearScr():
	print(chr(27)+'[2j')
	print('\033c')
	print('\x1bc')


while 1:
	clearScr()
	jobsList = OrderedDict()
	print("Search for jobs -> HTML: 1")
	print("View HTML: 2")
	print("Exit: 0")
	
	response = input("> ")
	
	if response == "1":
		
		jobsList = OrderedDict(chain(jobsList.items(), parse("seek").items()))
		jobsList = OrderedDict(chain(jobsList.items(), parse("indeed").items()))

		jobsList = OrderedDict(sorted(jobsList.items(), key=lambda x: x[1][0]))


		outputJobsToJson(jobsList)

		writeToHTML(jobsList)
		
	elif response == "2":
		print("file://" + os.path.dirname(os.path.realpath(__file__)).replace("/mnt/c", "c:/") + ("/jobs.html"))
		print("")
		webbrowser.open_new('file://' + os.path.dirname(os.path.realpath(__file__)).replace("/mnt/g", "g:/") + ("/jobs.html"))
		
	elif response == "0":
		exit()
		
	else:
		clearScr()
		print("Invalid input!")
		time.sleep(1.5)
		

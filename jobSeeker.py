from lxml import html
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

outputfile = "jobs.html"
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
				
		# Gets list of all strings with 1-2 years, 1+ year, 6 year, 4-5+ years etc.
		years = re.findall(r"((^-?)[1-9]+?.year)|([1-9]-[1-9].?.year)|(^-?)[1-9]\+.year", description)
		experience = -1
		if len(years) != 0:
			nums = [int(s) for s in list(years[0][2]) if s.isdigit()]
			experience = sum(nums) / len(nums)
		
		if experience > 3:
			score = score - experience * 2
			
		elif experience != -1:
			score = score + 3 / experience

		for years in range(10):
			re.search("", description)
		
		return (score, title, experience) if score > -50 else None

def parse(site):
	
	ListOfJobs = {}
	searchPage = requests.get({
		'seek': 'https://www.seek.com.au/jobs-in-information-communication-technology/in-Warranwood-VIC-3134?&salaryrange=40000-80000&salarytype=annual&subclassification=6287%2C6290%2C6299%2C6301%2C6302%2C6296',
		'indeed': 'https://au.indeed.com/jobs?as_and=software+developer&as_phr=%22Include%22&as_any=&as_not=Exclude&as_ttl=&as_cmp=&jt=all&st=&as_src=&salary=&radius=100&l=Ringwood+VIC+3134&fromage=any&limit=100&sort=&psf=advsrch&from=advancedsearch'
	}[site])
	
	searchTree = html.fromstring(searchPage.content)
	
	if site == "seek":
		numJobs = searchTree.xpath('//*[@data-autsomation="totalJobsCount"]/text()')[0],
	elif site == "indeed":
		numJobs = searchTree.xpath('//*[@id="searchCountPages"]/text()')[0].split()[-2]
	else:
		print("Site identifier error!")
		exit()
	
	numJobs = int(numJobs)
	
	# numJobs = searchTree.xpath({
	# 	'seek' : '//*[@data-automation="totalJobsCount"]/text()',
	# 	'indeed':'#searchCountPages/text()'
	# }[site])
	
	jobsPerPage = {
		'seek': 22,
		'indeed': 100
	}[site]
	
	with tqdm(total=int(numJobs) if not short else jobsPerPage) as pbar: 
		numPages = math.ceil(float(numJobs)/jobsPerPage)
		
		for page in range(numPages):
			titles = searchTree.xpath({
				'seek': '//a[@data-automation="jobTitle"]/text()',
				# 'indeed': '//a[contains(@class, "jobtitle")]/@title' #E$###
				# 'indeed': '//h2[@class="title"]/span'
				# 'indeed': '//span[@class="new"]'
				# 'indeed': '//span[@class="new"]/*'
				'indeed': '//div[contains(@class, "jobsearch-SerpJobCard") and not(@data-ci)]/h2/a/@title'
			}[site])
			
			ids = searchTree.xpath({
				'seek': '//@data-job-id',
				'indeed': '//div[contains(@class, "jobsearch-SerpJobCard")]/@data-jk'
			}[site])
			
			for i, title in enumerate(titles):
				titles[i] = re.sub(r"/|\n|\)|\(|\\", ' ', title) # replaces: / \n ) ( \
			
			for ID in ids:
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
				
				title = jobTree.xpath({
					'seek': '//span[@data-automation="job-detail-title"]/span/h1/text()',
					'indeed': '//h3[contains(@class, "jobsearch-JobInfoHeader-title")]/text()'
				}[site])[0]
				
				job = check(title, description, *getFilter())
				
				pbar.update(1)
				
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
	with open("filter.json", "r") as f:
		Filter = json.load(f)
		
	Inc = Filter["INCLUDE"]
	Exc = Filter["EXCLUDE"]
	OptExc = Filter["OPTIONAL_EXCLUDE"]
	OptInc = Filter["OPTIONAL_INCLUDE"]
	return (OptInc, OptExc, Exc, Inc)

def writeToHTML(jobs, file):
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



jobsList = OrderedDict()
jobsList.update(parse("indeed"))
jobsList.update(parse("seek"))

jobsList = OrderedDict(sorted(jobsList.items(), key=lambda x: x[1][0]))


jsonJobs = {}

for ID in jobsList:
	j = [{"title" : jobsList[ID][1],
				"score" : jobsList[ID][0],
				"url" : jobsList[ID][4],
				"site" : jobsList[ID][3],
				"description" : jobsList[ID][5],
			}]
	
	if jobsList[ID][2] > -1:
		j[0]["experience"] = jobsList[ID][2]
	
	jsonJobs[ID] = j

jsonJobsFile = open("jobs.json", "w+")
jsonJobsFile.write(json.dumps(jsonJobs, indent=2))
jsonJobsFile.close()

exit()

writeToHTML(jobsList, outputfile)

webbrowser.open_new(os.path.abspath("jobs.html").replace("/mnt/c", "c:/"))










# searchPage = requests.get('https://www.seek.com.au/jobs-in-information-communication-technology/in-Warranwood-VIC-3134?page=' + str(i) + '&salaryrange=40000-80000&salarytype=annual&subclassification=6287%2C6290%2C6299%2C6301%2C6302%2C6296')
	
	# searchTree = html.fromstring(searchPage.content)
	
	# jobs = searchTree.xpath('//a[@data-automation="jobTitle"]/text()')
	# ids = searchTree.xpath('//@data-job-id')
	
	# # (include, exclude, optionalExclude, optionalInclude) = getFilter()
	
	# for ID in (ids):
	# 	jobPage = requests.get("https://www.seek.com.au/job/" + ID)
	# 	jobTree = html.fromstring(jobPage.content)
	# 	description = ''.join(jobTree.xpath('//*[@data-automation="jobDescription"]/descendant::*/text()')).lower()
	# 	title = jobTree.xpath('//span[@data-automation="job-detail-title"]/span/h1/text()')[0]
		
	# 	job = check(description)
	# 	if job != None:
	# 		jobsList[ID] = job
			
	# 	pbar.update(1)
	# if short:
	# 	break



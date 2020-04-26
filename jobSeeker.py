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

def check(description):
    score = 0
    for optIncStr in optionalInclude:
        if optIncStr in description:
            score = score + optionalInclude[optIncStr]

        for optExtStr in optionalExclude:
            if optExtStr in description:
                score = score - optionalExclude[optExtStr]

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
        for ExStr in exclude:
            if ExStr.lower() in description:
                score -= 1000
        
        for InStr in include:
            if InStr.lower() not in description:
                score -= 1000
        
        if score > -50:
            return (score, title, experience)
        else:
            return None
        

query = "Software Developer"
short = True
skip = True

if skip == False:
    searchPage = requests.get('https://www.seek.com.au/' + query.replace(' ', '-') + '-jobs/in-Warranwood-VIC-3134/full-time?salaryrange=40000-80000&salarytype=annual')
    searchTree = html.fromstring(searchPage.content)

    jobsList = OrderedDict()

    numjobs = searchTree.xpath('//*[@data-automation="totalJobsCount"]/text()')[0]
    with tqdm(total=int(numjobs)) as pbar:
        numPages = int(math.ceil(float(numjobs))/22.0)
        for i in range(numPages):
            searchPage = requests.get('https://www.seek.com.au/jobs-in-information-communication-technology/in-Warranwood-VIC-3134?page=' + str(i) + '&salaryrange=40000-80000&salarytype=annual&subclassification=6287%2C6290%2C6299%2C6301%2C6302%2C6296')
            
            searchTree = html.fromstring(searchPage.content)
            
            jobs = searchTree.xpath('//a[@data-automation="jobTitle"]/text()')
            ids = searchTree.xpath('//@data-job-id')
            
            exclude = []
            include = []
            optionalInclude =  {"junior"        : 5, 
                                "graduate"      : 3, 
                                "git"           : 1, 
                                "Android"       : 3, 
                                "UWP"           : 5, 
                                "Agile"         : 2, 
                                "AWS"           : 2,
                                "Javascript"    : 6, 
                                "Word"          : 9, 
                                "Excel"         : 9, 
                                "KiCad"         : 7, 
                                "AutoCAD"       : 2, 
                                "C#"            : 3, 
                                "Java"          : 4, 
                                "Linux"         : 6, 
                                "HTML"          : 7, 
                                "CSS"           : 7, 
                                "JS"            : 7,  
                                "jQuery"        : 8, 
                                "PHP"           : 8, 
                                "MySQL"         : 7, 
                                "XML"           : 8, 
                                "Unix"          : 5, 
                                "Kotlin"        : 7, 
                                "R"             : 7, 
                                "Python"        : 5, 
                                "C++"           : 5, 
                                "Batch"         : 5, 
                                "Julia"         : 1}
            optionalExclude =  {"ASP.NET"       : 6, 
                                "MVC"           : 8,  
                                "Senior"        : 10, 
                                "Experienced"   : 4,
                                "PostgreSQL"    : 10, 
                                "Magneto"       : 8, 
                                "degree"        : 3,
                                "bachelor"      : 3}
            for ID in (ids):
                jobPage = requests.get("https://www.seek.com.au/job/" + ID)
                jobTree = html.fromstring(jobPage.content)
                description = ''.join(jobTree.xpath('//*[@data-automation="jobDescription"]/descendant::*/text()')).lower()
                title = jobTree.xpath('//span[@data-automation="job-detail-title"]/span/h1/text()')[0]
                
                job = check(description)
                if job != None:
                    jobsList[ID] = job
                    
                pbar.update(1)
            if short:
                break
            
        
    jobsList = OrderedDict(sorted(jobsList.items(), key=lambda x: x[1][0]))

    htmlfile = open("jobs.html","w+")
    htmlfile.write("<table style='text-align:left;'>")
    htmlfile.write("<tr style='font-size:18pt;text-align:center;'><th>Score</th><th>Title</th><th>Link</th><th>Years of Experience</th></tr>")
    for k in jobsList:
        htmlfile.write("<tr>")
        htmlfile.write("<th>" + str(jobsList[k][0]) + "</th>")
        htmlfile.write("<th>" + str(jobsList[k][1]) + "</th>")
        htmlfile.write("<th>" + "<a href='http://seek.com.au/job/" + str(k) + "'>" + str(k) + "</a>" + "</th>")
        htmlfile.write("<th style='text-align:center;'>" + ("" if jobsList[k][2] == -1 else str(jobsList[k][2])) + "</th>")
        htmlfile.write("</tr>")
    htmlfile.write("</table>")
    htmlfile.close()

    webbrowser.open_new(os.path.abspath("jobs.html").replace("/mnt/c", "c:/"))
    # for k, v in jobsList:
    #     webbrowser.open_new_tab("http://seek.com.au/job/" + k)

publisher = "123412341234123"
options = ["format=json", "l=3134", "radius=40", "jt=fulltime", "co=au", "q=" + query, ]

options = '&'.join(options)
indeedJson = requests.get("https://api.indeed.com/ads/apisearch?publisher=" + publisher + "&v=1&useragent=Mozilla&userip=" + socket.gethostbyname(socket.gethostname()) + options)

print(indeedJson.content)
exit()
indeedJson = json.loads(indeedJson.content)

print(indeedJson['totalResults'])


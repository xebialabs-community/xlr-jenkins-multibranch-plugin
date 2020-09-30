#
# Copyright 2020 XEBIALABS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import sys
import urllib
from com.xebialabs.xlrelease.plugin.webhook import JsonPathResult
import urlparse

"""
Calls Jenkins API in order to know if a job expects parameters
When expecting a parameter named "param", the JSON looks like:

    "actions" : [
        {
            "parameterDefinitions" : [
                {
                    "defaultParameterValue" : {
                        "name" : "param",
                        "value" : ""
                    },
                    "description" : "",
                    "name" : "param",
                    "type" : "StringParameterDefinition"
                }
            ]
        }
    ]

In last versions of Jenkins the parameters are defined in "property" field, leaving "actions" for old versions
"""
def isJobParameterized(request, jobContext, headers):
    jobInfo = request.get(jobContext + 'api/json', contentType='application/json', headers=headers)
    jobProperties = JsonPathResult(jobInfo.response, 'property').get()
    if jobProperties is not None:
        for prop in jobProperties:
            if (prop is not None and 'parameterDefinitions' in prop):
                return True

    jobActions = JsonPathResult(jobInfo.response, 'actions').get()
    if jobActions is not None:
        for action in jobActions:
            if (action is not None and 'parameterDefinitions' in action):
                return True

    return False

"""
With an input that looks like:
param1=value 1\n
param2=value 2\n

Produces: ?param1=value%201&param2=value%202 to be used as a query string
"""
def buildQueryString(params):
    if (params is not None):
        queryParams = []
        for param in params.splitlines():
            if param:
                tokens = param.split('=', 1)
                queryParams.append(tokens[0] + "=" + urllib.quote(tokens[1]))
        return "?" + "&".join(queryParams)
    else:
        return ""

def get_headers(request):
    # CSRF Protection
    response = request.get('crumbIssuer/api/json')
    if response.isSuccessful():
        crumb = JsonPathResult(response.response, 'crumb').get()
        return {'Jenkins-Crumb': crumb}
    else:
        return None


if jenkinsServer is None:
    print "No server provided."
    sys.exit(1)

jenkinsURL = jenkinsServer['url']
jobContext = '/job/' + urllib.quote(jobName) + '/'

request = HttpRequest(jenkinsServer, username, password)
headers = get_headers(request)

response = request.get(jobContext + 'api/json', contentType='application/json')
if response.isSuccessful():
    jobClass = JsonPathResult(response.response, '_class').get()

    if not "WorkflowMultiBranchProject" in jobClass:
        print "Job %s is not a multibranch project. Please use the other Jenkins task to manage it" % (jenkinsURL + jobContext)
        sys.exit(1)
    else:
        # WorkflowMultiBranchProject : true
        # print response.response
        # print jobClass

        jobs = JsonPathResult(response.response,'jobs').get()
        for job in jobs:
            if job['name'] == branch:
                jobUrl = job['url']
                print "job url is  %s" % (jobUrl)

        jobUrl = jobUrl.replace(jenkinsURL,'')
        buildContext = jobUrl.replace(jenkinsURL,'')

        if isJobParameterized(request, jobContext, headers):
            buildContext = buildContext + 'buildWithParameters' + buildQueryString(jobParameters)
        else:
            buildContext = buildContext + 'build'

        print "build url %s" % buildContext
        buildResponse = request.post(buildContext, '', contentType='application/json', headers=headers)
       

        if not buildResponse.getStatus() in [200, 201, 202]:           
            print "Unable to create the build request. Please check the parameters and job name."      
            print buildResponse.getStatus()         
            print buildResponse.getHeaders()
            print buildResponse.response           
            sys.exit(1)

        # query the location header which gives a queue item position (more reliable for retrieving the correct job later)
        location = None        
        if 'Location' in buildResponse.getHeaders() and '/queue/item/' in buildResponse.getHeaders()['Location']:
            location = '/queue/item/' + filter(None, buildResponse.getHeaders()['Location'].split('/'))[-1] + '/'
            print "location : {0}".format(location)

        task.setStatusLine("Build queued")
        task.schedule("jenkins/multibranch/Build.wait-for-queue.py")
else:
    print "Failed to connect at %s." % (jenkinsURL + jobContext)
    response.errorDump()
    sys.exit(1)
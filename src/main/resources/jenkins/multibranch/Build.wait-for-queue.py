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

"""
Print a nicely formatted build started message
"""
def notifyBuildStarted(jenkinsURL, jobContext, jobName, jobBuildNumber):
    jenkinsJobURL = jenkinsURL + jobContext + str(jobBuildNumber)
    print "Started [%s #%s](%s) - view [Console Output](%s)" % (jobName, jobBuildNumber, jenkinsJobURL, jenkinsJobURL + '/console')
    task.setStatusLine("Running build #%s" % jobBuildNumber)
    task.schedule("jenkins/multibranch/Build.wait-for-build.py")


jenkinsURL = jenkinsServer['url']
jobContext = jobUrl.replace(jenkinsURL,'')
request = HttpRequest(jenkinsServer, username, password)

if location:
    # check the response to make sure we have an item
    print "location is {0}".format(jobContext)
    response = request.get(location + 'api/json', contentType = 'application/json')
    if response.isSuccessful():
        # if we have been given a build number this item is no longer in the queue but is being built
        buildNumber = JsonPathResult(response.response, 'executable.number').get()
        if buildNumber:
            notifyBuildStarted(jenkinsURL, jobContext, jobName, buildNumber)
        else:
            task.schedule("jenkins/multibranch/Build.wait-for-queue.py")

    else:
        print "Could not determine build number for queued build at %s." % (jenkinsURL + location + 'api/json')
        sys.exit(1)

else:
    
    print "jobContext is {0}".format(jobContext)
    # fallback to the unreliable check because old jenkins(<1.561) does not populate the Location header
    response = request.get(jobContext + 'api/json', contentType = 'application/json')
    # response.inQueue is a boolean set to True if a job has been queued
    inQueue = JsonPathResult(response.response, 'inQueue').get()
    if inQueue:
        task.schedule("jenkins/multibranch/Build.wait-for-queue.py")
    else:
        buildNumber = JsonPathResult(response.response, 'lastBuild.number').get()
        notifyBuildStarted(jenkinsURL, jobContext, jobName, buildNumber)

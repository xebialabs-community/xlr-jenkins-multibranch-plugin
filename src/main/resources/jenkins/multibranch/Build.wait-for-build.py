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
from com.xebialabs.xlrelease.reports.excel import ExcelSheetWriter
from java.io import IOException
from java.lang import RuntimeException
from java.util import Date
from org.joda.time import Duration
from org.joda.time import PeriodType

import json


def addBuildRecord(response):
    buildData = json.loads(response)
    displayName = buildData.get('displayName', '')
    fullDisplayName = buildData.get('fullDisplayName', '')
    buildRecord = taskReportingApi.newBuildRecord()
    buildRecord.targetId = task.id
    buildRecord.project = fullDisplayName.replace(' {}'.format(displayName), '')
    buildRecord.build = 'Build ' + displayName
    buildRecord.build_url = buildData.get('url')
    buildRecord.serverUrl = jenkinsServer['url']
    buildRecord.serverUser = username or jenkinsServer['username']
    buildRecord.outcome = buildData.get('result', None)
    buildRecord.startDate = Date(long(buildData.get('timestamp')))
    buildRecord.endDate = Date(long(buildData.get('timestamp') + buildData.get('duration')))
    buildRecord.duration = ExcelSheetWriter.PERIOD_FORMATTER.print(Duration.millis(buildData.get('duration')).toPeriod().normalizedStandard(PeriodType.dayTime()))

    taskReportingApi.addRecord(buildRecord, True)


def finishPolling(buildStatus):
    print "\nFinished: %s" % buildStatus
    jenkinsJobURL = jenkinsURL + jobContext + str(buildNumber)
    task.setStatusLine("[Build #%s](%s)" % (str(buildNumber), jenkinsJobURL))
    if buildStatus != 'SUCCESS':
        task.schedule("jenkins/multibranch/Build.fail.py")


jenkinsURL = jenkinsServer['url']
request = HttpRequest(jenkinsServer, username, password)
jobContext = jobUrl.replace(jenkinsURL,'')
response = None
buildStatus = None
try:
    fullJobContext =  jobContext + str(buildNumber) + '/api/json'
    print("fullJobContext  {0}".format(fullJobContext))

    response = request.get(fullJobContext, contentType='application/json')
    if response.isSuccessful():
        buildStatus = JsonPathResult(response.response, 'result').get()
        duration = JsonPathResult(response.response, 'duration').get()
        if buildStatus and duration != 0:
            try:
                addBuildRecord(response.response)
            except RuntimeException as e:
                print "\nCould not add 'Build' attribute: %s\n" % str(e)
            except Exception as e:
                print "\nCould not add 'Build' attribute: %s\n" % str(e)
            finishPolling(buildStatus)
        else:
            task.schedule("jenkins/multibranch/Build.wait-for-build.py")
    else:
        print "\nFailed to check the job status. Received an error from the Jenkins server: `%s`" % response.response
        task.schedule("jenkins/multibranch/Build.wait-for-build.py")

except IOException as error:
    print "\nFailed to check the job status due to connection problems. Will retry in the next polling run. Error details: `%s`" % error
    task.schedule("jenkins/multibranch/Build.wait-for-build.py")

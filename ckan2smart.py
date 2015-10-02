import ssl
import sys
import requests
import json
import logging

# disable ssl checks
requests.packages.urllib3.disable_warnings()
# disable all ssl checks
context = ssl._create_unverified_context()
# disable moar ssl checks
ssl._create_default_https_context = ssl._create_unverified_context

import flask
import ckanclient

# This restores the same behavior as before.
#
API_KEY = 'my-api-key'
CKAN_URL = 'my-ckan-url'
ckan = ckanclient.CkanClient(base_location=CKAN_URL, api_key=API_KEY)

# start the web server
app = flask.Flask(__name__)

# configure logging to stdout
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# add logger to web server
app.logger.addHandler(ch)


def showAsJson(elem):
    return flask.Response(json.dumps(elem), mimetype='application/json')


# default route @homepage
@app.route('/')
def hello_world():
    # Return hello world
    return 'Hello World!'


# list datasets of ckan
@app.route('/v0/datasets')
def datasets():
    # get all datasets
    package_list = ckan.package_register_get()
    # Return as application/json
    return showAsJson(package_list)


# list all devices from all datasets
@app.route('/v0/devices')
def devices():
    # get all datasets
    package_list = ckan.package_register_get()
    # we add here all the points to show
    responseObjects = []
    # for all datasets available
    for package in package_list:
        print "Dataset:" + package
        try:
            # Get the Dataset description
            headers = {'Authorization': API_KEY}
            r = requests.get(url=CKAN_URL+"/rest/dataset/" + package, headers=headers, verify=False)
            # convert the response to json
            jsonResponse = json.loads(r.text);
            # get the format of the dataset
            format = jsonResponse['resources'][0]['format']
            # for now we care only about ngsi10
            if format == 'ngsi10':
                try:
                    # get the download url
                    downloadUrl = jsonResponse['resources'][0]['url']
                    print downloadUrl
                    # get the query payload
                    payload = jsonResponse['resources'][0]['payload']
                    print payload
                    # make the request
                    r = requests.post(url=downloadUrl,
                                      headers={"Content-type": "application/json", "Accept": "application/json"},
                                      data=payload, verify=False)
                    print r.status_code
                    # check the response code
                    if r.status_code == 200:
                        # convert the response to a json object
                        queryContextResponse = json.loads(r.text);
                        contextResponses = queryContextResponse['contextResponses']
                        # append the response object to the full device list
                        for contextElement in contextResponses:
                            # TODO: here you need to convert the contextElement to a smartCitizentElement
                            smartCitizentElement = conventContextElement(contextElement)
                            responseObjects.append(smartCitizentElement)
                except requests.HTTPError, e:
                    print 'HTTP ERROR %s occured' % e.code
                except requests.ConnectionError, e:
                    print 'Connection Error %s occured' % e
        except requests.HTTPError, e:
            print 'HTTP ERROR %s occured' % e.code
    # Return as application/json
    return showAsJson(responseObjects)


@app.route('/tags')
def tags():
    # get all ckan tags
    return showAsJson(ckan.tag_register_get())


if __name__ == '__main__':
    app.run()


# TODO: here you need to convert the contextElement to a smartCitizentElement
def conventContextElement(contextElement):
    return contextElement

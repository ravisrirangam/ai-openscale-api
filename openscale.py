import sys,os,os.path
import warnings
warnings.filterwarnings('ignore')
from ibm_ai_openscale import APIClient4ICP
from ibm_ai_openscale.engines import *
from ibm_ai_openscale.utils import *
from ibm_ai_openscale.supporting_classes import PayloadRecord, Feature
from ibm_ai_openscale.supporting_classes.enums import *

import pandas as pd
import requests
from ibm_ai_openscale.utils import get_instance_guid
from functools import wraps

from flask import Flask, jsonify, request, abort, Response
import json
import urllib3, requests
from flask_cors import CORS, cross_origin

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    if request.method == 'OPTIONS':
        response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT'
        headers = request.headers.get('Access-Control-Request-Headers')
        if headers:
            response.headers['Access-Control-Allow-Headers'] = headers
    return response


app = Flask(__name__)
CORS(app)

def limit_content_length(max_length):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            cl = request.content_length
            if cl is not None and cl > max_length:
                abort(413)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def getScoringId(subscriptionid):
    WOS_CREDENTIALS = {
        "username": 123,
        "password": 456,
        "url": "https://cpdga-appdomain.cloud"
    }
    #return "a123"
    ai_client = APIClient4ICP(WOS_CREDENTIALS)
    subscription = ai_client.data_mart.subscriptions.get(subscriptionid)
    txn = subscription.payload_logging.get_table_content(limit=5)
    transaction_id = txn['scoring_id'].values[0]
    return transaction_id


def explain(subscriptionid, transactionid):
    WOS_CREDENTIALS = {
        "username": 123,
        "password": 456,
        "url": "https://cpdga.appdomain.cloud"
    }
    ai_client = APIClient4ICP(WOS_CREDENTIALS)
    subscription = ai_client.data_mart.subscriptions.get(subscriptionid)
    explain_run = subscription.explainability.run(transaction_id=transactionid, background_mode=False, cem=False)
    explain_result = None
    if explain_run == None:
        time.sleep(10)
        explain_table = subscription.explainability.get_table_content(format='pandas')
        explain_result = pd.DataFrame.from_dict(explain_table[explain_table['transaction_id']==transactionid]['explanation'][0]['entity']['predictions'][0]['explanation_features'])
    else:
        explain_result = pd.DataFrame.from_dict(explain_run['entity']['predictions'][0]['explanation_features'])
        out = explain_result.to_json()
    return out

@app.route('/')
def Welcome():
	return 'Welcome to OpenScale API app running on CP4D'

@app.route('/getscoringid', methods=['POST'])
@limit_content_length(10 * 1024 * 1024)
def get_scoring_id():
    req = request.json
    jj = json.dumps(req)
    parsedjson = json.loads(jj)
    subid = parsedjson["subscriptionid"]
    #print(subid)
    scoringid = getScoringId(subid)
    mydict = {}
    mydict["scoringid"] = scoringid
    r = json.dumps(mydict)
    return Response(r, mimetype='application/json')

@app.route('/explain', methods=['POST'])
@limit_content_length(10 * 1024 * 1024)
def getExplainResults():
    req = request.json
    jj = json.dumps(req)
    parsedjson = json.loads(jj)
    subid = parsedjson["subscriptionid"]
    txnid = parsedjson["transactionid"]
    out = explain(subid, txnid)
    print(out)
    return Response(out, mimetype='application/json')


port = os.getenv('VCAP_APP_PORT', '5000')
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=int(port))

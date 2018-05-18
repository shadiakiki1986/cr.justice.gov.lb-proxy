from flask import Flask, jsonify, request, send_file, render_template
import os
import requests
import requests_cache
import json
from io import BytesIO
import pandas as pd
import datetime as dt
from flask_bootstrap import Bootstrap
import time
from scrapy_cr_justice_gov_lb.pipelines import ScrapyCrJusticeGovLbPipeline


requests_cache.install_cache(cache_name='scrapyrt_cache', backend='sqlite', expire_after=1*60*60) # expires in 1 hour

BASE_CRJUSTICE = "http://cr.justice.gov.lb/search"

app = Flask(__name__)
Bootstrap(app)

# https://stackoverflow.com/a/25352191/4126114
pd.set_option('display.max_colwidth', -1)

# GET vs POST functionality
# e.g. https://realpython.com/caching-external-api-requests/
@app.route('/')
def hello():
    """
    Requires env var SCRAPYRT, URL to scrapyrt server
    Supports GET params
    - use_sample .. instead of using actual scrapyrt output, use sample published at s3
    - register_number/register_place .. pair of info to be sent to spider
    - format .. valid values are "json" or "xlsx"

    Example
      curl http://localhost:3000
      curl http://localhost:3000/?use_sample=true&format=json&
      curl http://localhost:3000/?use_sample=true&format=xlsx
      curl http://localhost:3000/?use_sample=true&format=
    """
        
    scrapyrt_url = os.getenv("SCRAPYRT", None)
    if scrapyrt_url is None:
      return "Configure env var SCRAPYRT, e.g. http://localhost:3000"

    # return 'Hello World!'
    
    # get GET parameters
    # http://docs.python-requests.org/en/master/
    use_sample = request.args.get('use_sample', default=False, type=bool)
    register_number = request.args.get('register_number', default=None, type=str)
    register_place = request.args.get('register_place', default=None, type=str)
    requested_format = request.args.get('format', default="html", type=str)
    
    # get POST parameters
    # https://realpython.com/caching-external-api-requests/
    # use_sample = request.form.get('use_sample', default=False, type=bool)
    # register_number = request.form.get('register_number', default=None, type=str)
    # register_place = request.form.get('register_place', default=None, type=str)        
    # requested_format = request.form.get('format', default="html", type=str)

    if use_sample:
      url_sample = 'https://s3-us-west-2.amazonaws.com/keras-models-factory/scrapy-crjusticegovlb-scrapyrt-sample.json'
      response = requests.get(url_sample)
      register_number = 66942
      register_place = "Mount Lebanon"
      #time.sleep(2)
    else:
      # check xor http://stackoverflow.com/questions/432842/ddg#433161
      if bool(register_number) != bool(register_place):
        return "Must set both register_number and register_place"

      if not (bool(register_number) and bool(register_place)):
        return render_template('app.html', df_html=None, register_number=None, register_place=None)
    
      df_in = [{"register_number": register_number, "register_place": register_place}]
      payload = {"request":{"url": "http://example.com", "meta": {"df_in": df_in}}, "spider_name": "cr_justice_gov_lb_single"}
      response = requests.post('%s/crawl.json'%scrapyrt_url, data=json.dumps(payload))
      #return json.loads(response.content.decode())

    if requested_format=='json':
      return jsonify(response.json())

    df_out = pd.DataFrame(response.json()['items'])

    # send to spider pipeline .. scrapyrt doesnt do this
    pipeline = ScrapyCrJusticeGovLbPipeline()
    pipeline.df = df_out.copy()
    pipeline.close_spider(None)
    df_out = pipeline.df

    if df_out.shape[0]==0:
      return render_template('app.html', df_html='No results found', register_number=register_number, register_place=register_place)


    # postprocess details_url
    df_out['details_url'] = df_out['details_url'].apply(
      lambda x: "<a href='%s/%s'target='_blank'>Details</a>"%(BASE_CRJUSTICE, x)
    )

    if requested_format=='xlsx':
      output = BytesIO()
      writer = pd.ExcelWriter(output)
      df_out.to_excel(writer, sheet_name="main")
      writer.save()
      output.seek(0)
      fn = 'crjusticegovlb_%s.xlsx'
      dt_ff = "%Y%m%d_%H%M%S_UTC"
      dt_suffix = dt.datetime.strftime(dt.datetime.utcnow(), dt_ff)
      fn = fn%dt_suffix
      return send_file(output, attachment_filename=fn, as_attachment=True)
  

    df_html = df_out.to_html(classes='table', escape=False)


    return render_template('app.html', df_html=df_html, register_number=register_number, register_place=register_place)


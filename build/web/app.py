from flask import Flask, flash, jsonify, request, send_file, render_template, redirect, send_from_directory
import os
import requests
import requests_cache
import json
from io import BytesIO
import pandas as pd
import datetime as dt
from flask_bootstrap import Bootstrap
from scrapy_cr_justice_gov_lb.pipelines import ScrapyCrJusticeGovLbPipeline


requests_cache.install_cache(cache_name='scrapyrt_cache', backend='sqlite', expire_after=1*60*60) # expires in 1 hour

BASE_CRJUSTICE = "http://cr.justice.gov.lb/search"
DT_FF = "%Y%m%d_%H%M%S_UTC"

app = Flask(__name__)
Bootstrap(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = 'super secret key'

ALLOWED_EXTENSIONS = set(['xlsx'])

# https://stackoverflow.com/a/25352191/4126114
pd.set_option('display.max_colwidth', -1)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    
# GET vs POST functionality
# e.g. https://realpython.com/caching-external-api-requests/
# File upload
# http://flask.pocoo.org/docs/0.12/patterns/fileuploads/
@app.route('/', methods=['GET', 'POST'])
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
        
    SCRAPYRT_URL = os.getenv("SCRAPYRT", None)
    if SCRAPYRT_URL is None:
      return "Configure env var SCRAPYRT, e.g. http://localhost:3000"

    # return 'Hello World!'
    
    # defaults
    uploaded_file = None
    use_sample = False
    register_number = None
    register_place = None
    requested_format = "html"
    
    if request.method == 'GET':
        # get GET parameters
        # http://docs.python-requests.org/en/master/
        use_sample = request.args.get('use_sample', default=False, type=bool)
        register_number = request.args.get('register_number', default=None, type=str)
        register_place = request.args.get('register_place', default=None, type=str)
        requested_format = request.args.get('format', default="html", type=str)

        if use_sample:
          url_sample = 'https://s3-us-west-2.amazonaws.com/keras-models-factory/scrapy-crjusticegovlb-scrapyrt-sample.json'
          register_number = 66942
          register_place = "Mount Lebanon"
          response = requests.get(url_sample)
        else:
          # check xor http://stackoverflow.com/questions/432842/ddg#433161
          if bool(register_number) != bool(register_place):
            flash("Must set both register_number and register_place")
            return redirect(request.url)

          if not (bool(register_number) and bool(register_place)):
            return render_template('app.html', df_html=None, register_number=None, register_place=None)

          df_in = [{"register_number": register_number, "register_place": register_place}]
          payload = {"request":{"url": "http://example.com", "meta": {"df_in": df_in}}, "spider_name": "cr_justice_gov_lb_single"}
          response = requests.post('%s/crawl.json'%SCRAPYRT_URL, data=json.dumps(payload))
          #return json.loads(response.content.decode())
    
    else:
        # get POST parameters
        # https://realpython.com/caching-external-api-requests/
        # use_sample = request.form.get('use_sample', default=False, type=bool)
        # register_number = request.form.get('register_number', default=None, type=str)
        # register_place = request.form.get('register_place', default=None, type=str)        
        requested_format = request.form.get('format', default="html", type=str)

        # upload file
        # http://flask.pocoo.org/docs/0.12/patterns/fileuploads/
        if 'uploaded_file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        uploaded_file = request.files['uploaded_file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if uploaded_file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if not(uploaded_file and allowed_file(uploaded_file.filename)):
            flash("Cant upload for some reason. Contact admin")
            return redirect(request.url)
            
        # filename = secure_filename(uploaded_file.filename)
        dt_suffix = dt.datetime.strftime(dt.datetime.utcnow(), DT_FF)
        filename = "upload_%s.xlsx"%dt_suffix
        UPLOAD_FOLDER = os.path.join("/", "tmp")
        dest_file = os.path.join(UPLOAD_FOLDER, filename)
        uploaded_file.save(dest_file)

        df_in = pd.read_excel(dest_file)
        for required_field in ['register_number', 'register_place']:
            if not required_field in df_in.columns:
                flash("Missing column: %s"%required_field)
                return redirect(request.url)

        # limit columns
        df_in = df_in[['register_number', 'register_place']]
        
        # convert to string
        df_in['register_number'] = df_in['register_number'].apply(lambda x: str(x))
        
        # convert to dict
        df_in = df_in.to_json(orient='records')
        df_in = json.loads(df_in)
        
        # send to scrapyrt
        payload = {"request":{"url": "http://example.com", "meta": {"df_in": df_in}}, "spider_name": "cr_justice_gov_lb_single"}
        response = requests.post('%s/crawl.json'%SCRAPYRT_URL, data=json.dumps(payload))



    if requested_format=='json':
      return jsonify(response.json())

    df_out = pd.DataFrame(response.json()['items'])

    # send to spider pipeline .. scrapyrt doesnt do this
    pipeline = ScrapyCrJusticeGovLbPipeline()
    pipeline.df = df_out.copy()
    pipeline.close_spider(None)
    df_out = pipeline.df

    if df_out.shape[0]==0:
      # return render_template('app.html', df_html='No results found', register_number=register_number, register_place=register_place)
      flash('No results found')
      return redirect(request.url)


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
      dt_suffix = dt.datetime.strftime(dt.datetime.utcnow(), DT_FF)
      fn = fn%dt_suffix
      return send_file(output, attachment_filename=fn, as_attachment=True)
  

    # escape=False for displaying html anchor in td
    df_html = df_out.to_html(classes='table', escape=False, index=False)


    return render_template('app.html', df_html=df_html, register_number=register_number, register_place=register_place)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/example_file', methods=['GET'])
def example_file():
    return send_from_directory(BASE_DIR, 'df_in_sample.xlsx')

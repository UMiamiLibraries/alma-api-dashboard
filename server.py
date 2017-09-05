import requests
from bs4 import BeautifulSoup
from lxml import etree
from flask import Flask, render_template, request
app = Flask(__name__)

#global variables
apikey = ''

@app.route('/')
def index():
  return render_template('form.html')

@app.route('/submit-new-user/', methods=['POST'])
def SubmitNewUser():
    print("*******creating new user*******")
	
    #get data from flask request object
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    u_username = request.form['primary_id']
    u_password = request.form['password']

    #define user xml object
    user_xml = etree.fromstring('<?xml version="1.0"?><user><record_type desc="Public">PUBLIC</record_type><primary_id></primary_id><first_name></first_name><last_name></last_name><full_name></full_name><user_group desc="Special Collections">SPECCOLL</user_group><preferred_language desc="English">en</preferred_language><account_type desc="Internal">INTERNAL</account_type><external_id></external_id><password></password><force_password_change>true</force_password_change><status desc="Active">ACTIVE</status><contact_info><emails><email preferred="true" segment_type="Internal"><email_address></email_address><email_types><email_type desc="personal">personal</email_type></email_types></email></emails></contact_info><user_roles><user_role><status desc="Active">ACTIVE</status><scope desc="University of Miami">01UOML_INST</scope><role_type desc="Patron">200</role_type></user_role></user_roles></user>')
    
    #inject user data into user xml object
    primary_id = user_xml.findall(".//primary_id")
    primary_id[0].text = u_username
    first_name = user_xml.findall(".//first_name")
    first_name[0].text = fname
    last_name = user_xml.findall(".//last_name")
    last_name[0].text = lname
    full_name = user_xml.findall(".//full_name")
    full_name[0].text = fname + ' ' + lname
    email_address = user_xml.findall(".//email_address")
    email_address[0].text = email
    password = user_xml.findall(".//password")
    password[0].text = u_password
   
    #define request parameters
    url = 'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/users?social_authentication=false&send_pin_number_letter=false'
    user = etree.tostring(user_xml)
    print(user)
    headers = {'Content-Type': 'application/xml'}
    payload = {'apikey' : apikey}
    
    #create request url
    response = requests.post(url, headers=headers, params=payload, data=user)
    print(response.url)
    #print("***" + response.url + "***")
    root = etree.fromstring(response.content)
    soup = str(BeautifulSoup(etree.tostring(root), 'lxml'))
    print(soup)
    names = root.findall(".//full_name")
    try:
	    name = names[0].text
    except IndexError:
        return render_template("error_create.html", full_name=full_name)
    return render_template("user_create.html", name=name)
    
@app.route('/lookup-user/', methods=['POST'])
def LookupUser():
    print("*******searching for user*******")
    userid = request.form['userid']

    #create search parameters
    payload = {'apikey' : apikey,}
    url = 'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/users/' + userid + '?'
    response = requests.get(url, params=payload)
    #print("***" + response.url + "***")
    root = etree.fromstring(response.content)
    soup = str(BeautifulSoup(etree.tostring(root), 'lxml'))
    names = root.findall(".//full_name")
    emails = root.findall(".//email_address")
    name = ""
    email = ""
    try:
        name = names[0].text
        email = emails[0].text
    except IndexError:
        return render_template("error_search.html", userid=userid)
    return render_template("user_search.html", name=name, email=email)
	
if __name__ == '__main__':
    app.run(debug=True)
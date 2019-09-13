import requests
from bs4 import BeautifulSoup
from lxml import etree
from flask import Flask, render_template, request
import config
import time

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/submit-new-user/', methods=['POST'])
def submitnewuser():
    # get data from flask request object
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    u_username = request.form['primary_id']
    u_password = request.form['password']

    # define user xml object
    user_xml = etree.fromstring('<?xml version="1.0"?><user><record_type desc="Public">PUBLIC</record_type><primary_id></primary_id><first_name></first_name><last_name></last_name><full_name></full_name><user_group desc="Special Collections">SPECCOLL</user_group><preferred_language desc="English">en</preferred_language><account_type desc="Internal">INTERNAL</account_type><external_id></external_id><password></password><force_password_change>true</force_password_change><status desc="Active">ACTIVE</status><contact_info><emails><email preferred="true" segment_type="Internal"><email_address></email_address><email_types><email_type desc="personal">personal</email_type></email_types></email></emails></contact_info><user_roles><user_role><status desc="Active">ACTIVE</status><scope desc="University of Miami">01UOML_INST</scope><role_type desc="Patron">200</role_type></user_role></user_roles></user>')
    
    # inject user data into user xml object
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
   
    # define request parameters
    url = 'https://api-eu.hosted.exlibrisgroup.com/almaws/v1/users?social_authentication=false&send_pin_number_letter=false'
    user = etree.tostring(user_xml)
    print(user)
    headers = {'Content-Type': 'application/xml'}
    payload = {'apikey' : config.apikey}
    
    # create request url
    response = requests.post(url, headers=headers, params=payload, data=user)
    root = etree.fromstring(response.content)
    soup = str(BeautifulSoup(etree.tostring(root), 'lxml'))
    names = root.findall(".//full_name")
    try:
	    name = names[0].text
    except IndexError:
        return render_template("error_create.html", full_name=full_name)
    return render_template("user_create.html", name=name)


@app.route('/users/', methods=['GET', 'POST'])
def lookupuser():
    if request.method == 'GET':
        return render_template('users.html')
    else:
        print("*******searching for user*******")
        userid = request.form['userid']

        #create search parameters
        payload = {'apikey' : config.apikey}
        url = 'https://api-na.hosted.exlibrisgroup.com/almaws/v1/users/' + userid + '?'
        response = requests.get(url, params=payload)
        root = etree.fromstring(response.content)
        names = root.findall(".//full_name")
        emails = root.findall(".//email_address")
        try:
            name = names[0].text
            email = emails[0].text
        except IndexError:
            return render_template("user_search.html", userid=userid, error="true")
        return render_template("user_search.html", name=name, email=email, error="false")


@app.route('/sets/', methods=['GET', 'POST'])
def getsetcontents():
    if request.method == 'GET':
        return render_template("sets.html")
    else:
        setid = request.form['setid']
        payload = {'apikey': config.apikey}
        url = 'https://api-na.hosted.exlibrisgroup.com/almaws/v1/conf/sets/' + setid + '/members?'
        response = requests.get(url, params=payload)
        root = etree.fromstring(response.content)
        memberids = root.findall(".//member")
        setmembers = []
        for member in memberids:
            response = requests.get(member.attrib['link'], params=payload)
            root = etree.fromstring(response.content)
            setmember = [root.find(".//title").text, root.find(".//copy_id").text, root.find(".//temp_location").text]
            response = requests.get(member.attrib['link'] + '/loans', params=payload)
            root = etree.fromstring(response.content)
            setmember.append(root.find(".//user_id").text)
            setmember.append(root.find(".//due_date").text)
            setmembers.append(setmember)

        return render_template("set_results.html", setmembers=setmembers)


@app.route('/courses/', methods=['GET', 'POST'])
def courses():
    return render_template('courses.html')

# TODO: make the ate the day before
@app.route('/hours/', methods=['GET', 'POST'])
def hours():
    if request.method == 'GET':
        return render_template("hours.html")
    else:
        library_code = request.form['library']
        payload = {'apikey': config.apikey}
        url = 'https://api-na.hosted.exlibrisgroup.com/almaws/v1/conf/libraries/' + library_code + '/open-hours?'
        response = requests.get(url, params=payload)
        root = etree.fromstring(response.content)
        days = root.findall(".//day")
        calendar = []
        for day in days:
            day_of_week= day.find(".//day_of_week").attrib['desc']
            date = day.find(".//date").text[:-1]
            try:
                hours = day.findall(".//from")[-1].text + " - " + day.findall(".//to")[-1].text
            except IndexError:
                hours = "Closed"
            new_day = [day_of_week, date, hours]
            calendar.append(new_day)

        return render_template("hour_results.html", calendar=calendar, library=library_code)


@app.route('/flip-to-external/', methods=['GET', 'POST'])
def fliptoexternal():
    if request.method == 'GET':
        return render_template('flip_to_external.html')
    else:
        headers = {'Content-Type': 'application/xml'}
        payload = {'apikey': config.apikey}
        userids = request.form['userids'].splitlines()
        successusers = []
        failusers = []
        for userid in userids:
            url = 'https://api-na.hosted.exlibrisgroup.com/almaws/v1/users/' + userid.strip() + '?'
            response = requests.get(url, params=payload)
            root = etree.fromstring(response.content)
            try:
                name = root.find(".//full_name").text
                if root.find(".//account_type").text != 'EXTERNAL':
                    root.find(".//account_type").attrib['desc'] = 'External'
                    root.find(".//account_type").text = 'EXTERNAL'
                    root.find(".//external_id").text = 'SISEMP'
                    requests.put(url, headers=headers, params=payload, data=etree.tostring(root))
                    successusers.append([name, userid])
                else:
                    failusers.append([name, userid + " is already external"])
            except AttributeError:
                failusers.append([name, userid])
        return render_template("flip_to_external_results.html", successusers=successusers, failusers=failusers, userids=userids)


if __name__ == '__main__':
    app.run(debug=True)


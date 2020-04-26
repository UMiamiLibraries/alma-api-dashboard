import requests
from lxml import etree
from flask import Flask, render_template, request
from flask_basicauth import BasicAuth
import config

app = Flask(__name__)

app.config['BASIC_AUTH_USERNAME'] = config.username
app.config['BASIC_AUTH_PASSWORD'] = config.password
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)


@app.route('/')
def index():
    return render_template('index.html', view="home")


@app.route('/createuser/', methods=['POST'])
def submitnewuser():
    # get data from flask request object
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    u_username = request.form['primary_id']
    u_password = request.form['password']

    # TODO: use e-factory
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
    url = config.users
    user = etree.tostring(user_xml)
    print(user)
    headers = {'Content-Type': 'application/xml'}
    payload = {'apikey': config.apikey, 'social_authentication': 'false', 'send_pin_number_letter': 'false'}
    
    # create request url
    response = requests.post(url, headers=headers, params=payload, data=user)
    root = etree.fromstring(response.content)
    names = root.findall(".//full_name")
    try:
        name = names[0].text
    except IndexError:
        return render_template("error_create.html", full_name=full_name)
    return render_template("user_create.html", name=name)


@app.route('/users/', methods=['GET', 'POST'])
def users():
    if request.method == 'GET':
        return render_template('users.html')
    else:
        print("*******searching for user*******")
        userid = request.form['userid']
        payload = {'apikey': config.apikey}
        url = config.user.format(userid=userid)
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
def sets():
    if request.method == 'GET':
        return render_template("sets.html", method=request.method)
    else:
        setid = request.form['setid']
        payload = {'apikey': config.apikey}
        url = config.sets.format(setid=setid)
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
        return render_template("sets.html", setmembers=setmembers, method=request.method)


@app.route('/courses/', methods=['GET', 'POST'])
def courses():
    return render_template('courses.html')


# TODO: make the date the day before
@app.route('/hours/', methods=['GET', 'POST'])
def hours():
    if request.method == 'GET':
        return render_template("hours.html", method=request.method)
    else:
        library_code = request.form['library']
        payload = {'apikey': config.apikey}
        url = config.hours.format(library_code=library_code)
        response = requests.get(url, params=payload)
        root = etree.fromstring(response.content)
        days = root.findall(".//day")
        calendar = []
        for day in days:
            day_of_week  = day.find(".//day_of_week").attrib['desc']
            date = day.find(".//date").text[:-1]
            try:
                hours = day.findall(".//from")[-1].text + " - " + day.findall(".//to")[-1].text
            except IndexError:
                hours = "Closed"
            new_day = [day_of_week, date, hours]
            calendar.append(new_day)

        return render_template("hours.html", method=request.method, calendar=calendar, library=library_code)


@app.route('/flip-to-external/', methods=['GET', 'POST'])
def fliptoexternal():
    if request.method == 'GET':
        return render_template('flip_to_external.html', method=request.method)
    else:
        headers = {'Content-Type': 'application/xml'}
        payload = {'apikey': config.apikey}
        userids = request.form['userids'].splitlines()
        successusers = []
        failusers = []
        for userid in userids:
            url = config.user.format(userid=userid.strip())
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
                failusers.append(userid)
        return render_template("flip_to_external.html", method=request.method, successusers=successusers,
                               failusers=failusers, userids=userids)


@app.route('/primopermalink/', methods=['GET', 'POST'])
def primopermalink():
    if request.method == 'GET':
        return render_template('permalink.html', method=request.method)
    else:
        mmsid = request.form['mmsid']
        if not mmsid:
            return render_template("permalink.html", method="request.method", permalink="empty link")
        else:
            payload = {'apikey': config.apikey,
                       'vid': config.vid,
                       'scope': config.scope,
                       'inst': config.inst,
                       'tab': config.tab,
                       'q': "any,exact," + mmsid}
            url = config.primo
            response = requests.get(url, params=payload)
            jsonrecord = response.json()
            recordid = (jsonrecord["docs"][0]["pnx"]["search"]["recordid"])[0]
            permalink = config.primolink.format(recordid=recordid, vid=config.vid, scope=config.scope, tab=config.tab)
            return render_template("permalink.html", method=request.method, permalink=permalink)


def converthour(time):
    hour = int(time.split(" ")[0][0:2])
    if hour > 12:
        hour = hour - 12
        time = str(hour) + time[2:5] + " PM " + time[9:]
    else:
        time = time[2:] + " AM "
    return time


if __name__ == '__main__':
    app.run(debug=True)


# alma api dashboard

web app calling [alma api](https://developers.exlibrisgroup.com/alma/apis/). currently supports:
* creating and searching for users by id
* flipping users to external status (hidden)
* displaying set contents
* retrieving library hours
* primo permalink generator

## specs

front end built using [bootstrap](https://getbootstrap.com/). 

back end using [flask python framework](https://flask.palletsprojects.com/en/1.1.x/).

## setup
/path/to/development.conf

/path/to/alma-api-dashboard <br>
-----server.py <br>
-----config.py <br>
-----almaapidashboard.wsgi <br>
-----templates/ <br>
-----static/ (optional for images) <br>

config.py should include api key, api urls and unique institution data.
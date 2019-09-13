# dashboard

web app calling [alma api](https://developers.exlibrisgroup.com/alma/apis/). currently supports:
* creating and searching for users by id
* flipping users to external status (hidden)
* displaying set contents
* retrieving library hours

## specs

front end built using [bootstrap](https://getbootstrap.com/). 

back end using [flask python framework](https://flask.palletsprojects.com/en/1.1.x/).

## setup
/subversion/www/html/conf.d/development.conf

/subversion/www/html/devel/dev-non-svn/alma-api-dashboard <br>
-----server.py <br>
-----config.py <br>
-----alma_api_dashboard.wsgi <br>
-----templates/ <br>

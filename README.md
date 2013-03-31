# connectstrava

**IMPORTANT**
This is currently under active development.  Use with caution.

The connectstrava project is designed to synchronize activities (e.g. rides) from Garmin Connect with
Strava.  It is a very basic piece of software and makes several assumptions.

## Dependencies
 
* Python 2.6+.  (This is intended to work with Python 3, but is being developed on Python 2.x)
* Setuptools/Distribute
* Virtualenv 

## Installation 

Here are some instructions for setting up a development environment, which is the only real way to "install" this
at this juncture.

Note that this package uses [stravalib](https://github.com/hozn/stravalib) for the Strava interactions.  Since
stravalib is currently under active development, it must be installed into the virtualenv.

	shell$ git clone https://github.com/hozn/connectstrava.git
	shell$ git clone https://github.com/hozn/stravalib.git
	shell$ cd connectstrava
	shell$ python -m virtualenv --no-site-packages --distribute env
	shell$ source env/bin/activate
	(env) shell$ cd ../stravalib
	(env) shell$ python setup.py develop
	(env) shell$ cd ../connectstrava
    (env) shell$ python setup.py develop

We will assume for all subsequent shell examples that you are running in that activated virtualenv.  (This is denoted by using 
the "(env) shell$" prefix before shell commands.)    


## Configuration
   
Start by copying the example config file and filling in the values for your Garmin Connect and Strava credentials.

  shell$ cp settings.cfg.example settings.cfg
 
... And edit:

```
[main]
database_path = /path/to/sync.db 

gc.username = my-username
gc.password = my-password

strava.username = my-strava-email@example.com
strava.password = my-strava-password
```

## Initialize the Database

Before you can sync rides, you need to initialize the database with the last (most recent) activity in Garmin Connect
that has *already* been uploaded to Strava.

You can see the ID for an activity in the URL when you view the activity details.
For example http://connect.garmin.com/activity/12345

(These instructions assume you have the virtualenv setup, per instructions above and a valid configuration.)

	shell$ cd /path/to/connectstrava
	shell$ env/bin/connect-init-db -c settings.cfg --last-ride=12345

## Sync Rides

Once the database is initialized you can sync rides.  Essentially the script will look for rides that are newer than the
stored "last ride" id.  This will only work for a maximum of 20 unsync'd rides (the script does not currently support
paging through the Garmin Connect activity pages).

	shell$ cd /path/to/connectstrava
	shell$ connect-sync-rides -c settings.cfg

Info-level logs will indicate which rides have been uploaded/synchronized.  The script is designed to produce no 
output when there are no rides to sync.  (Edit config to turn logging to DEBUG if you want to see logs in this 
case.)

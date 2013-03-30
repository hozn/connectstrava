import sys
import logging
import optparse
import shelve
from contextlib import closing

from stravalib.protocol.scrape import WebsiteClient

from connectstrava.config import config, init_config
from connectstrava.garminconnect import ConnectClient

logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')

def _setup_parser_common(parser):
    parser.add_option('-c', '--config-file', dest='config_file', metavar='FILE', help='Path to the config file.')
    parser.add_option('-d', '--database', metavar='FILE', help='Path to the sync database file.')
    
def sync_rides():
    global config
    
    parser = optparse.OptionParser(usage='%prog [OPTIONS] CONFIGFILE')
    
    _setup_parser_common(parser)
        
    (options, args) = parser.parse_args()
    
    if not options.config_file:
        parser.error("No config file specified")
        parser.print_usage()
        sys.exit(2)
    
    init_config(options.config_file)
    
    if options.database:
        config.set('main', 'database_path', options.database)
    
    gc_username = config.get('main', 'gc.username')
    gc_password = config.get('main', 'gc.password')
    
    strava_username = config.get('main', 'strava.username')
    strava_password = config.get('main', 'strava.password')
    
    gc_client = ConnectClient(gc_username, gc_password)
    strava_client = WebsiteClient(strava_username, strava_password)
    
    activities = gc_client.get_activities()
    
    if len(activities) == 0:
        raise RuntimeError("No activities returned from Garmin Connect.")
    
    # We just grab the first activity to get the athlete id for the purpose of tracking last activity sync 
    userid = activities[0]['activity']['userId'].encode('latin1') # The unicode string is really a number
    
    with closing(shelve.open(config.get('main', 'database_path'), 'c')) as db:
        
        last_sync = db.get(userid)
        if not last_sync:
            raise RuntimeError("Need to initialize database with a last-sync'd activity for userId={0}".format(userid))
        
        # We are relying on reverse chronological order of the activities here.
        candidates = []
        for a in activities:
            a_id = int(a['activity']['activityId'])
            if a_id == last_sync:
                break
            else:
                candidates.append(a['activity'])
        
        logging.info("Found {0} activities that need to be sync'd.".format(len(candidates)))
        
        if candidates:
            
            for c in candidates:
                a_id = c['activityId']
                tmp_filename = '%s.tcx' % a_id  # TODO: Replace this with io.BytesIO()
                tcx_data = gc_client.download_activity(a_id, fmt='tcx')
                with open(tmp_filename, 'w') as fp:
                    fp.write(tcx_data)
                logging.info("Uploading activity {0}".format(a_id))
                strava_client.upload(tmp_filename)
        
            # The new last sync is actually the first one from our candidates list (since they're in newest-first order)
            db[userid] = int(candidates[0]['activityId'])
            
            logging.info("Updated last id for user {0} to {1}".format(userid, db[userid]))
            
def init_db():
    global config
    
    parser = optparse.OptionParser(usage='%prog -c CONFIGFILE [OPTIONS] --last-ride=[NUM]',
                                   description="Set the last (most recent) sync'd ride ID from Garmin Connect.")
    
    _setup_parser_common(parser)
    parser.add_option('--user-id', dest='userid', metavar='ID', type='int', 
                      help='The Garmin Connect userid.')
    
    parser.add_option('--last-ride', dest='last_ride', metavar='ID', type='int', 
                      help='The last (most recent) ride that has been synchronized.')
    
    (options, args) = parser.parse_args()
    
    if not options.config_file:
        parser.error("No config file specified")
        parser.print_usage()
        sys.exit(2)
    
    if not options.last_ride:
        parser.error("Must specify the --last-ride option.")
        parser.print_help()
        sys.exit(2)
    
    init_config(options.config_file)

    if options.database:
        config.set('main', 'database_path', options.database)
    
    userid = options.userid
    if not userid:
        raise RuntimeError("Must specify the Garmin Connect numeric user id with the --user-id parameter.")
    
    with closing(shelve.open(config.get('main', 'database_path'), 'c')) as db:
        db[str(userid)] = options.last_ride
    
import sys
import time
import logging
import logging.config
import optparse
import shelve
from contextlib import closing
from io import BytesIO

from stravalib.protocol.scrape import WebsiteClient

from connectstrava.config import config, init_config
from connectstrava.garminconnect import ConnectClient

def _setup_parser_common(parser):
    parser.add_option('-c', '--config-file', dest='config_file', metavar='FILE', help='Path to the config file.')
    parser.add_option('-d', '--database', metavar='FILE', help='Path to the sync database file.')
    
def sync_rides():
    global config
    
    parser = optparse.OptionParser(usage='%prog [OPTIONS] CONFIGFILE')
    
    _setup_parser_common(parser)
    
    parser.add_option('--timeout', dest='timeout', metavar='SECS', type='int', 
                      help='Maximum time before bailing out.', default=30)
    
    (options, args) = parser.parse_args()
    
    if not options.config_file:
        parser.error("No config file specified")
        parser.print_usage()
        sys.exit(2)
    
    init_config(options.config_file)
    
    logging.config.fileConfig(options.config_file)
    
    if options.database:
        config.set('main', 'database_path', options.database)
    
    timeout = options.timeout
    
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
        
        if candidates:
            
            logging.info("Found {0} activities that need to be sync'd.".format(len(candidates)))
            
            # First reverse it so we start with the oldest one (this makes it easier to update the last-sync'd record
            # along the way.
            
            candidates = list(reversed(candidates))
            
            upload_ids = []
            for c in candidates:
                a_id = c['activityId']
                
                #tmp_filename = '%s.tcx' % a_id  # TODO: Replace this with io.BytesIO()
                tcx_data = gc_client.download_activity(a_id, fmt='tcx')
                fp = BytesIO()
                fp.write(tcx_data)
                fp.seek(0)
                
                #with open(tmp_filename, 'w') as fp:
                #    fp.write(tcx_data)
                logging.info("Uploading activity {0}".format(a_id))
                upload_ids.extend(strava_client.upload(fp))
                
                # Update our last-sync db "row"
                db[userid] = int(a_id)
                db.sync()
                
                logging.debug("Updated last activity id for user {0} to {1}".format(userid, db[userid]))
        
            logging.info("{0} rides uploaded, last sync id for user {1} set to {2}".format(len(candidates), userid, db[userid]))
            logging.debug("Got upload ids: {0}".format(upload_ids))
            
            error_statuses = []
            success_statuses = []
            pending_ids = set(upload_ids)
            
            start_time = time.time()
            
            while len(pending_ids):
                for upload_id in list(pending_ids): # Make a copy for iteration since we modify it during iteration.
                    status= strava_client.check_upload_status(upload_id)
                    if status['workflow'] == 'Error':
                        logging.error("Error uploading item: {0}".format(status))
                        error_statuses.append(status)
                        pending_ids.remove(upload_id)
                    elif status.get('activity'):
                        url = 'http://app.strava.com/activities/{0}'.format(status['activity']['id'])
                        logging.info("Upload succeeded, acvitity URL: {0}".format(url))
                        success_statuses.append(status)
                        pending_ids.remove(upload_id)
                    else:
                        logging.debug("Upload still pending: {0}".format(status))
                    
                    if time.time() - start_time > timeout:
                        logging.warning("Bailing out because timeout of {0} exceeded. (last status={1!r})".format(timeout, status))
                        break
                    # We don't want to flood strava
                    time.sleep(1.0)
                
            if success_statuses:
                logging.info("{0} rides processed. Visit http://app.strava.com/athlete/training/new to update ride settings.".format(len(success_statuses)))
            else:
                logging.warning("Processing complete, but no successfull ride uploads.")
            
        else:
            logging.debug("No activities need to be sync'd.")
            
def init_db():
    global config
    
    parser = optparse.OptionParser(usage='%prog -c CONFIGFILE [OPTIONS] --last-ride=[NUM]',
                                   description="Set the last (most recent) sync'd ride ID from Garmin Connect.")
    
    _setup_parser_common(parser)
    #parser.add_option('--user-id', dest='userid', metavar='ID', type='int', 
    #                  help='The Garmin Connect userid.')
    
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
    logging.config.fileConfig(options.config_file)
    
    if options.database:
        config.set('main', 'database_path', options.database)
    
    gc_username = config.get('main', 'gc.username')
    gc_password = config.get('main', 'gc.password')
    gc_client = ConnectClient(gc_username, gc_password)
    
    activity = gc_client.get_activity(options.last_ride)
    userid = activity['userId'].encode('latin1') # It's a unicode string in response
    
    with closing(shelve.open(config.get('main', 'database_path'), 'c')) as db:
        db[userid] = options.last_ride
        logging.info("Updated last activity id for user {0} to {1}".format(userid, db[userid]))
    
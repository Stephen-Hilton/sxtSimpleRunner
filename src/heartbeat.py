import requests, json, os
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
from spaceandtime import SpaceAndTime

timestamp_format = '%Y-%m-%dT%H:%M:%S+00:00'

# add sxt early, for logging
sxt = SpaceAndTime(envfile_filepath="./src/.env")
sxt.logger_addFileHandler(Path(f'./src/logs/heartbeat_{datetime.utcnow().strftime(timestamp_format)}.log'))

# load in dotenv file 
load_dotenv('./src/.env')
zapier_webhook = os.getenv('ZAPIER_WEBHOOK_NOTIFY_NETWORK_STATE_CHANGE')
sxtlabs_dml_biscuit = os.getenv('SXTLABS_DML_BISCUIT')
test=str(os.getenv('TEST_ONLY')).strip().lower() in ['true','yes']
sxt.logger.info(f"config settings: \nzapier webhook: {zapier_webhook} \ndml_biscuit: {sxtlabs_dml_biscuit[:6]}...{sxtlabs_dml_biscuit[-6:]} \ntest_only: {test}\n")


# define function to report status
def report_status(webhook_url, status, message, eta: str = None):
    """Send status report to Zapier webhook"""
    header =  {"accept": "application/json",  "content-type": "application/json"}
    payload = {
        "status": status,
        "message": message
    }
    if eta: payload['eta'] = "ETA: " + eta
    if test:
        print('skipping API Call!')
        rtn = 200, {'test': 'true'}
    else:
        resp = requests.post(webhook_url, json=payload, headers=header)    
        jsonResp = resp.json()
        rtn = resp.status_code, jsonResp 
    sxt.logger.info(f"report_status response: {rtn}")
    


# get last heartbeat run status:
last_status_file = Path('./src/data/last_status.json')
sxt.logger.info(f'Getting last status from {last_status_file}')
if last_status_file.exists():
    with open(last_status_file, 'r') as f:
        last_status_data = json.load(f)
else:
    last_status_data = {'STATUS':'NOT CHECKED', 'UTC_TIMESTAMP': '1970-01-01T00:00:00+00:00'}

# calculate hours since last notification
last_status = last_status_data['STATUS']
utc_timestamp = datetime.strptime(last_status_data['UTC_TIMESTAMP'], timestamp_format)
hrs_since_last_notify = (datetime.utcnow() - utc_timestamp).total_seconds()/60/60
current_hour = datetime.utcnow().hour 
sxt.logger.info(f'Last status data: \nlast status: {last_status} \nUTC: {utc_timestamp} \nhrs_since_last_notify: {hrs_since_last_notify} \ncurrent_hour: {current_hour}\n')



# Authenticate to SXT network and run canary query
sxt.authenticate()
success, data = sxt.execute_query("""    SELECT 'OK' as STATUS
    , 'Space and Time Network is UP and accessible!' as MESSAGE
    from sxtlabs.SINGULARITY """)
 

 # fix up the data object
if not success: # something's wrong!
    data = { 
        'STATUS': 'Offline',
        'MESSAGE': 'SpaceNetwork is currently experiencing problems, engineering teams are actively engaged to return service.',
    }
else: # all is well!
    data = data[0]
    sxt.execute_query('update SXTLABS.Singularity set LAST_HEARTBEAT = current_timestamp'
                      , biscuits=[sxtlabs_dml_biscuit])
sxt.logger.info(f"data returned: \n{data}")


# test to see if state and last status state are different, or once every 6hrs (on the quarter-day only)
if data['STATUS'] != last_status or (hrs_since_last_notify > 5.95 and current_hour in [0,6,12,18]) :
    report_status(zapier_webhook, data['STATUS'], data['MESSAGE'])
else: 
    sxt.logger.info('No status change, skipping report')


# add current UTC time, and write new last_status to file
sxt.logger.info('Writing new last status to file')
data['UTC_TIMESTAMP'] = datetime.utcnow().strftime(timestamp_format)
with open(last_status_file, 'w') as f:
    json.dump(data, f)


import requests, json, logging
from tqdm import tqdm
import pandas as pd
import pathlib
from datetime import date, timedelta

def get_param(param):
    keys = param.keys()
    params = ''
    for key in keys:
        params += f'{key}={param[key]}'
    return params

def clean_data(data):
    keys = data['data'].keys()
    clean_data = []
    for key in keys:
        if 'Test Site'.lower() in data['data'][key]['description'].lower() or 'MAC' in str(data['data'][key]['cosit']): continue
        site = {}
        row = data['data'][key]
        site['id'] = row['id']
        site['node'] = row['node']
        site['cosit'] = row['cosit']
        site['siteId'] = row['node'] + '_' + row['cosit']
        site['name'] = row['name']
        site['addrs'] = row['description']
        site['parameters'] = get_param(row['parameters'])
        site['lat'] = row['location']['lat']
        site['lng'] = row['location']['lng']
        
        clean_data.append(site)
    return clean_data

def get_loc_data():
    logging.info('Fetching Location Data...')
    data = {"array": 1, "hasLocation": 1, "isPed": 0}
    headers  = {'referer':'https://trafficdata.tii.ie/publicmultinodemaplist.asp'}

    session = requests.Session()
    session.get('https://trafficdata.tii.ie/publicmultinodemaplist.asp')
    
    session.headers.update(headers)
    data = session.post('https://trafficdata.tii.ie/dataserver/public/tii/sites', data=json.dumps(data)).json()

    logging.info('Processing Location Data...')
    clean_d = clean_data(data)
    return  pd.DataFrame(clean_d)

def get_ids(id_):
#     data = {
#       "site":id_,
#       "siteExtras": "accessparameters"
#     }
#     headers = {
#             'content-type':'application/json;charset=UTF-8',
#             'origin':'https://trafficdata.tii.ie',
#             }

#     url = 'https://trafficdata.tii.ie/dataserver/sites'
#     respo = requests.post(url, headers=headers, data=json.dumps(data)).json()
#     siteGroups = respo['data'][id_]['accessParameters']['siteGroups'][0]

#     return siteGroups['sgid'], siteGroups['spid']
    ids = id_.split('-')
    sgid = 'XZOA8M4LR27P0HAO3_SRSB'
    spid = ids[0] + ids[1]
    return sgid, spid

def get_xl_data(id_, date):
    sgid, spid = get_ids(id_)
    url = f'https://trafficdata.tii.ie/tfweekreport.asp?sgid={sgid}&spid={spid}&reportdate={date}&enddate={date}&excel=1'
    r = requests.get(url, timeout=10)
    return r

def export_location_csv(df, folder):
    loc_file = f'{folder}\\Location_data.csv'
    df_loc = df.drop(columns=['id'])
    df_loc.to_csv(loc_file)
    logging.info(f'Location data saved to "{loc_file}"')

def download_reports(df, date, folder):
    logging.info(f'Downloading Traffic Data of individual locations...')
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        data = get_xl_data(row['id'], date)
        with open(folder + f'\\tfweekreport_{index}.xls', 'wb') as f:
            f.write(data.content)
    logging.info(f'Download Complete.')


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)
    folder = r'New' 

    prev_month = date.today().replace(day=1) - timedelta(days=1)
    prev_month = prev_month.replace(day=1)
    month_year = prev_month.strftime("%m-%Y")
    new_folder_path = folder + f"/{month_year}"
    
    pathlib.Path(new_folder_path).mkdir(parents=True, exist_ok=True) 
    
    date_ = prev_month.strftime("%Y-%m-%d")
    
    data = get_loc_data()
    export_location_csv(data, new_folder_path)
    download_reports(data, date_, new_folder_path)



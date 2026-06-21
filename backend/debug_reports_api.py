import requests

# Login
res = requests.post('http://localhost:8091/api/auth/login',
                    data={'username': 'manager@apex.com', 'password': 'manager123'})
token = res.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Generate PDF report
gen = requests.post('http://localhost:8091/api/reports/generate',
                    json={'organizationId': 'org_apex', 'reportType': 'PDF', 'periodType': 'Weekly'},
                    headers=headers)
print('Generate status:', gen.status_code)
rdata = gen.json()
print('Report ID:', rdata['reportId'])
print('Report type:', rdata['reportType'])
print('File path:', rdata['filePath'])

# Download it
fp = rdata['filePath']
dl = requests.get(f'http://localhost:8091{fp}', headers=headers)
print('Download status:', dl.status_code)
print('Content-Type:', dl.headers.get('content-type'))
print('File size:', len(dl.content), 'bytes')
print('PDF magic bytes (hex):', dl.content[:4].hex())
print('Is real PDF:', dl.content[:4] == b'%PDF')

# Also test Excel
gen2 = requests.post('http://localhost:8091/api/reports/generate',
                     json={'organizationId': 'org_apex', 'reportType': 'Excel', 'periodType': 'Monthly'},
                     headers=headers)
rdata2 = gen2.json()
fp2 = rdata2['filePath']
dl2 = requests.get(f'http://localhost:8091{fp2}', headers=headers)
print('\nExcel Content-Type:', dl2.headers.get('content-type'))
print('Excel file size:', len(dl2.content), 'bytes')
print('Is real XLSX:', dl2.content[:4] == b'PK\x03\x04')  # ZIP magic = XLSX

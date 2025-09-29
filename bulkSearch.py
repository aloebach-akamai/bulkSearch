# This CLI will allow you to easily perform a bulk search of all PM configs for a certain behavior and value
# The search can either be specified via input parameters --behavior, [--parameter], [--value], or alternatively a custom search JSON file

# https://github.com/aloebach-akamai/bulkSearch

#Author: Andrew Loebach


###   Importing packages   ### 
import sys
if sys.version_info[0] < 3:
	print("WARNING: Python 3 is required for running this script. Please check your python version\n")
	sys.exit()
import json
from urllib.parse import urljoin
from os.path import expanduser #added for importing credentials from .edgerc
from akamai.edgegrid import EdgeGridAuth, EdgeRc
import requests
import argparse
import time


#Parse command-line arguments and set default values if no argument is specified
parser = argparse.ArgumentParser()
parser.add_argument("--behavior", "--behaviour", help="Specify the PM behavior to search for")
parser.add_argument("--parameter", help="Specify a particular parameter we're searching for in the behavior's options")
parser.add_argument("--value", help="Specify a value to match on if you want to filter your search to matches where a parameter matches a specific value.")
parser.add_argument("--output", "--out", help="Specify the name of a file to output the results (in csv format")
parser.add_argument("--json", help="specify a json file containing a JSONPath expression to use as search criteria")
parser.add_argument("--switchkey", "--account-key", "--accountkey", help="Account switch key")
parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose output")
parser.add_argument("--section", help="Section for .edgerc file", default="default")
args = parser.parse_args()



#################################################
### Reading API credentials from .edgerc file ###
#################################################
home = expanduser('~') #search for .edgerc file in root directory
EDGERC_PATH = '%s/.edgerc' % home 
edgerc = EdgeRc(EDGERC_PATH)
section = args.section #can replace with PAPI or other section if you prefer
baseurl = 'https://%s' % edgerc.get(section, 'host')

s = requests.Session()
s.auth = EdgeGridAuth.from_edgerc(edgerc, section)



##############################################
###	  CREATE FILE TO OUTPUT TEST RESULTS   ### 
##############################################
if args.output:
	if args.output.endswith(".csv"):
		OUTPUT_FILE =  args.output
	else:
		OUTPUT_FILE =  args.output + ".csv"
	test_results = open(OUTPUT_FILE, 'w+') 
	if args.parameter:
		test_results.write('CONFIG_NAME,' + args.parameter)
	else:
		test_results.write('CONFIG_NAME,DETAIL')
	test_results.write(str('\n')) #new line
##############################################



##########################################################
###   Setting up template JSON for search parameters   ###
##########################################################
search_json = {
	"bulkSearchQuery": {
		"syntax": "JSONPATH",
		"match": "$..behaviors[?(@.name == 'BEHAVIOR')].options.PARAMETER"
	}
}

if args.json: #If json file is specified, extract search JSON from file
	print("\nloading search criteria from ", args.json)
	try:
		f = open(args.json, "r")
	except:
		print('ERROR: file cannot be read (', args.json , ')')
		sys.exit()
	search_json = json.loads( f.read() )
	
elif args.behavior: # if behavior is specified in search we search for this behavior directly
	print("\nsearching for", args.behavior, " behavior...")
	if args.parameter:
		search_match = "$..behaviors[?(@.name == 'BEHAVIOR')].options.PARAMETER".replace("BEHAVIOR",args.behavior).replace("PARAMETER",args.parameter)
		if args.value: 
			search_match = "$..behaviors[?(@.name == 'BEHAVIOR')].options[?(@.PARAMETER == 'VALUE')].PARAMETER".replace("BEHAVIOR",args.behavior).replace("PARAMETER",args.parameter).replace("VALUE",args.value)
		search_json['bulkSearchQuery']['match']	= search_match		
	else:
		search_match = "$..behaviors[?(@.name == 'BEHAVIOR')]".replace("BEHAVIOR",args.behavior)
		search_json['bulkSearchQuery']['match']	= search_match
		if args.value: 
			print("ERROR: When specifying --value, you must specify a --parameter to search for this value\n")
			sys.exit()

else:
	# if no JSON file or behavior is specified
	print("\nno json file or behavior specified. One of these is required as search criteria.")
	print("specify a behavior to search for with --behavior, or use a search file as JSON which you can input with --json.\n")
	print("\nUSAGE:	python bulkSearch.py --behavior <behavior name> [--parameter <name of parameter>] [--value <value of parameter>]\n")
	sys.exit()


if args.verbose:
	print("search_json: ")
	print(search_json, "\n")



############################################
####   PERFORMING BULK SEARCH API CALL   ###
############################################
if args.switchkey:
	API_path = '/papi/v1/bulk/rules-search-requests?accountSwitchKey=' + args.switchkey  #with accountSwitchKey as query parameter
else:
	API_path = '/papi/v1/bulk/rules-search-requests'  #without SwitchKey as query parameter

request_headers = {
	"accept": "application/json",
	"content-type": "application/json"
}

try:
	 #API Call to retrieve version info
	 API_response = s.post( urljoin(baseurl, API_path), headers=request_headers, data=json.dumps(search_json) )
	 bulk_search_link = json.loads(API_response.text)['bulkSearchLink']
except: 	#If the first API request fails print error message to check .edgerc file  
	 print('ERROR reading .edgerc file')
	 print('Please ensure that you have valid API credentials listed in the .edgerc file in the [', section, '] section', sep='')
	 print('A valid .edgerc file should be located here:', EDGERC_PATH)
	 sys.exit() #escape program if credentials are not successfully imported

if API_response.status_code != 202:
	print("ERROR with bulk search request")
	print('Status code: ', API_response.status_code)
	print(API_response.text)
	sys.exit()
elif args.verbose:
	print('Status code: ', API_response.status_code)
	print(API_response.text)



########################################################
####   RETRIEVING BULK SEARCH RESULTS VIA API CALL   ###
########################################################
try:
	API_path = bulk_search_link # API_response.text['bulkSearchLink']
except:
	print("ERROR fetching link for retrieving bulk search results")
	sys.exit()

# checking for bulk search results	
waiting_for_bulk_search_results = True
while waiting_for_bulk_search_results:
	print('waiting for bulk search results...')
	try:
		#API Call to retrieve version info
		API_response = s.get( urljoin(baseurl, API_path) )
	except: 	
		print('ERROR retrieving bulk search results')
		sys.exit() #escape program if credentials are not successfully imported
	
	if API_response.status_code == 200:
		search_results = json.loads(API_response.text)
		if search_results['searchTargetStatus'] == "COMPLETE":
			print("search results retrieved.\n") # print newline here 
			break
	else:
		print("ERROR: invalid response to bulk search results")
		print('Status code: ', API_response.status_code)
		print(API_response.text)
		sys.exit()
	
	# wait 10 seconds then check again
	time.sleep(5)



##################################################################
####   GET VALUES FROM PROPERTY BASED ON BULK SEARCH RESULTS   ###
##################################################################
# define function to traversing json rule tree:
def find_element_in_json(json, path):
	next_path = path.split('/', 1)
	if next_path[0].isdigit():	# if this is a digit we need to cast it as an integer so it's not interpreted as a key
		next_path[0] = int(next_path[0])
	if len(next_path) < 2:
		return json[next_path[0]]
	else:
		return find_element_in_json( json[next_path[0]], next_path[1])

# parse rule trees to get details
for result in search_results['results']:
	if 'propertyName' in result:
		print("Property name: ", result['propertyName'])
	else:
		# TO-DO: Add support for PM Includes
		print("ERROR: Property name not found in result")
		print(result)
		continue
	
	# retrieve property JSON 
	request_headers = {
		'Content-Type': 'application/json',
		'PAPI-Use-Prefixes': 'false'
	}
	if args.switchkey:
		API_path = '/papi/v1/properties/{0}/versions/{1}/rules?accountSwitchKey={2}'.format(result['propertyId'], result['propertyVersion'], args.switchkey)
	else:
		API_path = '/papi/v1/properties/{0}/versions/{1}/rules'.format(result['propertyId'], result['propertyVersion'])
	
	papi_response = s.get(urljoin(baseurl, API_path), headers=request_headers)
	rule_tree = json.loads(papi_response.text)
	
	# get value at location returned from bulksearch API
	for location in result['matchLocations']:
		if args.verbose: print("  location:", location)
		
		search_result = find_element_in_json(rule_tree, location.strip('/'))
		if args.parameter:
			print("  ", args.parameter, ": ",  search_result)
		else:
			print("  value:", search_result)
			
		if args.output:
			test_results.write( result['propertyName'] + "," + str(search_result) )
			test_results.write(str('\n')) #new line
		
	print("")
######################################


print("<script completed>\n")

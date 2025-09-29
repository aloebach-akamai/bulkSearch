
# BulkSearch

A Python script which can be used to search through Akamai Property Manager configurations for a specific behavior or value using Akamai's [bulksearch API](https://techdocs.akamai.com/property-mgr/reference/post-bulk-search)
<br/>

## Dependencies
You will need the following to use the bulkSearch script:
* Valid [EdgeGrid authentication credentials](https://techdocs.akamai.com/developer/docs/edgegrid) for an API client which has read access to [Property Manager API](https://techdocs.akamai.com/property-mgr/reference/api) 
* Python 3 installed on your machine
* A few python libraries which can be installed with the command below:
```bash
pip3 install -r requirements.txt
```

## Usage
### Simple Search 
The following command will search all configurations for the "customBehavior" behavior:
```
% python bulkSearch.py --behavior edgeWorker 

searching for edgeWorker  behavior...
waiting for bulk search results...
waiting for bulk search results...
waiting for bulk search results...
search results retrieved.

Property name:  www.davidbartosh.com.xml
  value: {'name': 'edgeWorker', 'options': {'enabled': True, 'createEdgeWorker': '', 'edgeWorkerId': '4219', 'resourceTier': '', 'mPulse': False, 'continueOnError': False}}

Property name:  dummy_xiaozang_FOSSL_PM
  value: {'name': 'edgeWorker', 'options': {'enabled': True, 'createEdgeWorker': '', 'edgeWorkerId': '3871', 'mPulse': False, 'continueOnError': False}}

Property name:  ktokarsk-test.kaki.pl
  value: {'name': 'edgeWorker', 'options': {'enabled': True, 'createEdgeWorker': '', 'edgeWorkerId': '4251', 'mPulse': False, 'continueOnError': False}}

Property name:  fnami_ion_template
  value: {'name': 'edgeWorker', 'options': {'enabled': True, 'createEdgeWorker': '', 'edgeWorkerId': '4351', 'mPulse': False, 'continueOnError': False}}

Property name:  sanandh-ion.edgesuite.net
  value: {'name': 'edgeWorker', 'options': {'enabled': True, 'createEdgeWorker': '', 'edgeWorkerId': '37869', 'resourceTier': '', 'mPulse': False, 'continueOnError': False}}
  
<script completed>
```

Note that this outputs all of the details of this behavior in PM's JSON format.
<br/>
<br/>

### Specifying a parameter to output
Using the `--parameter` option, we can look for just the parameter we're interested in, such as the value of a CP Code, or the specific Edgeworker ID in the Edgeworker behavior.

The following command will search all configurations for the "edgeWorker" behavior and output the respective edgeWorker ID:
```
 % python bulkSearch.py --behavior edgeWorker --parameter edgeWorkerId

searching for edgeWorker  behavior...
waiting for bulk search results...
waiting for bulk search results...
waiting for bulk search results...
waiting for bulk search results...
waiting for bulk search results...
search results retrieved.

Property name:  www.davidbartosh.com.xml
   edgeWorkerId :  4219

Property name:  dummy_xiaozang_FOSSL_PM
   edgeWorkerId :  3871

Property name:  ktokarsk-test.kaki.pl
   edgeWorkerId :  4251

Property name:  fnami_ion_template
   edgeWorkerId :  4351

Property name:  sanandh-ion.edgesuite.net
   edgeWorkerId :  37869

<script completed>
```
<br/>
<br/>


### Search for a specific value
To search for a behavior with a specific value, we can use the `--value` option. 

I want to search for any configuration that uses a specific CP Code. This is slightly trickier since the value I'm looking for is nested into the JSON. The `cpCode` behavior looks like this:

```json
{
	"name": "cpCode",
	"options": {
		"value": {
			"cpCodeLimits": null,
			"createdDate": 1469198169000,
			"description": "Drews.site",
			"id": 487341,
			"name": "Drews.site",
			"products": [
				"Fresca"
			]
		}
	}
}
```

bulkSearch will look into `options` by default, but since we want to look for `value`->`id`, we need to specify the parameter as `value.id` 

The following command will search all configurations for a CP Code with the value 487341:
```
python bulkSearch.py --behavior 'cpCode' --parameter 'value.id' --value 487341

searching for cpCode  behavior...
waiting for bulk search results...
waiting for bulk search results...
waiting for bulk search results...
search results retrieved.

Property name:  API_test_config
   value.id :  487341

Property name:  Drews_IPA_test
   value.id :  487341

Property name:  Drews_site
   value.id :  487341

Property name:  serverless.drewstestsite.com
   value.id :  487341

<script completed>
```
<br/>
<br/>


### JSON search file
As an alternative to specifying the `--behavior` and other parameters, you can instead use a search query JSONPath saved in a .json file.

syntax: `python bulkSearch.py --json <name of file containing query details>`

Example:
We want to search all configs for the "customBehavior" behavior, and output the behavior Ids.

We will store the JSONPath formatted match in the `match` field of the json search file, which we are saving as custom_behavior_search.json:
```json
{
	"bulkSearchQuery": {
		"syntax": "JSONPATH",
		"match": "$..behaviors[?(@.name == 'customBehavior')].options.behaviorId"
	}
}
```

The query can be performed with the following command
```
python bulkSearch.py --json custom_behavior_search.json   
```

Here are some examples of `match` criteria that you can configure in the search JSON file:
* `"$..behaviors[?(@.name == 'customBehavior')].options[?(@.behaviorId == 'cbe_111166541')].behaviorId"`	-> searches for custom behavior with behaviorId 111166541
* `"$..behaviors[?(@.name == 'customBehavior')].options.behaviorId"`	-> searches for any custom behavior and outputs behaviorID
* `"$..behaviors[?(@.name == 'origin')].options.hostname"`	-> outputs all origin hostnames
* `"$..behaviors[?(@.name == 'edgeWorker')].options.edgeWorkerId"`	-> search for any Edgeworker and outputs Edgeworker IDs
* `"$..behaviors[?(@.name == 'sureRoute')].options.testObjectUrl"`	-> search for any SureRoute behavior and outputs the testObject URL
* `"$..behaviors[?(@.name == 'cpCode')].options.value.id"`	-> search for all CP code behaviors and output the CP Code IDs
<br/>
<br/>


### Saving results to a .csv file 

The results can be conveniently outputted to a .csv file by specifying the name of the output file with `--out <filename>`

Example:
```
 python bulkSearch.py --behavior 'customBehavior' --parameter 'behaviorId' --out 'custom_behaviors.csv'
```
<br/>


## Clone this repository from git
```
git clone https://github.com/aloebach-akamai/bulkSearch.git
```

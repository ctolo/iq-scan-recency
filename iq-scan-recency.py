#!/usr/bin/python3
# ----------------------------------------------------------------------------
# Python Dependencies
import json
import argparse
import asyncio
import aiohttp

# ----------------------------------------------------------------------------
iq_url, iq_session, components, history = "", "", {}, {}

def get_arguments():
    global iq_url, iq_session, iq_auth
    parser = argparse.ArgumentParser(description='Get last CI scan from application history.')
    parser.add_argument('-u', '--url', help='', default="http://localhost:8070", required=False)
    parser.add_argument('-a', '--auth', help='', default="admin:admin123", required=False)
    args = vars(parser.parse_args())
    iq_url = args["url"]
    creds = args["auth"].split(":")
    iq_session = aiohttp.ClientSession()
    iq_auth = aiohttp.BasicAuth(creds[0], creds[1])
    return args

async def main():
    args = get_arguments()
    apps = await get_apps()

    for app_history in asyncio.as_completed([
            handle_history(app) for app in apps ]):
        history.update(await app_history)

    save_results("results.json", history, True)
    await iq_session.close()

#---------------------------------
async def get_apps():
    url = f'{iq_url}/api/v2/applications'
    apps = await get_url(url, "applications")
    if apps is None: 
        print('No apps found')
        await iq_session.close()
        exit(1)
    return apps

async def handle_history(app):
	resp, appId = {}, app['id']
	url = f'{iq_url}/api/v2/reports/applications/{appId}/history'
	app_history = await get_url(url)
	app['last_ci'] = {}
	for report in app_history['reports']:
		clean_dict(report,['applicationId','latestReportHtmlUrl',
			'reportHtmlUrl','embeddableReportHtmlUrl','reportPdfUrl',
			'reportDataUrl','policyEvaluationResult'])

	for report in app_history['reports']:
		if not report['isForMonitoring']:
			app['last_ci'] = report
			break

	app.update(app_history)
	clean_dict(app,['id','contactUserName','applicationTags','applicationId'])
	resp = {appId: app}
	return resp

def print_summary():
    summary = {"format":{}}
    for c in components.values():
        if not c["format"] in summary["format"]:
            summary["format"].update({c["format"]: 0 })
        summary["format"][c["format"]] += 1
    pp(summary)
#-----------------------------------------------------
def pp(page):
    print(json.dumps(page, indent=4))

def clean_dict(dictionary, remove_list):
    for e in remove_list: 
        dictionary.pop(e, None)

def save_results(file_name, results, indent=False):
    with open(file_name, "w+") as file:
        if indent:
              file.write(json.dumps(results, indent=4))
        else: file.write(json.dumps(results))
    print(f"Json results saved to -> {file_name}")

async def get_url(url, root=""):
    resp = await iq_session.get(url, auth=iq_auth)
    if resp.status != 200: return None
    node = await resp.json()
    if root in node: node = node[root]
    if node is None or len(node) == 0: return None
    return node
#-----------------------------------------------------   
if __name__ == "__main__":
    asyncio.run(main())










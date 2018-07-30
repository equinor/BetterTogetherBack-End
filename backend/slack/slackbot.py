import os
import ssl
import urllib
import base64

from slackclient import SlackClient
import json


def get_persons_from_slack():
    persons = []
    context = ssl._create_unverified_context()

    client = SlackClient(os.environ['SLACK_TOKEN'])
    request = client.api_call("conversations.members", channel=os.environ['SLACK_CHANNEL'])
    if request['ok']:
        for member in request['members']:
            person = dict()
            profile = client.api_call("users.profile.get", user=member)['profile']
            person['username'] = profile['display_name_normalized']
            if 'image_1024' not in profile.keys():
                person['image'] = "unknown"
            else:
                img = urllib.request.urlopen(profile['image_1024'], context=context).read()
                person['image'] = str(base64.b64encode(img))[2:]
                filename = person['username']+'.png'
                with open(os.path.join('../api/static/images', filename), 'wb') as f:
                    f.write(img)
            person['name'] = profile['real_name']
            persons.append(person)
    else:
        print("request failed")

    return persons


def write_to_json(data):
    with open("../backend/json/jsonUserList.json", 'w') as outfile:
        json.dump(data, outfile, indent=2, sort_keys=True)
        outfile.close()

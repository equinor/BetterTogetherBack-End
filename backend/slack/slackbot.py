import os
import ssl
import urllib
import base64

from slackclient import SlackClient


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
            if 'image_192' not in profile.keys():
                person['image'] = "unknown"
            else:
                img = urllib.request.urlopen(profile['image_192'], context=context).read()
                person['image'] = str(base64.b64encode(img))[2:]
                filename = person['username']
                with open(os.path.join('./backend/DB/api/static/images', filename), 'wb') as f:
                    f.write(img)
            person['name'] = profile['real_name']
            persons.append(person)
    else:
        print("request failed")

    return persons

from slackclient import SlackClient
import json


def get_persons_from_slack():
    persons = []

    client = SlackClient("INSERT_TOKEN_HERE")
    request = client.api_call("conversations.members", channel="INSERT_CHANNEL_ID_HERE")
    if request['ok']:
        for member in request['members']:
            person = dict()
            profile = client.api_call("users.profile.get", user=member)['profile']
            person['username'] = profile['display_name_normalized']
            if 'image_1024' not in profile.keys():
                person['image'] = "unknown"
            else:
                person['image'] = profile['image_1024']
            person['name'] = profile['real_name']
            persons.append(person)
    else:
        print("request failed")

    return persons


def write_to_json(data):
    with open("../backend/json/jsonUserList.json", 'w') as outfile:
        json.dump(data, outfile, indent=2, sort_keys=True)
        outfile.close()


#write_to_json(get_persons_from_slack())

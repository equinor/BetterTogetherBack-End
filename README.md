
# BetterTogether Backend [![Build Status](https://travis-ci.org/Statoil/BetterTogetherBack-End.svg?branch=master)](https://travis-ci.org/Statoil/BetterTogetherBack-End)

This is the database and web display for the Better Together project.
The purpose of this project is to log and encourage pair programming in a team by
getting rewarded when reaching a set number of pair programming events.

## Installation

The following environment variables must be defined in the [Dockerfile](https://github.com/Statoil/BetterTogetherBack-End/blob/master/Dockerfile):
- BT_TOKEN: to access the web page and REST api endpoints
- SLACK_TOKEN: token provided by slack that gives access to channels in slack
- SLACK_CHANNEL: channel id found in the slack channel url
- POSTGRES_USERNAME: credentials for postgres database
- POSTGRES_PASSWORD: credentials for postgres database
- POSTGRES_HOSTNAME: hostname for postgres database

Install [Docker](https://docs.docker.com/install/#supported-platforms) and build an image
    ```docker image build -t <name_of_image>:<name_of_tag> .```

Start a running container associated with the image:
    ```docker run -p 80:80 <name_of_image>:<name_of_tag>```

## Interaction
All communication with the REST api and webview must provide a token parameter to validate.

Example:
    ```http://0.0.0.0/api/user/all?token=EXAMPLE```

You will use the app from BetterTogether to add pairs when you have pair programmed.
Everything else can be accessed through curl.

Changing thresholds:
    ```curl -X put <yourlink>/api/threshold/update/<reward_type>/<your threshold>```

Using rewards:
    ```curl -X put <yourlink>/api/reward/use/<reward_type>```

Change lifetime of edges in webview:
Add a url parameter after the token representing the lifetime of the edges in number of days as follows:
    ```http://0.0.0.0?token=EXAMPLE&days=20```

Reset database:
Uncomment ```db.drop_all()``` in **set_up_db()** in [routes.py](https://github.com/Statoil/BetterTogetherBack-End/blob/master/backend/DB/api/routes.py)

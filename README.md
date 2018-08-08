# kong-expired-token-cleanup
## Overview
A simple python script, which can be installed on any *nix server to manage expired token deletion in a kong cassandra database, and notify admins via email afterwards.

The script will also report on token creation "abuse". This "abuse" is defined as a consumer who creates more than 100 tokens per day; the expectation being that a consumer should cache and reuuse tokens for their set duration.

Especially useful in environments where storage capacity is a conern.

## Dependencies
Python 2.7 - https://www.python.org/downloads/source/

Python [cassandra-driver](https://datastax.github.io/python-driver/installation.html)
```
pip install cassandra-driver
```

Python [argparse](https://docs.python.org/2.7/library/argparse.html)
```
pip install argparse
```

Python [smtplib](https://docs.python.org/2/library/smtplib.html)
```
pip install smtplib
```

## Instalation
### Usage Note:
This script is best employed as a daily or weekly cron task. The following instructions will be aligned towards that approach.

```
mkdir /opt/script
git install https://github.optum.com/Optum/kong-expired-token-cleanup.git /opt/scipt
```

Usage
```
# python OAuth_Token_Cleanup.py -h
usage: OAuth_Token_Cleanup.py [-h] [--ssl] [--ca CA]
                              cassandrahost keyspace username password email
                              smtpserver

Deletes expired OAuth 2.0 Tokens used in Kong API Gateway functionality from a cassandra database over SSL. Also reports on consumers who create an excessive amount of tokens

positional arguments:
  cassandrahost  hostname of one cassandra contact point
  keyspace       keyspace for the token deletes
  username       cassandra username
  password       cassandra password
  email          email address to notify of token cleanup
  smtpserver     SMTP relay server to use to send notification email

optional arguments:
  -h, --help     show this help message and exit
  --ssl          (Default false) use SSL for connections to cassandra
  --ca CA        If using SSL, provide a path to the truststore as a PEM

Examples:

python OAuth_Token_Cleanup.py localhost kong_dev dbausername dbapassword email@server.com mail.relay.com
Deletes tokens in the kong_dev keyspace (oauth2_tokens table), using the dbausername and dbapassword. Will send a notification email to email@server.com, relaying off mail.relay.com

python OAuth_Token_Cleanup.py localhost kong_dev dbausername dbapassword email@server.com mail.relay.com --ssl --ca /path/to/truststore.pem
Deletes tokens in the kong_dev keyspace (oauth2_tokens table), using the dbausername and dbapassword over SSL. Will send a notification email to email@server.com, relaying off mail.relay.com
```

Crontab installation with SSL and email notifications
```
crontab -e

# For daily runs (recommended)
0 2 * * * python /opt/scripts/kong-expired-token-cleanup/OAuth_Token_Cleanup.py localhost kong_kespace cass_username cass_password notifyme@email.com --ssl --ca /opt/scripts/kong-expired-token-cleanup/truststore.ca> /dev/null 2>&1

# for weekly runs
0 2 * * o python /opt/scripts/kong-expired-token-cleanup/OAuth_Token_Cleanup.py localhost kong_kespace cass_username cass_password notifyme@email.com --ssl --ca /opt/scripts/kong-expired-token-cleanup/truststore.ca> /dev/null 2>&1
```
## Supported Dependencies 
python 2.7.x 
cassandra 3.x

## Maintainers
[jeremyjpj0916](https://github.com/jeremyjpj0916)  
[rsbrisci](https://github.com/rsbrisci)  

Feel free to open issues, or refer to our Contribution Guidelines if you have any questions.

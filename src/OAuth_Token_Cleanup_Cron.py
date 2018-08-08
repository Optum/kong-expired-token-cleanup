from cassandra.cluster import Cluster
from ssl import PROTOCOL_TLSv1, CERT_REQUIRED
from cassandra.auth import PlainTextAuthProvider
import argparse
import time
import datetime
import smtplib
import uuid
import socket
from email.mime.text import MIMEText
import sys
import argparse
import os.path

# Loads hostname of server to give detail in notification email
casshost=socket.gethostname()

# Parses Arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description='Deletes expired OAuth 2.0 Tokens used in Kong API Gateway functionality from a cassandra database over SSL. Also reports on consumers who create an excessive amount of tokens',
                                 epilog="Examples:\n\
\n\
python OAuth_Token_Cleanup.py localhost kong_dev dbausername dbapassword email@server.com mail.relay.com\n\
Deletes tokens in the kong_dev keyspace (oauth2_tokens table), using the dbausername and dbapassword. Will send a notification email to email@server.com, relaying off mail.relay.com\n\n\
python OAuth_Token_Cleanup.py localhost kong_dev dbausername dbapassword email@server.com mail.relay.com --ssl --ca /path/to/truststore.pem\n\
Deletes tokens in the kong_dev keyspace (oauth2_tokens table), using the dbausername and dbapassword over SSL. Will send a notification email to email@server.com, relaying off mail.relay.com\n\
.\n\
.")
parser.add_argument('cassandrahost', type=str, help='hostname of one cassandra contact point')
parser.add_argument('keyspace', type=str, help='keyspace for the token deletes')
parser.add_argument('username', type=str, help='cassandra username')
parser.add_argument('password', type=str, help='cassandra password')
parser.add_argument('email', type=str, help='email address to notify of token cleanup')
parser.add_argument('smtpserver', type=str, help='SMTP relay server to use to send notification email')
parser.add_argument('--ssl', action='store_true', default=False, help='(Default false) use SSL for connections to cassandra')
parser.add_argument('--ca', type=str, help='If using SSL, provide a path to the truststore as a PEM')

args = parser.parse_args()
if args.ssl:
        if args.ca is None:
                parser.error("--ssl requires --ca to set a truststore")
        if (not os.path.exists(args.ca)):
                parser.error("--ca file not found or reachable")
        ssl_opts = {
            'ca_certs': args.ca,
            'ssl_version': PROTOCOL_TLSv1,
            'cert_reqs': CERT_REQUIRED  # Certificates are required and validated
        }
else:
        ssl_opts = {}


def sendEmailAlert(BODY, dbhost, subject):
        msg = MIMEText(BODY, 'html')
        msg['Subject'] = dbhost + " " + subject
        sender = dbhost + " OAuth Token Cleanup Script"
        recipients = [args.email]
        msg['From'] = sender
        msg['To'] = ", ".join(recipients)
        server = smtplib.SMTP(args.smtpserver)
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()
def deleteExpiredIDs(host,keyspace,user,password):
        # subtracts 7200 because we want to only delete those tokens more than two hours old. Subtacts 21600 (6 hours) because cassandra compensates for the UTC/CTC time difference
        two_hours_ago = datetime.datetime.utcfromtimestamp(int(time.time())- 7200 - 21600)
        auth_provider = PlainTextAuthProvider(username=user, password=password)
        cluster = Cluster([host],ssl_options=ssl_opts,auth_provider=auth_provider,port=9042)
        session = cluster.connect(keyspace)
        str_two_hours_ago = str(two_hours_ago)
        rows = session.execute("SELECT id, credential_id FROM oauth2_tokens where created_at <='" + str_two_hours_ago  + "' ALLOW FILTERING")
        rowsdeleted = 0
        consumer_tokens = {}
        for token_row in rows:
                 # Used to determine is a consumer is abusing token service
                if token_row.credential_id in consumer_tokens:
                        consumer_tokens[token_row.credential_id] += 1
                else:
                        consumer_tokens[token_row.credential_id] = 1
                rowsdeleted+=1
                session.execute("DELETE from oauth2_tokens where id=" + str(token_row.id) + "")

        consumer_abuse_table = "<hr/><span class=\"black\">Consumer Token Creation Abuse (If any): </span><hr/>"
        for key, value in consumer_tokens.iteritems():
                if value >= 100:
                        offending_creds = session.execute("SELECT consumer_id FROM oauth2_credentials where id = " + str(key).replace('(','').replace(')','') +  " ALLOW FILTERING")
                        offending_consumer_id = str(offending_creds[0].consumer_id)
                        offending_consumer = session.execute("SELECT username FROM consumers where id = " + offending_consumer_id + " ALLOW FILTERING")
                        offending_consumer_username = str(offending_consumer[0].username)
                        consumer_abuse_table+= "<br/><span class=\"black\">Cassandra Keyspace: </span> " + str(keyspace)+                               "<br/><span class=\"black\">Consumer ID: </span> "+ offending_consumer_id +                         "<br/><span class=\"black\">Consumer Name: </span> "+ offending_consumer_username +                              "<br/><span class=\"black\">Tokens Created: </span> "+ str(value) + "<hr/>"


        sendEmailAlert("<html> <head> <style> body{ font-family: FrutigerLTStd-Light, Arial, sans-serif;} h1, h2, h3, h4 { color:#e87722; font-weight: bold; text-rendering: optimizeLegibility; margin: 0 0 24px 0; } .black{ color:#333333; }.light{ color:#8c8c8c; font-size: 10px; } </style> </head> <body> <br/> <h1><span class=\"black\">Server:</span> " + casshost + "<br/><span class=\"black\">Cassandra Keyspace: </span> "+str(keyspace) +"<br/><span class=\"black\">OAuth_Tokens Rows Deleted: </span> "+str(rowsdeleted)+"</h1> "+str(consumer_abuse_table)+"</body> </html>",casshost,"OAuth Token Cleanup")
        cluster.shutdown()
deleteExpiredIDs(args.cassandrahost, args.keyspace, args.username, args.password)

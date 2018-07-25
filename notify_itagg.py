#!/usr/bin/python

import argparse
import urllib.request

# iTagg details
API_URL = "http://secure.itagg.com/smsg/sms.mes"
API_USERNAME = "b5abeaef"
API_PASSWORD = "6399f0cb"





def main():
    argp = argparse.ArgumentParser(description='Sends an SMS via the iTagg SMS servoce')
    argp.add_argument('-r', '--recipient', metavar='PHONE_NUMBER', default='', required=True,
                      help='The phone number to send the SMS to')
    argp.add_argument('-m', '--message', metavar='MESSAGE', default='', required=True,
                      help='The message to send')
    argp.add_argument('-s', '--sender', metavar='PHONE_NUMBER', default='python',
                      help='The phone numer/short code to send the message from')
    args = argp.parse_args()

    send(args.recipient, args.message, args.sender)




def send(recipient, message, sender='python'):
    data = {
        'usr': API_USERNAME,
        'pwd': API_PASSWORD,
        'from': sender,
        'to': recipient,
        'type': 'text',
        'route': 7,
        'txt': message
    }

    # Encode the data
    data_encoded = urllib.parse.urlencode(data).encode("utf-8")

    # Send the request to iTagg
    request = urllib.request.Request(API_URL, data=data_encoded, method="POST")
    #result = urllib.request.urlopen(request)

    # Process the response
    #body = result.read().decode("utf-8")
    body = "error code|error text|submission reference\n0|sms submitted|996a4201cfe1cb7acfac341a6c7a2b0e-3\n"

    if (body == 'fail,login'):
        print('Unable to login to iTagg')
        exit(-1)


    lines = body.split("\n")
    fields = lines[1].split("|")
    print(fields)
    if (fields[0] == '0'):
        print('SMS was sent successfully - ', fields[2])
        exit()
    else:
        print('SMS failed to send - ', fields[2])
        print(fields)
        exit(-1)

if __name__ == '__main__':
    main()

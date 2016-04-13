from flask import current_app as app
from argparse import ArgumentParser
import sys
import imaplib
import email
import email.header
import datetime
import yaml
import os

class GliderEmailProcessor(object):

    def __init__(self, config):
        self.config = config


    def process_mailbox(self):
        """
        Do something with emails messages in the folder.  
        """
        if self.config.get('SEARCH'):
            search_args = self.config['SEARCH'].split(' ')
            rv, data = self.mail_client.search(None, *search_args)
        else:
            rv, data = self.mail_client.search(None, "ALL")

        if rv != 'OK':
            print "No messages found!"
            return

        for num in data[0].split():
            rv, data = self.mail_client.fetch(num, '(RFC822)')
            if rv != 'OK':
                print "ERROR getting message", num
                return
            
            msg = email.message_from_string(data[0][1])
            decode = email.header.decode_header(msg['Subject'])[0]
            subject = unicode(decode[0])
            print 'Message {}: {}'.format(num, subject)
            print 'Raw Date:', msg['Date']
            print "Writing message ", num
            if not os.path.exists(self.config['OUTPUT_DIRECTORY']):
                os.makedirs(self.config['OUTPUT_DIRECTORY'])
            with open(os.path.join(self.config['OUTPUT_DIRECTORY'], '{}.txt'.format(num)), 'wb') as f:
                f.write(data[0][1])

            # Now convert to local date-time
            date_tuple = email.utils.parsedate_tz(msg['Date'])
            if date_tuple:
                local_date = datetime.datetime.fromtimestamp(
                    email.utils.mktime_tz(date_tuple))
                print "Local Date:", \
                    local_date.strftime("%a, %d %b %Y %H:%M:%S")

    def process(self):
        # open connection to gmail 
        self.mail_client = imaplib.IMAP4_SSL('imap.gmail.com')
         
        # Most imaplib functions return a tuple
        ## first object is a status ('OK')
        ## Second object is some output
        status, data = self.mail_client.login(self.config['EMAIL_ACCOUNT'], self.config['EMAIL_PASSWORD'])

         
        print status, data
         
         # M.list() returns a list of all the mailboxes
        status, mailboxes = self.mail_client.list()
        if status == 'OK':
            print "Mailboxes:"
            for mailbox in mailboxes:
                print mailbox
         
        mailbox_list = []

        # Now we select the specific folder we are interested in
        ## Run the function we defined above to loop over all emails in this folder
        ## The function will return the subject and date of each email, and write to a local .txt file
        status, emails = self.mail_client.select(self.config['EMAIL_FOLDER'])
        if status == 'OK':
            print "Processing mailbox...\n"
            self.process_mailbox()     
            self.mail_client.close()
        else:
            print "ERROR: Unable to open mailbox ", status
         
        self.mail_client.logout()

def main():
    '''
    Downloads emails from gliders
    '''
    parser = ArgumentParser(description=main.__doc__)
    parser.add_argument('-c', '--config', help='Configuration file')
    parser.add_argument('-o', '--output', help='Output directory')
    args = parser.parse_args()
    if args.config is None:
        sys.stderr.write('Please specify a configuration')
        parser.print_help()
        sys.exit(1)

    with open(args.config, 'r') as f:
        config = yaml.load(f.read())

    if args.output:
        config['OUTPUT_DIRECTORY'] = args.output

    processor = GliderEmailProcessor(config)
    processor.process()

    sys.exit(0)

if __name__ == '__main__':
    main()

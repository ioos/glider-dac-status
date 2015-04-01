from flask import current_app as app
import sys
import imaplib
import getpass
import email
import email.header
import datetime


 # Define a function to retrieve emails
def process_mailbox(M):
    """
    Do something with emails messages in the folder.  
    """
    config = app.config['GLIDER_EMAIL']
    rv, data = M.search(None, "ALL")
    if rv != 'OK':
        print "No messages found!"
        return
    for num in data[0].split():
        rv, data = M.fetch(num, '(RFC822)')
        if rv != 'OK':
            print "ERROR getting message", num
            return
        
        msg = email.message_from_string(data[0][1])
        decode = email.header.decode_header(msg['Subject'])[0]
        subject = unicode(decode[0])
        print 'Message %s: %s' % (num, subject)
        print 'Raw Date:', msg['Date']
        print "Writing message ", num
        f = open('%s/%s.txt' %(config["OUTPUT_DIRECTORY"], num), 'wb')
        f.write(data[0][1])
        f.close() 
        #print msg
        # Now convert to local date-time
        date_tuple = email.utils.parsedate_tz(msg['Date'])
        if date_tuple:
            local_date = datetime.datetime.fromtimestamp(
                email.utils.mktime_tz(date_tuple))
            print "Local Date:", \
                local_date.strftime("%a, %d %b %Y %H:%M:%S")

def process():
    config = app.config['GLIDER_EMAIL']

    # open connection to gmail 
    M = imaplib.IMAP4_SSL('imap.gmail.com')
     
    # Most imaplib functions return a tuple
    ## first object is a status ('OK')
    ## Second object is some output
    status, data = M.login(config['EMAIL_ACCOUNT'], config['EMAIL_PASSWORD'])

     
    print status, data
     
     # M.list() returns a list of all the mailboxes
    status, mailboxes = M.list()
    if status == 'OK':
        print "Mailboxes:"
        print mailboxes
     
    mailbox_list = []

    # Now we select the specific folder we are interested in
    ## Run the function we defined above to loop over all emails in this folder
    ## The function will return the subject and date of each email, and write to a local .txt file
    status, emails = M.select(config['EMAIL_FOLDER'])
    if status == 'OK':
        print "Processing mailbox...\n"
        process_mailbox(M)     
        M.close()
    else:
        print "ERROR: Unable to open mailbox ", status
     
    M.logout()

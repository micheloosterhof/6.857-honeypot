import output_parser as op
from pprint import pprint
import enchant
import xlsxwriter
import requests
from time import sleep
import json

ENGLISH = enchant.Dict('en_US')

class Analytics:
    def __init__(self, sessions):
        
        self.sessions = sessions

        login_attempts = {} # username to password dict (password to count)
        passwd_ct = {} # password tuples

        # count up passwords
        for session in self.sessions.values():
            for event in session.events:
                if 'login attempt' in event.description[0]:
                    attempt = dict(event.description[1:])
                    passwd_ct = login_attempts.get(attempt['username'], {})
                    passwd_ct[attempt['password']] = passwd_ct.get(attempt['password'], 0) + 1
                    login_attempts[attempt['username']] = passwd_ct

        self.passwd_ct = passwd_ct
        self.login_attempts = login_attempts

    def ip_to_logins(self):
        ip_to_logins = {}
        for session in self.sessions.values():
            events = [e for e in session.events if 'login attempt' in e.description[0]]
            ip = session.d['src_ip']                 
            ip_to_logins[ip] = ip_to_logins.get(ip, 0) + len(events)

        return ip_to_logins

    def ip_to_successes(self):
        ip_to_successes = {}
        for session in self.sessions.values():
            events = [e for e in session.events if e.event_id == 'cowrie.login.success']
            ip = session.d['src_ip']
            ip_to_successes[ip] = ip_to_successes.get(ip, 0) + len(events)

        return ip_to_successes

    def login_analysis(self):
        # sort passwords by frequency
        for (username, pw_ct) in reversed(sorted(self.login_attempts.items(), key=lambda (k,v):len(v))):
            print "________________________"
            print "USERNAME: ", username
            p = sorted(pw_ct.items(), key=lambda (k,v):v)
            p.reverse()
            pprint(p)


    # Calculate average password guess length
    # return tuple containing (avg length over all unique guesses, avg length weighted by frequency)
    def avg_guessed_pw_lengths(self):

        # average length of unique passwords attempted 
        lengths = [len(k) for k in self.passwd_ct]
        avg_length_unique = sum(lengths) / float(len(lengths))

        # average password length weighted by frequency 
        lengths = [len(k) for k in self.passwd_ct for i in range(self.passwd_ct[k])]
        avg_weighted = sum(lengths) / float(len(lengths))

        return (avg_length_unique, avg_weighted)

    # return list of guesses that were valid words
    def english_words(self):

        passwords = [key for l in a.login_attempts.values() for key in l for i in range(l[key])]
        for p in passwords:
            print p
        valid = [w for w in passwords if len(w) > 0 and str(w).isalpha() and ENGLISH.check(w)]
        return valid

    # Calculate frequency with which all English word guesses were made 
    def get_words(self):
        d = {}
        for word in self.english_words():
            d[word] = d.get(word, 0) + 1
        return d

    # Calculate how many password guesses were numbers-only
    def get_number_count(self):
        pws = [p for p in self.passwd_ct if str(p).isdigit()]
        return len(pws)

    # Calculate # of usernames where hackers guessed username == password
    def username_equals_password_count(self):
        usernames = [u for (u, pw_ct) in self.login_attempts.items() if u in pw_ct]
        return len(usernames)
    
    def ip_session_counts(self):
        ip_counts = {}
        for k in self.sessions.keys():
            ip = self.sessions[k].d['src_ip']
            ip_counts[ip] = ip_counts.get(ip, 0) + 1

        return ip_counts

    def ip_intel(self, contact_email):
        data = {}
        IPs = self.ip_session_counts().keys()
        workbook = xlsxwriter.Workbook('intel_data.xlsx')
        worksheet = workbook.add_worksheet()
        worksheet.write(0,0, 'IP Address')
        worksheet.write(0,1, 'IP Intel Result')
        row = 1

        for i in IPs:
            r = requests.get('http://check.getipintel.net/check.php?ip=%s&contact=%s&flags=f' % (i, contact_email))
            print '%s : %s' % (i, r.text)
            data[i] = r.text
            worksheet.write(row, 0, i)
            worksheet.write(row, 1, data[i])
            row += 1
            sleep(5) # API is rate-limited 

        workbook.close()
        return data
        

    def ip_locs(self):

        data = {}
        IPs = self.ip_session_counts().keys()
        for i in IPs:
            print "IP %s of %s" % (str(IPs.index(i)), str(len(IPs)))
            r = requests.get('https://tools.keycdn.com/geo.json?host=%s' % i)
            try: 
                j = json.loads(r.text)
                print j['data']['geo']
                data[i] = j
            except Exception:
                print "failed for IP %s: response code %s, text %s" % (i, r.status_code, r.text)
                data[i] = None

            sleep(2) # API is rate-limited 

        workbook = xlsxwriter.Workbook('loc_data.xlsx')
        worksheet = workbook.add_worksheet()
        headings = ['IP Address', 'Latitude', 'Longitude', 'Country', 'Region', 'City', 'Postal Code', 'ISP', 'Host', 'ASN']
        keys = ['ip', 'latitude', 'longitude', 'country_name', 'region', 'city', 'postal_code', 'isp', 'host', 'asn']

        for i in range(len(headings)):
            worksheet.write(0,i, headings[i])

        row = 1

        for i in IPs:
            if data[i] == None or data[i]['status'] != 'success':
                worksheet.write(row, 0, i)
                row += 1
                continue
            entry = data[i]['data']['geo']
            for j in range(len(keys)):
                key = keys[j]
                val = entry[key]
                worksheet.write(row, j, val)
            row += 1

        workbook.close()

# take in a text file where each line is a new value
# return a dictionary containing counts of each item 
# (useful for counting data in .xls file)
def count_vals(filename):
    vals = {}
    f = open(filename, 'r')
    lines = [x.rstrip() for x in list(f)]
    for line in lines:
        vals[line] = vals.get(line, 0) + 1
    return vals

def merge_sessions(prefix, date_list):
    # create an analytics object with sessions across all logs merged together
    all_sessions = {}

    for l in date_list:
        o = op.OutputParser(filename=prefix+l)
        all_sessions.update(o.sessions)

    combined_analytics = Analytics(all_sessions)
    return combined_analytics

PREFIX = 'cowrie.json.2016_'
DATES = ['4_20','4_21','4_22', '4_23', '4_24', '4_25', '4_26', '4_27', '4_28', '4_29', '4_30']

# a = merge_sessions(PREFIX, DATES)

# a.english_words()

res = count_vals('pw.txt')

vals = [k for k in res if len(k) > 0 and k.isdigit()]


print len(vals)
print len(res)


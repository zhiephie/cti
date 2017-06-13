import inspect
import time
import datetime, calendar

s = '201;232;7055;250;1;1;CONNECTION_CLEAR'
a = s.split(";")[-1:]
# atau 
# a = s.rsplit(';', 1)
# i'm <coded-out>
print(a[0])

def test(*args):
    keys = args
    l = len(keys)
    # for i, key in enumerate(keys):
    # s = list(keys)
    query = ""
    # print(l, s[1])
    for i, key in enumerate(keys):
        query += key
        if i < l:
            query += ":"
        # if l >= 1:
        #     result = [item for item in s]
        # else:
        #     result = [item[0] for item in s]
    
    return query.split(":")[-2:]

print(test('a', 'b', 'c', 'b'))



def myfunc2(*args, **kwargs):
   for a in args:
       print a
   for k,v in kwargs.iteritems():
       print "%s = %s" % (k, v)

# myfunc2('a', 'b', 'b', a=1234)
print(datetime.datetime.now())

# Get first value
ext = s.split(";", 1)[0]

# Get second value
# ext = s.split(";", 2)[1]

print(ext)

from datetime import datetime
s1 = '10:33:26'
s2 = '11:15:49' # for example
FMT = '%H:%M:%S'
tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)

print(tdelta)

def add_months(sourcedate,months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = min(sourcedate.day,calendar.monthrange(year,month)[1])
    return datetime.date(year,month,day)

def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

print get_sec('1:23:45')
print get_sec('0:04:15')
print get_sec('0:00:25')

FMT = '%H:%M:%S'
delta = datetime.strptime("10:10:29", FMT) - datetime.strptime("09:10:10", FMT)
print(delta)

print(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))

print get_sec('0:00:45')


l = ['a', 'b']
if 1 in range(len(l)):
    print('ok')
else:
    print("none")

print(time.strftime('%Y-%m-%d'))
inDate = "2017-05-31 00:00:00"
dt = inDate[0:10]
print(dt)

ww = datetime.now().replace(microsecond=0)
www = str(ww)
print(www.split(':'))
from datetime import datetime
import pytz

HST = pytz.timezone('Pacific/Honolulu')
datetime_hst = datetime.now(HST)
print("Date & Time in HST : ", 
      datetime_hst.strftime('%b %d, %I:%M %p %Z'))
test = "123"
print(test[1])
testint = int(test[1])
print (testint)

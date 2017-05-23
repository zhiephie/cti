s = '106;230;1;5005;251;202;;;OFFERED'
a = s.split(";")[-1:]
# atau 
# a = s.rsplit(';', 1)
print(a[0])
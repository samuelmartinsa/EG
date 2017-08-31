from urllib2 import urlopen
f = urlopen('http://www.python.org/')
print f.read(100)
import re
import requests
from pymongo import MongoClient
from time import time

connection = MongoClient("mongodb://localhost:27017")
db = connection.bigdata1db

url = "https://www.flipkey.com/"
page = requests.get(url)

destinations = re.findall(r'<div class="caption">[\s]*(.*?)[\s]*<span class="count">', page.text, flags = 0)
dest_urls = re.findall(r'<li class="destination">[\s]*<a href="(.*?)">', page.text, flags = 0)
dest_urls = [url[:-1] + dest_url for dest_url in dest_urls]

for i in range(len(destinations)):
    destination_obj = {}
    destination_obj['name'] = destinations[i]
    destination_obj['properties'] = []
    print(destinations[i])
    dest_page = requests.get(dest_urls[i])
    if (destinations[i] == 'Destin' or destinations[i] == 'Myrtle Beach' or destinations[i] == 'San Diego'):
        properties = re.findall(r'<h3 class="pc-title">[\s]*<a href="[^"]*?" target="_blank">(.*?)</a>', dest_page.text, flags = 0)
        prices = re.findall(r'<p class="pc-price">[\s]*([0-9$]*?)[\s]*</p>', dest_page.text, flags = 0)
        properties_urls = re.findall(r'<h3 class="pc-title">[\s]*<a href="([^"{}]*?)"', dest_page.text, flags = 0)
    else:
        properties = re.findall(r'target="_blank" data-stop-propagation>[\s]*([^{}]*?)[\s]*</a>', dest_page.text, flags = 0)
        prices = re.findall(r'<p class="price">[\s]*(.*?)[\s]*</p>', dest_page.text, flags = 0)
        properties_urls = re.findall(r'<div class="rentalUnitInfo group">[\s]*<h3>[\s]*<a href="([^{}]*?)" target="_blank" data-stop-propagation>', dest_page.text, flags = 0)

    sleeps = re.findall(r'Sleeps (.*?)[\s]*</p>', dest_page.text, flags = 0)

    #print(properties)
    
    print(len(sleeps))
    print(len(prices))
    print(len(properties))
    print(len(properties_urls))

    for j in range(len(properties)):
        property_page = requests.get(properties_urls[j])
        general_amenities_html_list = re.findall(r'<h4>General</h4>[\s]*<hr/>[\s]*<ul class="group">[\s]*(.*?)[\s]*</ul>', property_page.text, re.DOTALL)
        general_amenities = []
        if (len(general_amenities_html_list) > 0):
            general_amenities = re.findall(r'<li><i class="icon icon-checkmark"></i>(.*?)</li>', general_amenities_html_list[0], flags = 0)
        
        property_obj = {}
        property_obj['name'] = properties[j]
        property_obj['max_sleeps'] = int(sleeps[j])
        property_obj['general_amenities'] = general_amenities
        property_obj['price'] = int(prices[j][1:])
        t = str(time())
        point_index = t.index('.')
        #to have an unique id to access properties inside destination
        property_obj['timestamp_id'] = t[:point_index] + t[point_index+1:]
        destination_obj['properties'].append(property_obj)
    db.destinations.insert(destination_obj)
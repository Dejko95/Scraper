from flask import Flask, request, render_template, redirect
from pymongo import MongoClient
from time import time

connection = MongoClient("mongodb://localhost:27017")
db = connection.bigdata1db

app = Flask(__name__)

def clear(query):
    if query == "null":
        return ""
    return query

@app.route('/')
def index():
    return redirect("http://127.0.0.1:5000/search/1/10/null/null/null/null/null/null", code=302)

@app.route("/list/<int:page>/<int:per_page>")
def homepage(page, per_page):
    property_results = list(db.destinations.aggregate([{"$unwind": "$properties"}, {"$skip": (page - 1) * per_page}, {"$limit": per_page}]))
    return render_template('results.html', property_results = property_results, page = page, per_page = per_page)

@app.route("/search/<int:page>/<int:per_page>/<dest_query>/<prop_query>/<sleep_query>/<price_query>/<amts_query>/<sort_by>")
def search(page, per_page, dest_query, prop_query, sleep_query, price_query, amts_query, sort_by):
    pipeline = []
    pipeline.append({"$unwind": "$properties"})

    dest_query = clear(dest_query)
    prop_query = clear(prop_query)
    sleep_query = clear(sleep_query)
    price_query = clear(price_query)
    amts_query = clear(amts_query)
    sort_by = clear(sort_by)
    if dest_query:
        pipeline.append({"$match": {"name": {"$regex": dest_query}}})
    if prop_query:
        pipeline.append({"$match": {"properties.name": {"$regex": prop_query}}})
    if sleep_query:
        if (sleep_query[0] == '<'):
            pipeline.append({"$match": {"properties.max_sleeps": {"$lt": int(sleep_query[1:])}}})
        elif (sleep_query[0] == '>'):
            pipeline.append({"$match": {"properties.max_sleeps": {"$gt": int(sleep_query[1:])}}})
        else:
            pipeline.append({"$match": {"properties.max_sleeps": int(sleep_query)}})
    if price_query:
        if (price_query[0] == '<'):
            pipeline.append({"$match": {"properties.price": {"$lt": int(price_query[1:])}}})
        elif (price_query[0] == '>'):
            pipeline.append({"$match": {"properties.price": {"$gt": int(price_query[1:])}}})
        else:
            pipeline.append({"$match": {"properties.price": int(price_query)}})
    if amts_query:
        pipeline.append({"$match": {"properties.general_amenities":  amts_query}})
    if sort_by:
        if sort_by.startswith("dest"):
            criteria = "name"
            order = int(sort_by[4:])
        elif sort_by.startswith("prop"):
            criteria = "properties.name"
            order = int(sort_by[4:])
        elif sort_by.startswith("sleep"):
            criteria = "properties.max_sleeps"
            order = int(sort_by[5:])
        elif sort_by.startswith("price"):
            criteria = "properties.price"
            order = int(sort_by[5:])
        elif sort_by.startswith("amts"):
            criteria = "properties.general_amenities"
            order = int(sort_by[4:])
        pipeline.append({"$sort": {criteria: order}})
    pipeline.append({"$skip": (page - 1) * per_page})
    pipeline.append({"$limit": per_page})
    property_results = list(db.destinations.aggregate(pipeline))
    return render_template('results.html', property_results = property_results, page = page, per_page = per_page, dest_query = dest_query, prop_query = prop_query, sleep_query = sleep_query, price_query = price_query, amts_query = amts_query, sort_by = sort_by)

@app.route("/addProperty/<destination>/<name>/<sleeps>/<price>/<amenities_list>/<timestamp_id>")
def addProperty(destination, name, sleeps, price, amenities_list, timestamp_id):
    try:
        property_obj = {}
        property_obj['name'] = name
        property_obj['max_sleeps'] = int(sleeps)
        amenities_list = clear(amenities_list)
        property_obj['general_amenities'] = amenities_list.split(",")
        property_obj['general_amenities'] = [item.strip() for item in property_obj['general_amenities']]
        property_obj['price'] = int(price)
        if (timestamp_id == 'null'):
            t = str(time())
            point_index = t.index('.')
            timestamp_id = t[:point_index] + t[point_index+1:]
        property_obj['timestamp_id'] = timestamp_id
        #existing destination
        if db.destinations.find({"name": destination}).count() > 0:
            db.destinations.update({"name": destination}, {"$push": {"properties": property_obj}})
        else:
            #new destination
            destination_obj = {}
            destination_obj['name'] = destination
            destination_obj['properties'] = []
            destination_obj['properties'].append(property_obj)
            db.destinations.insert(destination_obj)
        return "Successfully added."
    except:
        return "Inserting failed."

@app.route("/removeProperty/<destination>/<property_timestamp_id>")
def removeProperty(destination, property_timestamp_id):
    try:
        db.destinations.update({"name": destination}, {"$pull": {"properties": {"timestamp_id": property_timestamp_id}}})
        return "Successfully removed."
    except:
        return "Removing failed."

@app.route("/editProperty/<destination>/<name>/<sleeps>/<price>/<amenities_list>/<property_timestamp_id>")
def editProperty(destination, name, sleeps, price, amenities_list, property_timestamp_id):
    try:
        response = removeProperty(destination, property_timestamp_id)
        if (response == "Successfully removed."):
            response = addProperty(destination, name, sleeps, price, amenities_list, property_timestamp_id)
            if (response == "Successfully added."):
                return "Successfully edited."
            else:
                return "Edit failed."
        else:
            return "Edit failed."
    except:
        return "Edit failed."

if __name__ == "__main__":
    app.run()
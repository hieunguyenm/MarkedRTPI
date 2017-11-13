from flask import Flask, render_template
from urllib.request import urlopen
import json
import markdown2
from time import time
from datetime import datetime
import xml.etree.cElementTree as et
import pymysql.cursors
from lxml import html as lh
from re import search
from raven.contrib.flask import Sentry

application = Flask(__name__)

red_line = ("Saggart", "Fortunestown", "Citywest Campus", "Cheeverstown", "Fettercairn", "Tallaght", "Hospital",
            "Cookstown", "Belgard", "Kingswood", "Red Cow", "Kylemore", "Bluebell", "Blackhorse", "Drimnagh",
            "Goldenbridge", "Suir Road", "Rialto", "Fatima", "James's", "Heuston", "Museum", "Smithfield",
            "Four Courts", "Jervis", "Abbey Street", "Busáras", "Connolly", "George's Dock",
            "Mayor Square - NCI", "Spencer Dock", "The Point")
green_line = ("Brides Glen", "Cherrywood", "Laughanstown", "Carrickmines", "Ballyogan Wood", "Leopardstown Valley",
              "The Gallops", "Glencairn", "Central Park", "Sandyford", "Stillorgan", "Kilmacud", "Balally",
              "Dundrum",
              "Windy Arbour", "Milltown", "Cowper", "Beechwood", "Ranelagh", "Charlemont", "Harcourt",
              "St. Stephen's Green")

sentry = Sentry(application, dsn='')

@application.route('/bus')
def index():
    return 'RTPI'


@application.route('/bus/<stop>')
def bus_query(stop):
    db_conn = pymysql.connect(host='localhost', user='rtpi',
                              password='')
    db_cursor = db_conn.cursor()

    try:
        stop_number = int(stop)
    except ValueError:
        return "Error"

    query = "SELECT Street, Name FROM stopnames WHERE Code = '{}'".format(
        stop_number)
    db_cursor.execute(query)
    db_cursor.close()

    markdown_body = "# Stop {}\n\n".format(stop_number)

    for response in db_cursor:
        street = response[0]
        name = response[1]

        if not isinstance(street, str) or street == name:
            markdown_body += "{}\n\n".format(name)
        else:
            markdown_body += "{}, {}\n\n".format(name, street)

    markdown_body = markdown2.markdown(markdown_body)

    markdown_table = render_bus_table(stop)

    markdown_table = markdown2.markdown(markdown_table, extras=["tables"])

    markdown_time = "\n***Real time data at {} UTC.***".format(datetime.fromtimestamp(
        time()).strftime('%Y-%m-%d %H:%M:%S'))
    markdown_time = markdown2.markdown(markdown_time)

    return render_template('bus_template.html', title="Stop {} Timetable".format(stop_number),
                           body_content=markdown_body, table_content=markdown_table, request_time=markdown_time,
                           stop_id=stop_number, street=street, name=name)


@application.route('/rail/<station>')
def rail_query(station):
    rail_url = "https://api.irishrail.ie/realtime/realtime.asmx/getStationDataByCodeXML?StationCode="
    in_list = "  * "

    station_name_index = 2
    origin_index = 6
    destination_index = 7
    location_index = 11
    due_index = 12
    late_index = 13
    ex_arrival_index = 14
    ex_depart_index = 15
    sch_arrival_index = 16
    sch_depart_index = 17

    url_data = urlopen(rail_url + str(station)).read().decode('utf-8')
    markdown_data = "# "

    root = et.fromstring(url_data)

    if root:
        station_name = root[0][station_name_index].text

        markdown_data += "{} Station\n\n*Real time data at {} UTC.*\n\n".format(station_name,
                                                                                datetime.fromtimestamp(
                                                                                    time()).strftime(
                                                                                    '%Y-%m-%d %H:%M:%S'))

        for child in root:
            if child[station_name_index].text != child[origin_index].text:
                markdown_data += "* **{}**\n" \
                                 "{}**Origin:** {}\n" \
                                 "{}**Due in:** {}\n" \
                                 "{}**Late by:** {}\n" \
                                 "{}**Expected arrival:** {}\n" \
                                 "{}**Scheduled arrival:** {}\n" \
                                 "{}**Last location:** {}\n\n".format(child[destination_index].text,
                                                                      in_list, child[origin_index].text,
                                                                      in_list, child[due_index].text,
                                                                      in_list, child[late_index].text,
                                                                      in_list, child[ex_arrival_index].text,
                                                                      in_list, child[sch_arrival_index].text,
                                                                      in_list, str(child[location_index].text))
            else:
                markdown_data += "* **{}**\n" \
                                 "{}**Origin:** {}\n" \
                                 "{}**Due in:** {}\n" \
                                 "{}**Late by:** {}\n" \
                                 "{}**Expected departure:** {}\n" \
                                 "{}**Scheduled departure:** {}\n" \
                                 "{}**Last location:** {}\n\n".format(child[destination_index].text,
                                                                      in_list, child[origin_index].text,
                                                                      in_list, child[due_index].text,
                                                                      in_list, child[late_index].text,
                                                                      in_list, child[ex_depart_index].text,
                                                                      in_list, child[sch_depart_index].text,
                                                                      in_list, str(child[location_index].text))
    else:
        return 'Error'

    markdown_html = markdown2.markdown(markdown_data)
    return render_template('rail_template.html', title=station_name + " Timetable", body_content=markdown_html,
                           station_id=station, name=station_name)


@application.route('/luas/<line>/<number>')
def luas_query(line, number):
    try:
        id_number = int(number)
    except ValueError:
        return "Error"

    luas_url = "https://www.luas.ie/luaspid.html?get="
    outbound = "&direction=Outbound"
    inbound = "&direction=Inbound"
    luas_table_header = "| Destination | Due time |\n|:---:|:---:|\n"
    ticker_regex = '<div class="ticker__item">(.+?)</div>'

    if line == "red" and 0 <= id_number < len(red_line):
        if id_number == 26:
            stop = "Bus%E1ras"
            title = "Busáras Luas Stop"
        else:
            stop = red_line[id_number]
            title = "{} Luas Stop".format(red_line[id_number])
        markdown_data = "# {} Luas Stop\n\n## Inbound\n\n{}".format(red_line[id_number], luas_table_header)
    elif line == "green" and 0 <= id_number < len(green_line):
        stop = green_line[id_number]
        title = "{} Luas Stop".format(green_line[id_number])
        markdown_data = "# {} Luas Stop\n\n## Inbound\n\n{}".format(green_line[id_number], luas_table_header)
    else:
        return 'Error'

    id_stop = "{}/{}".format(line, number)

    inbound_response = urlopen("{}{}{}".format(luas_url, stop, inbound)).read().decode('UTF-8')
    outbound_response = urlopen("{}{}{}".format(luas_url, stop, outbound)).read().decode('UTF-8')

    inbound_page = lh.fromstring(inbound_response)
    outbound_page = lh.fromstring(outbound_response)

    if inbound_page[0][0] is not None:
        for i in range(int(len(inbound_page[0]) / 2)):
            markdown_data += "| {} | {} |\n".format(inbound_page[0][2 * i].text, inbound_page[0][2 * i + 1].text)
    else:
        markdown_data += "| - | - |"

    markdown_data += "\nLuas updates: *{}*\n\n## Outbound\n\n{}".format(search(ticker_regex, inbound_response).group(1),
                                                                        luas_table_header)

    if outbound_page[0][0] is not None:
        for i in range(int(len(outbound_page[0]) / 2)):
            markdown_data += "| {} | {} |\n".format(outbound_page[0][2 * i].text, outbound_page[0][2 * i + 1].text)
    else:
        markdown_data += "| - | - |"

    markdown_data += "\nLuas updates: *{}*\n\n***Real time data at {} UTC.***".format(search(
        ticker_regex, outbound_response).group(1), datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S'))

    markdown_html = markdown2.markdown(markdown_data, extras=["tables"])

    return render_template('luas_template.html', title=title, body_content=markdown_html, stop_id=id_stop,
                           name=title[:-10])


@application.route("/api/rendered/bus/<stop>")
def api_bus_table(stop):
    try:
        stop_number = int(stop)
    except ValueError:
        return "Error"

    data = render_bus_table(stop_number)
    return markdown2.markdown(data, extras=["tables"])


def render_bus_table(stop_number):
    bus_url = "https://data.dublinked.ie/cgi-bin/rtpi/realtimebusinformation?stopid="
    table_header = "| Route | Destination | Origin | Due |\n|:---:|:---:|:---:|:---:|\n"

    json_response = urlopen(bus_url + str(stop_number)).read().decode('utf-8')
    json_data = json.loads(json_response)

    error_code = int(json_data['errorcode'])

    if error_code != 0:
        empty_table = "{}{}".format(table_header, "| - | - | - | - |")
        return empty_table

    number_of_results = json_data['numberofresults']
    results = json_data['results']

    markdown_data = table_header

    for i in range(0, number_of_results):
        try:
            due_time = int(results[i]['duetime'])
        except ValueError:
            due_time = results[i]['duetime']

        markdown_data += "| **{}** | {} | {} | {}{}\n".format(results[i]['route'], results[i]['destination'],
                                                              results[i]['origin'], due_time,
                                                              (" min |" if isinstance(due_time, int) else " |"))

    return markdown_data


def render_rail_list(station):
    rail_url = "https://api.irishrail.ie/realtime/realtime.asmx/getStationDataByCodeXML?StationCode="
    in_list = "  * "

    station_name_index = 2
    origin_index = 6
    destination_index = 7
    location_index = 11
    due_index = 12
    late_index = 13
    ex_arrival_index = 14
    ex_depart_index = 15
    sch_arrival_index = 16
    sch_depart_index = 17

    url_data = urlopen(rail_url + str(station)).read().decode('utf-8')
    markdown_data = "# "

    root = et.fromstring(url_data)

    if root:
        markdown_data += "{} Station\n\n*Real time data at {} UTC.*\n\n".format(root[0][station_name_index].text,
                                                                                datetime.fromtimestamp(
                                                                                    time()).strftime(
                                                                                    '%Y-%m-%d %H:%M:%S'))

        for child in root:
            if child[station_name_index].text != child[origin_index].text:
                markdown_data += "* **{}**\n" \
                                 "{}**Origin:** {}\n" \
                                 "{}**Due in:** {}\n" \
                                 "{}**Late by:** {}\n" \
                                 "{}**Expected arrival:** {}\n" \
                                 "{}**Scheduled arrival:** {}\n" \
                                 "{}**Last location:** {}\n\n".format(child[destination_index].text,
                                                                      in_list, child[origin_index].text,
                                                                      in_list, child[due_index].text,
                                                                      in_list, child[late_index].text,
                                                                      in_list, child[ex_arrival_index].text,
                                                                      in_list, child[sch_arrival_index].text,
                                                                      in_list, str(child[location_index].text))
            else:
                markdown_data += "* **{}**\n" \
                                 "{}**Origin:** {}\n" \
                                 "{}**Due in:** {}\n" \
                                 "{}**Late by:** {}\n" \
                                 "{}**Expected departure:** {}\n" \
                                 "{}**Scheduled departure:** {}\n" \
                                 "{}**Last location:** {}\n\n".format(child[destination_index].text,
                                                                      in_list, child[origin_index].text,
                                                                      in_list, child[due_index].text,
                                                                      in_list, child[late_index].text,
                                                                      in_list, child[ex_depart_index].text,
                                                                      in_list, child[sch_depart_index].text,
                                                                      in_list, str(child[location_index].text))
    else:
        return 'Error'


if __name__ == "__main__":
    application.run(host='0.0.0.0')

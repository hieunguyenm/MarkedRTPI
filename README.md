# MarkedRTPI

Markdown-style Dublin Real Time Passenger Information website in Python

## Usage

The code is currently running on [https://rtpi.nguyenhi.eu](https://rtpi.nguyenhi.eu)

All usage instructions are on the website above.

## Information

The code is written in Python and is deployed with Flask.

The code relies on the Python module, `markdown2`, to turn Markdown text into HTML. That data is then put into a Jinja2 template and relayed to NGiNX acting as a reverse proxy, communicating via uWSGI.

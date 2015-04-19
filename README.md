cloudflare-ddns
===============

Introduction
------------

A script for dynamically updating CloudFlare DNS IPv4 and IPv6 records.  You can use CloudFlare to host DNS for a domain on their free plan, even if you disable all their proxying features.

thatjpk's great script didn't support updating AAAA records (IPv6), so I heavily modified it to include a few more features as well:
- Both IPv4 and IPv6 support (A and AAAA records) in one script and config
- Support for multiple domains and subdomains in one script and config
- Can check for a file on your webserver to determine if the IP has changed at all (easing the load on the public IP check servers)

Dependencies
------------

You'll need a python interpreter and the following libraries:

 - ConfigParser (Ubuntu: `apt-get install python-configparser`)
 - [Requests](http://docs.python-requests.org/en/latest/) (Ubuntu: `apt-get install python-requests`)

Usage
-----

First, a few assumptions:

  - You have a CloudFlare account.
  - You're using CloudFlare to host DNS for a domain you own.
  - You have at least one A or AAAA record in CloudFlare you intend to dynamically update.

### Basic Configuration

To use this utility, modify the `cloudflare_config.ini` file.  Create one section for every domain you want to update and add all the subdomains you want to update to the respective section. If you want to update the naked domain name, too, add it to the list of subdomains. For example, I might want to update just the main naked domain name 'mydomain.com':

    [mydomain.com]
    CF_Subdomains: mydomain.com

Or I might want to update 'home.mydomain.com' and both 'myotherdomain.com' and 'test.myotherdomain.com':

    [mydomain.com]
    CF_Subdomains: home
    
    [myotherdomain.com]
    CF_Subdomains: myotherdomain.com,test

### Detecting an IP change

In normal mode, the script will check the A and AAAA records for any of those (sub-)domains, compare them to your current public IPv4 and IPv6 addresses and update them if necessary.

If you run a webserver on your dynamic host, instead of polling your public IPs from a remote server periodically, the script can also check for a file on your webserver first. When it can load the file and the key in it matches the key in your config, your IPs obviously haven't changed. If there is an error or mismatch, it will assume the IPs have changed, determine the new ones by contacting a remote server and run the DDNS update. In order to use this, set 'Check_Enable: True' in the config file and set check URLs for IPv4 and IPv6. These should point to a text file on your webserver which contains an arbitrary string. This string needs to be identical to the 'Check_Key' option in the config file. The check URLs for IPv4 and IPv6 should return the key only when accessed via IPv4 or IPv6 respectively. This can be done by placing the files on different subdomains with only an A record for the IPv4 URL and only an AAAA record for the IPv6 URL.

### Running

To do a one-off update of your DNS record, simply run `python cloudflare_ddns.py cloudflare_config.ini` from your terminal.
The script will determine your public IPv4 and IPv6 addresses and automatically update the CloudFlare DNS records along with them.

Because dynamic IPs can change regularly, it's recommended that you run this utility periodically in the background to keep the CloudFlare records up-to-date.

Just add a line to your [crontab](http://en.wikipedia.org/wiki/Cron) and let cron run it for you at a regular interval.

    # Every 15 minutes, check the current public IPs, and update the records on CloudFlare.
    */15 * * * * /path/to/code/cloudflare-ddns.py /path/to/code/cloudflare_config.ini >> /var/log/cloudflare_ddns.log

This example will update the record every 15 minutes.  You'll want to be sure that you insert the correct paths to reflect were the codebase is located.
The redirection (`>>`) to append to a log file is optional, but handy for debugging if you notice the DNS record is not staying up-to-date.  The script tries to print something useful to stdout any time it runs. If you find the "unchanged" messages too chatty, set 'Quiet' to true in the config and stdout will only get messages when the IP actually changed, or when there's an error.

If the program encounters an issue while attempting to update CloudFlare's records, it will print the failure response CloudFlare returns. Check your configuration file for accurate information and try again.

Further information
-------------------

If you want to learn more about the CloudFlare API, you can read on
[here](http://www.cloudflare.com/docs/client-api.html).

Credits and Thanks
------------------

 - [thatjpk](https://github.com/thatjpk) for figuring out all the complicated things ;-)
 - [CloudFlare](https://www.cloudflare.com/) for having an API and otherwise generally being cool.
 - [ipv6-test.com](http://ipv6-test.com/) for making grabbing your public IP from a script super easy.


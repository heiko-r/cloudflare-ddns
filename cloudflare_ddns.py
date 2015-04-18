#!/usr/bin/env python
#
# CloudFlare DDNS script.
#
# usage:
#   cloudflare_ddns.py [config]
#
# See README for details
#

import requests
import json
import time
import os
import sys
import ConfigParser


# CloudFlare api url
CLOUDFLARE_URL = 'https://www.cloudflare.com/api_json.html'

# Location of this script.
SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))

# If a command-line argument is provided, use that as the config file.
if len(sys.argv) == 1:
    CONFIG_FILE = os.path.join(SCRIPT_ROOT, "cloudflare_config.ini")
else:
    CONFIG_FILE = os.path.join(SCRIPT_ROOT, sys.argv[1])

def main():
    now = time.ctime()
    
    config = ConfigParser.RawConfigParser()
    
    # Check for config file
    if not os.path.isfile(CONFIG_FILE):
        msg = \
            "Configuration file not found. Please review the README and try " \
            "again."
        log(now, 'error', '(no conf)', '(no conf)', msg)
        raise Exception(msg)
    
    # Read config file
    config.readfp(open(CONFIG_FILE))
    
    # Call check URL to determine if IPv4 or IPv6 address has changed
    if config.getboolean('DEFAULT', 'Check_Enable'):
        cf_key4_response = requests.get(config.get('DEFAULT', 'Check_IPv4'), verify=config.getboolean('DEFAULT', 'Check_SSLVerify'))
        cf_key6_response = requests.get(config.get('DEFAULT', 'Check_IPv6'), verify=config.getboolean('DEFAULT', 'Check_SSLVerify'))
    
    # If a key can be retrieved and it equals the one in the config, do nothing.
    # Else, run the update script.
    if not (config.getboolean('DEFAULT', 'Check_Enable') and \
            cf_key4_response.status_code > 199 and cf_key4_response.status_code < 300 and \
            cf_key6_response.status_code > 199 and cf_key6_response.status_code < 300 and \
            cf_key4_response.text.strip() == config.get('DEFAULT', 'Check_Key') and \
            cf_key6_response.text.strip() == config.get('DEFAULT', 'Check_Key')):
        # Check public IP addresses
        public_ipv4 = requests.get(config.get('DEFAULT', 'Discover_IPv4')).text.strip()
        public_ipv6 = requests.get(config.get('DEFAULT', 'Discover_IPv6')).text.strip()
        
        # Create a list of record IDs we want to update
        for domain in config.sections():
            # Prepare parameters for API call
            cf_params = {
                'a': 'rec_load_all',
                'tkn': config.get('DEFAULT', 'CF_Key'),
                'email': config.get('DEFAULT', 'CF_Email'),
                'z': domain,
                'o': 0
            }
            
            # Create list of subdomains for this domain from config option
            subdomains = config.get(domain, 'CF_Subdomains').split(',')
            
            # Results may be paginated, so loop over each page.
            has_more = True
            while has_more:
                # Make API call
                cf_response = requests.get(CLOUDFLARE_URL, params=cf_params)
                if cf_response.status_code < 200 or cf_response.status_code > 299:
                    msg = "CloudFlare returned an unexpected status code: {}".format(
                        cf_response.status_code
                        )
                    log(now, 'error', domain, public_ip, msg)
                    raise Exception(msg)
                
                response = json.loads(cf_response.text)
                for record in response["response"]["recs"]["objs"]:
                    if (
                        (record["type"] == 'A' or record["type"] == 'AAAA') and \
                        (
                            record["name"] in subdomains or \
                            record["name"].rsplit('.' + domain, 1)[0] in subdomains
                            )
                        ):
                        # If this record already has the correct IP, we return early
                        # and don't do anything.
                        if ((record["type"] == 'A' and record["content"] == public_ipv4) or (record["type"] == 'AAAA' and record["content"] == public_ipv6)):
                            if not config.getboolean('DEFAULT', 'Quiet'):
                                log(now, 'unchanged', record["name"] + " (" + domain + ")", public_ipv4)
                        else:
                            record_id = record["rec_id"]
                            
                            # Now we've got a record_id and all the good stuff to actually update the
                            # record, so let's do it.
                            
                            if record["type"] == 'A':
                                new_ip = public_ipv4
                                new_ttl = config.get('DEFAULT', 'TTL_A')
                            else:
                                new_ip = public_ipv6
                                new_ttl = config.get('DEFAULT', 'TTL_AAAA')
                            
                            cf_upd_params = {
                                'a': 'rec_edit',
                                'tkn': config.get('DEFAULT', 'CF_Key'),
                                'id': record_id,
                                'email': config.get('DEFAULT', 'CF_Email'),
                                'z': domain,
                                'type': record["type"],
                                'ttl': new_ttl,
                                'name': record["name"],
                                'content': new_ip,
                                'service_mode': config.get('DEFAULT', 'CF_Service_Mode')
                                }
                            
                            cf_upd_response = requests.get(CLOUDFLARE_URL, params=cf_upd_params)
                            if cf_response.status_code < 200 or cf_response.status_code > 299:
                                msg = "CloudFlare returned an unexpected status code: {}".format(
                                    response.status_code
                                    )
                                log(now, 'error', record["name"] + " (" + domain + ")", new_ip, msg)
                                raise Exception(msg)
                            upd_response = json.loads(cf_upd_response.text)

                            if upd_response["result"] == "success":
                                log(now, 'updated', record["name"] + " (" + domain + ")", new_ip)
                            else:
                                msg = "Updating record failed with the result '{}'".format(
                                    upd_response["result"]
                                    )
                                log(now, 'error', record["name"] + " (" + domain + ")", new_ip, msg)
                                raise Exception(msg)
                
                # Check if the response was paginated and if so, call another page
                if response["response"]["recs"]["has_more"]:
                    # Set a new start point
                    cf_params["o"] = response["response"]["recs"]["count"]
                else:
                    has_more = False
    else:
        if not config.getboolean('DEFAULT', 'Quiet'):
            log(now, 'Key check successful', '', '')
    
def log(timestamp, status, subdomain, ip_address, message=''):
    print(
        "{date}, {status:>10}, {a:>10}, {ip}, '{message}'".format(
            date=timestamp,
            status=status,
            a=subdomain,
            ip=ip_address,
            message=message
            )
        )
    return

if __name__ == '__main__':
    main()


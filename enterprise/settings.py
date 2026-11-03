"""Course 2's enterprise track settings. Fill these in before 00_preflight.

The first four must name the same catalog, schema and volume you used in course 1 (its lnl/config.py): course 2 carries
on with the pipeline and tables course 1 built there, and lands the deliveries it handed over. Mock data only.
"""

ENTERPRISE_CATALOG = ""            # the catalog course 1 used (ENTERPRISE_CATALOG in course 1's lnl/config.py)
ENTERPRISE_SCHEMA = "lnl_{user}"   # the same schema rule as course 1; {user} becomes your user name
ENTERPRISE_VOLUME = "landing"      # the same volume as course 1: the landing folder and the handoff live in it
ENTERPRISE_SERVERLESS = True       # serverless jobs; False runs the job's notebook task on ENTERPRISE_CLUSTER_ID
ENTERPRISE_CLUSTER_ID = ""         # classic only: an all-purpose cluster for the job's notebook task
RESTRICTED_GROUP = ""              # account group allowed to see race and religion, e.g. "restricted-readers"
ANALYST_GROUP = ""                 # account group that gets read access to the published view
ALERT_EMAILS = []                  # who gets job-failure email; empty = you
ALERT_DESTINATIONS = []            # display names of notification destinations an admin set up (PagerDuty, webhook)

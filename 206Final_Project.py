import requests
import json
import sqlite3
import facebook

graph = facebook.GraphAPI(access_token = 'EAACEdEose0cBAMf5iq2hGNpZCvbNqV62kd1pdjSkOg2iszRuahgCMlFLZCUMglikHRL5SC1H87Bt9CCsJjwOtSZBZCWXRyMocdQTrAonZBitZCTpf706OxFwAi09SYnZBhsQfJQUC0XSiqQWP54ngU8ZCGCnRkdHphWdj1HFMZB1pFq5IbGN2tKPFvZBBPLVFwjeWccwDEn5iSBxU8MkbCpvdOOIRLRYyMR5sZD')

friends = graph.get_connections(id = 'me', connection_name = 'friends')

print(friends)
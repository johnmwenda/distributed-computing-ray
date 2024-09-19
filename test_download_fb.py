#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import requests as r
import wget

filedir = os.path.join('~/Downloads')

try:
    LINK = "https://video.fnbo10-1.fna.fbcdn.net/o1/v/t29/f1/m49/3558566391082853.mp4?efg=eyJ2aWRlb19pZCI6MjIzNTcwODAzODMyOTk2LCJ2ZW5jb2RlX3RhZyI6ImRhc2hfbGl2ZV9tZF9mcmFnXzJfdmlkZW8ifQ&_nc_ht=video.fnbo10-1.fna.fbcdn.net&_nc_cat=107&strext=1&ccb=9-4&oh=00_AfAOmu4JXYtNnlVJyKfTQ5SXiTO7tfFNcwtq05BIh8W31A&oe=66319CF5&_nc_sid=9ca052"
    html = r.get(LINK)
    sdvideo_url = re.search('sd_src:"(.+?)"', html.text)[1]
except r.ConnectionError as e:
    print("OOPS!! Connection Error.")
except r.Timeout as e:
    print("OOPS!! Timeout Error")
except r.RequestException as e:
    print("OOPS!! General Error or Invalid URL", e)
except (KeyboardInterrupt, SystemExit):
    print("Ok ok, quitting")
    sys.exit(1)
except TypeError as e:
    print(e)
    print("Video May Private or Invalid URL")
else:
    sd_url = sdvideo_url.replace('sd_src:"', '')
    print("\n")
    print("Normal Quality: " + sd_url)
    print("[+] Video Started Downloading")
    wget.download(sd_url, filedir)
    sys.stdout.write(ERASE_LINE)
    print("\n")
    print("Video downloaded")
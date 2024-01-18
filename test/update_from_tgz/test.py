import logging

import autoupdate

logging.basicConfig(level=logging.DEBUG)

autoupdate.check_archive('https://www.picave.org/latest')

import subprocess
import re
from subprocess import Popen, PIPE
res = subprocess.Popen(['ip', 'address', 'show'], stdout=PIPE, stderr=PIPE)
res = res.communicate()[0].decode('utf-8').split('\n')
pattern1 = r'\d: (.+):'
pattern2 = r'inet (?P<joe>\d+\.\d+\.\d+\.\d+/\d+)'
interfaces = {}
last_int = ''
for line in res:
    try:
        match1 = re.search(pattern1, line).group(1)
        last_int = match1
        print(last_int)
    except AttributeError:
        pass
    try:
        match2 = re.search(pattern2, line).group('joe')
        interfaces[last_int] = match2
    except AttributeError:
        continue

print(interfaces)
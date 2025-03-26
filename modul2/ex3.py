import subprocess
import re

result = subprocess.Popen(['ifconfig'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

output, _ = result.communicate()
pattern = r'(?m)^(\S+):.*?\n\s+inet\s+(\d+\.\d+\.\d+\.\d+)'
output = output.decode("utf-8")

print(type(str(output)))
print(str(output))

found = re.findall(pattern, output)
print(type(found))

dict1 = {}
for item in found:
     dict1[item[0]] = item[1]
print(dict1)
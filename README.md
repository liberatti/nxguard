# NXGuard

Gerenciar um openresty com modsecurity para proteção de APIs

## Frameworks
+ Jinja2
+ python

```conf
server:
  {% for host in unbound.hosts %}
  local-data: "{{ host.name }} A {{ host.address }}"
  {% endfor %}

  do-ip6: {{ unbound.ipv6_enabled | lower }}
```

```python
from jinja2 import Environment, FileSystemLoader
import os, yaml, xml.etree.ElementTree as ET

env = Environment(loader=FileSystemLoader('/usr/local/opnsense/service/templates'))

template = env.get_template('OPNsense/Unbound/unbound.conf')
config = parse_config_xml('/conf/config.xml')

output = template.render(unbound=config['unbound'])
O resultado é salvo no destino definido no manifest.yaml.
```
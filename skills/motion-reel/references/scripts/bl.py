#!/usr/bin/env python3
"""Send a python file to the running Blender MCP socket (no second Blender). Usage: bl.py file.py"""
import socket,json,sys
code=open(sys.argv[1]).read()
s=socket.create_connection(('localhost',9876),timeout=3000)
s.sendall(json.dumps({"type":"execute_code","params":{"code":code}}).encode())
buf=b''
while True:
    d=s.recv(65536)
    if not d: break
    buf+=d
    try: r=json.loads(buf); break
    except: pass
print(r.get('result',{}).get('result',r) if isinstance(r.get('result'),dict) else r)

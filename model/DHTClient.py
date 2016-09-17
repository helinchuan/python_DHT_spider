#!/usr/bin/env python
# coding=utf-8
'''
Created on 2016��9��17��

@author: he
'''
from struct import unpack,pack
     
def num_to_dotted(n):  
    d = 256 * 256 * 256 
    q = []  
    while d > 0:  
        m, n = divmod(n, d)  
        q.append(str(m))  
        d /= 256 
    return '.'.join(q)  
 
def decode_nodes(nodes):  
    n = []  
    nrnodes = len(nodes) / 26 
    nodes = unpack("!" + "20sIH" * nrnodes, nodes)  
    for i in range(nrnodes):  
        nid, ip, port = nodes[i * 3], num_to_dotted(nodes[i * 3 + 1]), nodes[i * 3 + 2]  
        n.append((nid, ip, port))  
    return n  
 
#decode_nodes函数的反作用函数如下:  
def dotted_to_num(ip):  
    hexn = ''.join(["%02X" % long(i) for i in ip.split('.')])  
    return long(hexn, 16)  
 
def encode_nodes(nodes):  
    n = []  
    for node in nodes:  
        n.extend([node.nid, dotted_to_num(node.ip), node.port])  
    return pack("!" + "20sIH" * len(nodes), *n) 

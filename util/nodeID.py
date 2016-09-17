#!/usr/bin/env python
#coding=utf-8
'''
Created on 2016年9月16日

@author: he
'''
from hashlib import sha1  
from random import randint  

def node_id():  
    """  
    把爬虫"伪装"成正常node, 一个正常的node有ip, port, node ID三个属性, 因为是基于UDP协议,   
    所以向对方发送信息时, 即使没"明确"说明自己的ip和port时, 对方自然会知道你的ip和port,   
    反之亦然. 那么我们自身node就只需要生成一个node ID就行, 协议里说到node ID用sha1算法生成,   
    sha1算法生成的值是长度是20 byte, 也就是20 * 8 = 160 bit, 正好如DHT协议里说的那范围: 0 至 2的160次方,   
    也就是总共能生成1461501637330902918203684832716283019655932542976个独一无二的node.   
    ok, 由于sha1总是生成20 byte的值, 所以哪怕你写SHA1(20)或SHA1(19)或SHA1("I am a 2B")都可以,   
    只要保证大大降低与别人重复几率就行. 注意, node ID非十六进制,   
    也就是说非FF5C85FE1FDB933503999F9EB2EF59E4B0F51ECA这个样子, 即非hash.hexdigest().  
    """ 
    hash = sha1()  
    s = ""  
    for i in range(20):  
        s += chr(randint(0, 255))  
    hash.update(s)  
    return hash.digest()  
 
def intify(nid):  
    """这是一个小工具, 把一个node ID转换为数字. 后面会频繁用到.""" 
    assert len(nid) == 20 
    return long(nid.encode('hex'), 16) #先转换成16进制, 再变成数字 


    
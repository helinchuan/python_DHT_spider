#!/usr/bin/env python
#coding=utf-8
'''
Created on 2016年9月16日

@author: he
'''

'''
协议里说道, table里有bucket, bucket里有node, 每个bucket有K个node, 目前K=8, 即每个bucket有8个node. 由于table范围是0到2的160次方, 那么一个table最多能有(2的160次方)/K那么多的bucket.

OK, 按照OOP编程思想来说, 那么肯定会有table, bucket, node这3个类, 无OOP的, 自己看着办.

由于是基于Kademila而写, 所以我习惯上把这三个类名变为KTable, KBucket, KNode:
'''
import time
import nodeID.intify as intify


class KNode:  
    def __init__(self, nid, ip, port):  
        """  
        nid就是node ID的简写, 就不取id这么模糊的变量名了. __init__方法相当于别的OOP语言中的构造方法,   
        在python严格来说不是构造方法, 它是初始化, 不过, 功能差不多就行.  
        """ 
        self.nid = nid #node ID  
        self.ip = ip  
        self.port = port  
 
    #以下两个方法非Python程序员不需关心  
    def __eq__(self, other):  
        return self.nid == other.nid  
    def __ne__(self, other):  
        return self.nid != other.nid  
 
 
class KBucket:  
    def __init__(self, min, max):  
        """  
        min和max就是该bucket负责的范围, 比如该bucket的min:0, max:16的话,   
        那么存储的node的intify(nid)值均为: 0到15, 那16就不负责, 这16将会是该bucket后面的bucket的min值.   
        nodes属性就是个列表, 存储node. last_accessed代表最后访问时间, 因为协议里说到,   
        当该bucket负责的node有请求, 回应操作; 删除node; 添加node; 更新node; 等这些操作时,   
        那么就要更新该bucket, 所以设置个last_accessed属性, 该属性标志着这个bucket的"新鲜程度". 用linux话来说, touch一下.  
        这个用来便于后面说的定时刷新路由表.  
        """ 
        self.min = min #最小node ID数字值  
        self.max = max #最大node ID数字值  
        self.nodes = [] #node列表  
        self.last_accessed = time() #最后访问时间  
 
    def nid_in_range(self, nid):  
        """判断指定的node ID是否属于该bucket的范围里""" 
        return self.min <= intify(nid) < self.max  
 
    def append(self, node):  
        """  
        添加node, 参数node是KNode实例.  
 
        如果新插入的node的nid属性长度不等于20, 终止.  
        如果满了, 抛出bucket已满的错误, 终止. 通知上层代码进行拆表.  
        如果未满, 先看看新插入的node是否已存在, 如果存在, 就替换掉, 不存在, 就添加,  
        添加/替换时, 更新该bucket的"新鲜程度".  
        """ 
        if len(node.nid) != 20: return 
        if len(self.nodes) < 8:  
            if node in self.nodes:  
                self.nodes.remove(node)  
                self.nodes.append(node)  
            else:  
                self.nodes.append(node)  
            self.last_accessed = time()  
        else:  
            raise BucketFull
 
 
class KTable:  
    """  
    该类只实例化一次.  
    """ 
    def __init__(self, nid):  
        """  
        这里的nid就是通过node_id()函数生成的自身node ID. 协议里说道, 每个路由表至少有一个bucket,   
        还规定第一个bucket的min=0, max=2的160次方, 所以这里就给予了一个buckets属性来存储bucket, 这个是列表.  
        """ 
        self.nid = nid #自身node ID  
        self.buckets = [KBucket(0, 2 ** 160)] #存储bucket的例表  
 
    def append(self, node):  
        """添加node, 参数node是KNode实例""" 
 
        #如果待插入的node的ID与自身一样, 那么就忽略, 终止接下来的操作.  
        if node.nid == self.nid: return   
 
        #定位出待插入的node应该属于哪个bucket.  
        index = self.bucket_index(node.nid)  
        bucket = self.buckets[index]  
 
        #协议里说道, 插入新节点时, 如果所归属的bucket是满的, 又都是活跃节点,   
        #那么先看看自身的node ID是否在该bucket的范围里, 如果不在该范围里, 那么就把  
        #该node忽略掉, 程序终止; 如果在该范围里, 就要把该bucket拆分成两个bucket, 按范围"公平平分"node.  
        try:  
            bucket.append(node)  
        except BucketFull:
            if not bucket.nid_in_range(self.nid): return #这个步骤很重要, 不然递归循环很狂暴, 导致程序死翘翘.  
            self.split_bucket(index)   
            self.append(node)  
 
    def bucket_index(self, nid):  
        """  
        定位bucket的所在索引  
 
        传一个node的ID, 从buckets属性里循环, 定位该nid属于哪个bucket, 找到后, 返回对应的bucket的索引;   
        没有找到, 说明就是要创建新的bucket了, 那么索引值就是最大索引值+1.  
        注意: 为了简单, 就采用循环方式. 这个恐怕不是最有效率的方式.  
        """ 
        for index, bucket in enumerate(self.buckets):  
            if bucket.nid_in_range(nid):  
                return index  
        return index          
 
    def split_bucket(self, index):  
        """  
        拆表  
 
        index是待拆分的bucket(old bucket)的所在索引值.   
        假设这个old bucket的min:0, max:16. 拆分该old bucket的话, 分界点是8, 然后把old bucket的max改为8, min还是0.   
        创建一个新的bucket, new bucket的min=8, max=16.  
        然后根据的old bucket中的各个node的nid, 看看是属于哪个bucket的范围里, 就装到对应的bucket里.   
        各回各家,各找各妈.  
        new bucket的所在索引值就在old bucket后面, 即index+1, 把新的bucket插入到路由表里.  
        """ 
        old = self.buckets[index]  
        point = old.max - (old.max - old.min)/2 
        new = KBucket(point, old.max)  
        old.max = point  
        self.buckets.insert(index + 1, new)  
        for node in old:  
            if new.nid_in_range(node.nid):  
                new.append(node)  
        for node in new:  
            old.remove(node)          
 
    def find_close_nodes(self, target):  
        """  
        返回与目标node ID或infohash的最近K个node.  
 
        定位出与目标node ID或infohash所在的bucket, 如果该bucuck有K个节点, 返回.   
        如果不够到K个节点的话, 把该bucket前面的bucket和该bucket后面的bucket加起来, 只返回前K个节点.  
        还是不到K个话, 再重复这个动作. 要注意不要超出最小和最大索引范围.  
        总之, 不管你用什么算法, 想尽办法找出最近的K个节点.  
        """ 
        K=8
        nodes = []  
        if len(self.buckets) == 0: return nodes  
        index = self.bucket_index(target)  
        nodes = self.buckets[index].nodes  
        min = index - 1 
        max = index + 1 
        while len(nodes) < K and (min >= 0 or max < len(self.buckets)):  
            if min >= 0:  
                nodes.extend(self.buckets[min].nodes)  
            if max < len(self.buckets):  
                nodes.extend(self.buckets[max].nodes)  
            min -= 1 
            max += 1 
 
        num = intify(target)  
        nodes.sort(lambda a, b, num=num: cmp(num^intify(a.nid), num^intify(b.nid)))  
        return nodes[:K] #K是个常量, K=8 

#异常类
class BucketFull(BaseException):
    def __init__(self, value):
         self.value = value
    def __str__(self):
         return repr(self.value)
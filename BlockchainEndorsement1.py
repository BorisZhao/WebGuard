from flask import Flask, request
import rsa as rsa
import hashlib
import threading
import requests
import json
import ast
import random
import multiprocessing
import base64

# TODO(赵博): 实现区块链背书节点，要求能够接收web端发送的访问记录、HTML还有哈希，能上链，实现区块封装还有区块链的首尾连接，实现挖矿
# HTML deliverer

class Block(object):#赵博：定义区块数据结构
    def __init__(self):
        self.dict={}
        self.dict['transaction']={}#赵博：交易信息列表，用字典表示，方便转JSON传输
        self.dict['index']=0#赵博：区块序号
        self.dict['nonce']=0#赵博：随机数，初始化成0
        self.dict['preHash']=''#赵博：上一个区块的哈希
        self.dict['hash']=''#赵博：本区块的哈希，初始化成空串
        self.dict['id']=''#赵博：挖矿节点的ID，直接使用端口号
        #self.addTrans=False

    def print(self):#赵博：定义一个打印区块信息的成员函数
        print("==============================================================================")
        print('From:%s'%self.dict['id'])
        print("Index:%d" % int(self.dict['index']))
        print("Previous Block Hash:%s" % self.dict['preHash'])
        print("Hash:%s" % self.dict['hash'])
        print("PoW:%d" % int(self.dict['nonce']))
        print("Transactions:")
        #
        print(self.dict['transaction'])
        print("==============================================================================")

    def add_transaction(self):#赵博：这个成员函数被调用的时候，把交易池里所有的交易全部添加进正在挖的区块
        global transactionPool
        global cnt
        # for transaction in transactionPool:
        #     self.dict['transaction'][str(cnt)]=str(transaction)
        #     transactionPool.remove(str(transaction))
        #     cnt+=1
        while not transactionPool.empty():
            self.dict['transaction'][str(cnt)] = str(transactionPool.get())
            # print(str(cnt))
            cnt=cnt+1


def mining():
    global block
    global ledger
    global transactionPool
    global acceptNewBlock
    global cnt
    while True:#赵博：挖矿是个死循环
        # ledger[-1].print()
        #赵博：初始化新区块
        block.dict['index']=ledger[-1].dict['index']+1#赵博：新区块的标号要比区块链头的区块序号大一
        block.dict['nonce']=random.randint(0,1000)#赵博：感觉每次搞随机数效率太低了，不如按照传统方法，从随机数开始每次加一
        block.dict['preHash']=ledger[-1].dict['hash']#赵博：把上一个区块的哈希存进新区块
        block.dict['hash']=''#赵博：区块哈希初始化
        block.dict['id']='5004'#赵博：直接使用本机端口号
        block.dict['transaction']={}#赵博：交易列表初始化成空字典
            # transactionPool.clear()
        # block.print()
        if not transactionPool.empty():#赵博：交易池非空将把所有池中交易全部打包进区块
            block.add_transaction()
        # block.print()
        while block.dict['hash'][:5]!='00000' :#赵博：要求哈希高n位为零
            block.dict['nonce']+=1#赵博：每次nonce加一，重新计算哈希
            hash = hashlib.sha256()
            #赵博：哈希要保证区块上所有信息都不可篡改
            hash.update(str(block.dict['index']).encode('utf-8'))
            hash.update(str(block.dict['nonce']).encode('utf-8'))
            hash.update(str(block.dict['preHash']).encode('utf-8'))
            for transaction in block.dict['transaction']:
                hash.update(block.dict['transaction'][transaction].encode('utf-8'))
            block.dict['hash']=hash.hexdigest()#赵博：将哈希以十六进制字符串的形式存入字典
        # if acceptNewBlock:
        #     continue
        cnt=0#赵博：将交易计数器清零
        block.dict['transaction']=json.dumps(block.dict['transaction'])#赵博：将交易列表转为字符串，否则传输时会丢数据
        try:
            for addr in nodeList:
                result=requests.post(f"http://127.0.0.1:{addr}/block_listener",data=block.dict)#区块广播
        except:
            continue
        print(result)


app = Flask(__name__)

@app.route('/block_listener', methods=['POST'])#厉成毅：将/block_listener与接受区块函数绑定
def add_block():
    global acceptNewBlock
    global ledger
    newBlock=Block()
    # acceptNewBlock = True
    dict = request.form.to_dict()#厉成毅：将区块信息从接收信息中抽取出，转为字典
    #赵博：提取新区快信息
    newBlock.dict['index']=int(dict['index'])
    newBlock.dict['nonce']=int(dict['nonce'])
    newBlock.dict['preHash']=str(dict['preHash'])
    newBlock.dict['hash']=str(dict['hash'])
    newBlock.dict['id']=str(dict['id'])
    newBlock.dict['transaction']=ast.literal_eval(dict['transaction'])
    #赵博：使用同样方法计算区块哈希
    new_hash=hashlib.sha256()
    new_hash.update(str(newBlock.dict['index']).encode('utf-8'))
    new_hash.update(str(newBlock.dict['nonce']).encode('utf-8'))
    new_hash.update(str(newBlock.dict['preHash']).encode('utf-8'))
    for transaction in newBlock.dict['transaction']:
        new_hash.update(newBlock.dict['transaction'][transaction].encode('utf-8'))
    newHash=new_hash.hexdigest()
    #赵博：区块需要满足：计算哈希与区块内哈希匹配且符合难度要求，区块标号必须大于本地账本末尾区块标号
    if newHash[:5] != '00000' or newHash!=newBlock.dict['hash'] or int(newBlock.dict['index'])<=int(ledger[-1].dict['index']):
        print('Block denied')
        # acceptNewBlock = False
        return 'Block denied'
    else:
        print('block accepted')
        # newBlock.print()
        ledger.append(newBlock)#赵博：将合法区块加入链尾
        ledger[-1].print()
        # for b in ledger:
        #     b.print()
        # block.print()
        # del transactionPool[:len(dict['transaction'])]
        # acceptNewBlock = False
        return 'Block accepted'

@app.route('/transaction_listener',methods=['POST'])#厉成毅：将/transaction_listener与接受交易信息函数绑定
def add_transaction():
    global transactionPool
    try:#赵博：如果是Web注册信息，需要单独处理
        textHash = request.form.to_dict()
        # print(type(textHash))
        print(textHash['hash'])
        print(textHash['HTML'])
        transactionPool.put(textHash['hash'])#添加进交易池
        transactionPool.put(textHash['HTML'])
    except:
        try:#赵博：一般信息直接上链即可
            print(json.dumps(request.form.to_dict()))
            transactionPool.put(json.dumps(request.form.to_dict()))
            # print(transactionPool)
        except:
            return 'Not valid transaction',500
    return 'confirmed',200

@app.route('/verify', methods=['POST'])#厉成毅：将/verify与查询比对哈希的函数绑定
def query():
    dict=request.form.to_dict()#赵博：抽取客户端发送的哈希
    #赵博：查询这个哈希是否已经上链
    for b in ledger:
        for key in b.dict['transaction'].keys():
            print(key,b.dict['transaction'][key])
            if b.dict['transaction'][key]==dict['hash']:
                return 'True',200
    return 'False',200

acceptNewBlock=False
ledger = []#赵博：本地帐本
cnt=0#赵博：交易池内交易数
transactionPool=multiprocessing.Queue()#赵博：交易池，存放交易信息，线程安全
#创建创世区块
genesis_block=Block()
genesis_block.dict['hash']='2c8d90f16775a1aac97a64c2718f4cc38f3c1ab7c5f63799b7662ced594895ac'
genesis_block.dict['preHash']='0'
genesis_block.dict['index']=0
genesis_block.dict['nonce']=0
ledger.append(genesis_block)

nodeList=[5001,5002,5003,5004]
block=Block()#赵博：临时区块，存储正在挖矿的区块
# print(id(newBlock),id(block),id(ledger),id(ledger[-1]))
#block.print()
#ledger[-1].print()

def app_run():#厉成毅：定义主线程
    app.run(port=5001,threaded=True)

if __name__ == '__main__':
    mining=threading.Thread(target=mining)
    mining.start()#赵博：开启挖矿线程
    main_app = threading.Thread(target=app_run)
    main_app.start()



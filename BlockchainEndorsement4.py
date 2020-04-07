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

# TODO(ZB): implement endorsement node 1
# HTML deliverer

class Block(object):
    def __init__(self):
        self.dict={}
        self.dict['transaction']={}
        self.dict['index']=0
        self.dict['nonce']=0
        self.dict['preHash']=''
        self.dict['hash']=''
        self.dict['id']=''
        #self.addTrans=False

    def print(self):
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

    def add_transaction(self):
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
    while True:
        # ledger[-1].print()
        block.dict['index']=ledger[-1].dict['index']+1
        block.dict['nonce']=random.randint(0,1000)
        block.dict['preHash']=ledger[-1].dict['hash']
        block.dict['hash']=''
        block.dict['id']='5004'
        block.dict['transaction']={}
            # transactionPool.clear()
        # block.print()
        if not transactionPool.empty():
            block.add_transaction()
        # block.print()
        while block.dict['hash'][:5]!='00000' :
            block.dict['nonce']+=1
            hash = hashlib.sha256()
            hash.update(str(block.dict['index']).encode('utf-8'))
            hash.update(str(block.dict['nonce']).encode('utf-8'))
            hash.update(str(block.dict['preHash']).encode('utf-8'))
            for transaction in block.dict['transaction']:
                hash.update(block.dict['transaction'][transaction].encode('utf-8'))
            block.dict['hash']=hash.hexdigest()
        # if acceptNewBlock:
        #     continue
        cnt=0
        block.dict['transaction']=json.dumps(block.dict['transaction'])
        try:
            for addr in nodeList:
                result=requests.post(f"http://127.0.0.1:{addr}/block_listener",data=block.dict)
        except:
            continue
        print(result)


app = Flask(__name__)

@app.route('/block_listener', methods=['POST'])
def add_block():
    global acceptNewBlock
    global ledger
    newBlock=Block()
    # acceptNewBlock = True
    dict = request.form.to_dict()
    newBlock.dict['index']=int(dict['index'])
    newBlock.dict['nonce']=int(dict['nonce'])
    newBlock.dict['preHash']=str(dict['preHash'])
    newBlock.dict['hash']=str(dict['hash'])
    newBlock.dict['id']=str(dict['id'])
    newBlock.dict['transaction']=ast.literal_eval(dict['transaction'])
    new_hash=hashlib.sha256()
    new_hash.update(str(newBlock.dict['index']).encode('utf-8'))
    new_hash.update(str(newBlock.dict['nonce']).encode('utf-8'))
    new_hash.update(str(newBlock.dict['preHash']).encode('utf-8'))
    for transaction in newBlock.dict['transaction']:
        new_hash.update(newBlock.dict['transaction'][transaction].encode('utf-8'))
    newHash=new_hash.hexdigest()
    if newHash[:5] != '00000' or newHash!=newBlock.dict['hash'] or int(newBlock.dict['index'])<=int(ledger[-1].dict['index']):
        print('Block denied')
        # acceptNewBlock = False
        return 'Block denied'
    else:
        print('block accepted')
        # newBlock.print()
        ledger.append(newBlock)
        ledger[-1].print()
        # for b in ledger:
        #     b.print()
        # block.print()
        # del transactionPool[:len(dict['transaction'])]
        # acceptNewBlock = False
        return 'Block accepted'

@app.route('/transaction_listener',methods=['POST'])
def add_transaction():
    global transactionPool
    try:
        textHash = request.form.to_dict()
        # print(type(textHash))
        print(textHash['hash'])
        print(textHash['HTML'])
        transactionPool.put(textHash['hash'])
        transactionPool.put(textHash['HTML'])
    except:
        try:
            print(json.dumps(request.form.to_dict()))
            transactionPool.put(json.dumps(request.form.to_dict()))
            # print(transactionPool)
        except:
            return 'Not valid transaction',500
    return 'confirmed',200


@app.route('/verify', methods=['POST'])
def query():
    dict=request.form.to_dict()
    for b in ledger:
        for key in b.dict['transaction'].keys():
            print(key,b.dict['transaction'][key])
            if b.dict['transaction'][key]==dict['hash']:
                return 'True',200
    return 'False',200

acceptNewBlock=False
ledger = []
cnt=0
transactionPool=multiprocessing.Queue()

genesis_block=Block()
genesis_block.dict['hash']='2c8d90f16775a1aac97a64c2718f4cc38f3c1ab7c5f63799b7662ced594895ac'
genesis_block.dict['preHash']='0'
genesis_block.dict['index']=0
genesis_block.dict['nonce']=0
ledger.append(genesis_block)

nodeList=[5001,5002,5003,5004]
block=Block()
# print(id(newBlock),id(block),id(ledger),id(ledger[-1]))
#block.print()
#ledger[-1].print()

def app_run():
    app.run(port=5004,threaded=True)

if __name__ == '__main__':
    mining=threading.Thread(target=mining)
    mining.start()
    main_app = threading.Thread(target=app_run)
    main_app.start()



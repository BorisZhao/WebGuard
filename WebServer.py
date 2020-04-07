from flask import Flask, request
import rsa
import base64
import json
import socket
import requests
import time
import hashlib
import threading

indorsementlist = [5001, 5002, 5003, 5004]

# from flask import request

#TODO(厉成毅，朴明庆):实现将网页原文以及原文哈希发布至区块链、处理客户端的访问请求、验证客户端签名、HTML文档文件的读取以及加密传输，并将客户端访问记录发布至区块链
#TODO(赵博):调试，与区块链网络对接
# HTML deliverer
app = Flask(__name__)


@app.route('/messi', methods=['GET', 'POST'])#厉成毅：将网页发送函数与/messi接口关联，方法为GET或POST
def frontpage():
    try:#朴明庆：签名验证不通过会抛异常，应该用try而不是if
        f = open('messi.txt', 'r', encoding='UTF-8')#厉成毅：打开网页HTML文本文件并读取
        page = f.read()
        f.close()
        # TODO(朴明庆):实现客户端提交的时间戳以及签名的验证
        # print(request.form.to_dict())
        dict = request.form.to_dict()#朴明庆：将存入字典的公钥、签名以及时间戳原文提取出来
        PK=dict['PK']#朴明庆：提取客户端公钥
        # print(type(dict['PK']))
        # print(type(dict['timestamp']))
        # print(type(dict['sig']))
        sig = base64.b64decode(dict['sig'].encode('utf-8'))#朴明庆：将签名提取出来，并且按照编码过程逆向解码
        #print(type(sig))
        rsa.verify(dict['timestamp'].encode('utf-8'), sig, rsa.PublicKey.load_pkcs1(PK.encode('utf-8')))#朴明庆：验证签名

    except:
        print('false')#朴明庆：输出验证未通过提示
        timestamp=time.ctime(time.time())#朴明庆：记录非法访问时间
        req={}
        req['request']=f'{request.remote_addr},{timestamp}'#厉成毅：将时间戳原文和访问来源IP关联起来
        # print(f'{request.remote_addr},{timestamp}')
        for addr in nodeList:#厉成毅：广播给区块链节点
            try:
                ret=requests.post(f'http://127.0.0.1:{addr}/transaction_listener',data=req)
                print(ret.text)
            except:
                print(f'{addr}failed')#厉成毅：节点掉线会输出提示
        #print(page)
        return "This page do not exist.",404#厉成毅：提示用户页面不存在
    else:
        print('true')#朴明庆：输出验证通过提示
        text=''
        for i in range(0,len(page),39):#朴明庆：rsa加密对明文长度有限制，切分成步长39字符的片段加密后连起来
            text+=base64.b64encode(rsa.encrypt(page[i:i+39].encode('utf-8'),rsa.PublicKey.load_pkcs1(PK.encode('utf-8')))).decode('utf-8')
        for addr in nodeList:#厉成毅：把访问信息广播给区块链
            try:
                ret=requests.post(f'http://127.0.0.1:{addr}/transaction_listener',data=dict)
                print(ret.text)
            except:
                print(f'{addr}failed')
        return text,200

nodeList=[5001,5002,5003,5004]#厉成毅：区块链节点地址

def hashing():#朴明庆：给文档打哈希
    hash = hashlib.sha256()
    f = open('messi.txt', 'r', encoding='utf-8')#朴明庆：读取网页文档
    txt = f.read()
    f.close()
    for i in range(0, len(txt), 40):#朴明庆：这里面update等同于字符串相连之后一起哈希
        hash.update(txt[i:i + 40].encode('utf-8'))
    dict={}
    dict['hash']=hash.hexdigest()#厉成毅：把哈希用十六进制形式保存成字符串，存进字典
    dict['HTML']=txt#厉成毅：把网页原文存进字典
    for addr in nodeList:#厉成毅：把字典广播给区块链
        try:
            ret = requests.post(f'http://127.0.0.1:{addr}/transaction_listener', data=dict)
            print(ret.text)
        except:
            print(f'{addr}failed')

def app_run():#厉成毅：开主线程
    app.run(port=5000, threaded=True)

if __name__ == '__main__':
    main_app=threading.Thread(target=app_run)#厉成毅：主线程启动
    main_app.start()
    h=threading.Thread(target=hashing)#厉成毅：哈希也要开个进程，启动
    h.start()

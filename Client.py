import requests
import rsa
import time
import base64
from flask import request
import webbrowser
import hashlib
import random
#TODO(厉成毅，朴明庆):实现用户提交时间戳以及对应签名，接收HTML并且解密，向区块链查询哈希，匹配的话把网页打在浏览器上，不匹配的话丢弃掉
#TODO(赵博):调试，与区块链网络对接
(PK,SK)=rsa.newkeys(1024)#朴明庆：生成的公私钥要用封装好的函数保存进两个专门的变量里
PK=PK.save_pkcs1()
SK=SK.save_pkcs1()

timestamp=time.ctime(time.time()).encode('utf-8')#朴明庆：打个时间戳
sig=rsa.sign(timestamp,rsa.PrivateKey.load_pkcs1(SK),'SHA-1')#公钥签名
sig=base64.b64encode(sig).decode('utf-8')#厉成毅：签名传不过去啊啊啊啊啊啊！！！！！！！！
#朴明庆：我看了一下好像是编码的问题，查了一下是得先用base64转成byte，再把byte编成utf8就能传了
# try:
#     # print(type(PK))
#     # print(type(timestamp))
#     # print(type(sig))
#     rsa.verify(timestamp,sig,rsa.PublicKey.load_pkcs1(PK))
#     print('true')
# except:
#     print('false')
newrequest=requests.post('http://127.0.0.1:5000/messi',data={'PK':PK,'timestamp':timestamp.decode('utf-8'),'sig':sig}).text#厉成毅：发请求到webserver
text=''
for i in range(0, len(newrequest), 172):#朴明庆：解码的步长要跟webserver对应，39字符对应的是172字节
    text+=rsa.decrypt(base64.b64decode(newrequest[i:i+172].encode('utf-8')),rsa.PrivateKey.load_pkcs1(SK)).decode('utf-8')#朴明庆：解密
    #text += base64.b64encode(rsa.encrypt(page[i:i + 50].encode('utf-8'), rsa.PublicKey.load_pkcs1(PK.encode('utf-8')))).decode('utf-8')


#print(newrequest.text)
#print(text)
nodeList=[5001,5002,5003,5004]#厉成毅：区块链节点地址表
f=open('result.html','w')#厉成毅：把收到的文件保存在result里，方便区分
f.write(text)
f.close()
hash = hashlib.sha256()#朴明庆：给文件算哈希
f = open('result.html', 'r')
txt = f.read()
for i in range(0, len(txt), 40):
    hash.update(txt[i:i + 40].encode('utf-8'))
dict = {}
dict['hash'] = hash.hexdigest()#厉成毅：把哈希放进字典

# judge=requests.post(f'http://127.0.0.1:5001/verify',data=dict).text
# print(judge,type(judge))
if requests.post(f'http://127.0.0.1:{nodeList[random.randint(0,3)]}/verify',data=dict).text=='True':#赵博：没有找到对应哈希的话会返回字符串‘false’
    webbrowser.open_new_tab('result.html')#厉成毅：我找到了在python里把HTML用浏览器打开的办法
else:
    print('Invalid page intercepted!')#厉成毅：输出提示信息，把网页丢弃掉
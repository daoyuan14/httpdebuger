#! /usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------
#   Author: clzqwdy@gmail.com
#   Name:   HttpProxy.py    ---->   HttpDebuger.py
#   Version:0.1.0
#   Python: 2.6(only, because 2.5 don't support ssl)
#------------------------------------------
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import urllib2
import urlparse
import urllib
import os, sys
import socket
import select
import threading
from subprocess import call

try:
    import ssl
    SSLEnable = True
except:
    SSLEnable = False

dirs = {}
dirs['cur'] = os.path.dirname(__file__)     # current path!
#print(dirs['cur'])      # test: .
dirs['cert'] = os.path.join(dirs['cur'], 'cert')
#print(dirs['cert'])    # test: ./cert

DEF_KEY_FILE  = os.path.join(dirs['cur'], 'root/root-key.pem')
DEF_CERT_FILE = os.path.join(dirs['cur'], 'root/root-cert.pem')
#print(DEF_KEY_FILE)     # test: ./root/root-key.pem

openssl = "C:\\Users\\clzqwdy\\Software\\OpenSSL-Win32\\bin\\openssl.exe"

class LocalRequestHandler(BaseHTTPRequestHandler):
    _lock = threading.Lock()
    
    def _read_write(self, soc, c):
        '''转发接收内容'''
        count = 0
        while 1:
            count += 1
            
            # ins: socket has in data
            # exs: socket has exception
            ins, _, exs = select.select([soc,c], [], [soc,c], 10)

            if exs:     # an exception happened!
                break
            if ins:     # have something to read
                for i in ins:
                    if i == soc:    # sock has in data, can read it
                        out = c     # then sent to connection
                    else:
                        out = soc
                    b = i.recv(8192)    # the content of reading
                    if b:
                        out.sendall(b)  # now send content of reading to out!
                        count = 0       # return to normal situation, encounter again!
            else:
                # over time
                break
            if count > 30: break    # max time of no data to send: 10*30 s
    
    def deal_with_client(self, connstream):
        data = connstream.read()
        # null data means the client is finished with us
        while data:
            connstream.write('hello!')
            data = connstream.read()
        # finished with client
        connstream.close()
    
    def do_GET(self):
        """ handle browser's GET request, and support https
        """
        
        ''' get request from client '''
        
        # check url path, just handle http(s) request
        parseResult = urlparse.urlparse(self.path)
        if (parseResult.scheme != 'http' and parseResult.scheme != 'https') or not parseResult.netloc:
            self.send_error(501, 'Unsupported scheme, such as FTP!')
            self.connection.close()
            return
        
        ''' so the following snippets are no use and wrong!
        if self.headers.has_key('Host'):
            host = self.headers['Host']     # 一般是有www的吧？yes!
            # Test: when I access http://localhost:8080/, it print [Has host, and it is:localhost:8080]
            #print( 'Has host, and it is:' + host )
        else:
            host = ''
            #print( 'Has not host!' )
        url = 'http://' + host + self.path  # so I think this path is wrong! But for localhost:8013/ it is right!
        print( url )
        # test: localhost:8013/ 所以前面应该加上个'http://' 这仅仅适用于喊localhost的本地地址
        # test: when I access http://www.baidu.com, it output: [http://www.baidu.comhttp://www.baidu.com/]
        '''
        
        # for the out website and localhost, the URL are all right!
        url = self.path
        # Test: when I access http://localhost:8080/test, it output: [http://localhost:8080/test]
        # Test: when I access http://www.google.com/notebook, it output: [http://www.google.com/notebook]
        #print( url )
        
        ''' forward request to outside and get response from outside '''
        
        # create a Request object
        #request = urllib2.Request('http://www.python.org/fish.html')   # MD，居然给我一个无效的链接
        #request = urllib2.Request('http://localhost:8013/')
        #request = urllib2.Request('http://www.baidu.com')
        request = urllib2.Request(url)
        
        # add all headers
        for key, value in self.headers.items():
            request.add_header(key, value)
            #print( 'Key: %s, Vaule: %s' % (key, value) )   # just for testing
        #request.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.9 Safari/533.4')
        # 去掉下面的编码，它不会强制让页面下载下来了
        #request.add_header('Accept', 'application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5')
        #request.add_header('Accept-Encoding', 'gzip')
        #request.add_header('Accept-Charset', 'utf-8')
        
        # modify urllib2's urlopen not to use proxy!
        proxy_handler = urllib2.ProxyHandler( {} )      # we don't need IE's proxy
        opener = urllib2.build_opener(proxy_handler)
        urllib2.install_opener(opener)  # install it globally so it can be used with urlopen. 相当于替换了urlopen()中的opener
        
        try:
            response = urllib2.urlopen(request)
            #print( response.read() )   # 一使用，下面的self.wfile.write( response.read() )就没效果了. 因为文件指针移动了
        except urllib2.HTTPError, errMsg:       # return 'HTTP Error %s: %s' % (self.code, self.msg)
            ''' forward status line to browser, when error '''
            #errNum = int( str(errMsg).split(' ')[2].split(':')[0] )     # original format: HTTP Error 404: Not Found
            errNum = errMsg.code        # 没必要上面那么麻烦吧
            ''' 这段出错提示反而不好
            if errNum == 404:
                # 一旦陷入异常, response就没有值了. 就不能指望它在错误前还是还是先把内容发过去了。
                # 否则会出现UnboundLocalError: local variable 'response' referenced before assignment的错误
                #self.wfile.write( response.read() )     # no use!!!
                self.send_error(404, 'Local proxy error, We could not access the URL you specified. Please check it!')  # it can output log info
            elif errNum == 502:
                self.send_error(502, 'Local proxy error, Invalid response from fetchserver, an occasional transmission error, or the fetchserver is too busy.')
            else:
                self.send_error(errNum)
            '''
            #self.send_error(errNum, errMsg.reason)  # But, AttributeError: 'HTTPError' object has no attribute 'reason'
            self.send_error(errNum, errMsg.msg)     # because I am in Python 2.5, I see it in urllib2.py
            print('exception1')     # 起到类似AfxMessageBox的作用
            # 仍然输出错误页面, 然后再关闭连接
            self.wfile.write( errMsg.read() )
            # 出错的情况下，直接不返回内容给本地浏览器，这样做好吗???
            # BaseHTTPRequestHandler中的所有函数都是用于proxy和本地浏览器之间的
            # 所以，我感觉self.connection还是跟本地浏览器之间的吧！yes!~(因为self不就承担的是服务器的角色嘛)
            # 那么，urllib用什么断开连接呢？！
            self.connection.close()    # 这是将proxy和本地浏览器断开连接 # BaseHTTPServer的文档中都没这个函数，估计是继承的吧.yes!!!
            return
        except urllib2.URLError, e:     # 见<Python网络编程基础> P122      # return '<urlopen error %s>' % self.reason
            #errNum = int( str(e).split(' ')[2].split(':')[0] )  # ValueError: invalid literal for int() with base 10: '(11001,'
            #self.send_error(errNum, e.reason)
            print('exception2')
            print(e.reason)
            self.connection.close()
            return
        
        #self.connection.close()    # 到底这个有没有关闭连接的功能？！ test: no use!
        # 还是因为到下面的语句时又重新创建一个了？！
        
        # forward status line to browser, 不用在这里写了
        ''' 完全不应该这样写
        #print( response.read() )    # 这边调用后，下面的self.wfile.write( response.read() )就不对了，因为文件指针已经移动
        statusLine = response.readline()    # such as, HTTP/1.0 200 OK
        #print(statusLine)  # 乱码，是不是编码问题???     # 同理，如果是response.read()，更是一大堆乱码!    # 但是为什么testUrlOpen.py没有乱码???
        #self.wfile.write(statusLine)        # 加了这一句，豆瓣的图片都显示出来了,但是页面看不出其他效果!!!But now still no response header!
        words = statusLine.split()          # 以空格为分隔符来划分
        #print(words)    # Test: ['\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x04\x03\x03\x03\x03\x02\x04\x03\x03\x03\x04\x04\x04\x05\x06']   # 可见根本没分割开来
        status = int( words[1] )    # 如果上面没分割开来，会出现的错误: IndexError: list index out of range
        reason = words[2]   # right? I want to error info
        '''
        #status = response.getcode()    # it only use for urllib, urllib2 use Expection to handle it!
        
        # 噢，在send_response()和send_header()使用前一定不能出现self.wfile.write()吧!即不能用response，因为response中就是页面的内容.
        self.send_response(200, 'Success')     # 我咋感觉应该把这句话写在上一句的前面??? 一写到上面就不ok了！页面一片空白. 感觉是因为response.read()已经失效了的缘故。还是没用
        
        # forward headers to browser, loop to call self.send_header(keyword, value)
        #print('success!')  # just to test!
        info = response.info()
        for key, value in info.items():
            self.send_header(key, value)
        self.end_headers()      # Sends a blank line, indicating the end of the HTTP headers in the response.
        
        # forward page(contents) to browser
        self.wfile.write( response.read() )     # wfile: Contains the output stream for writing a response back to the client.
        # 感觉下面这句话反而多余, need to learn it!!! 但删掉这句话后，也不再有记录信息了!!!
        
        # after all done, close our connection with client
        self.connection.close()     # has use?
        
    def do_POST(self):
        """ handle browser's POST request
        """
        # check url path, just handle http(s) request
        parseResult = urlparse.urlparse(self.path)
        if (parseResult.scheme != 'http' and parseResult.scheme != 'https') or not parseResult.netloc:
            self.send_error(501, 'Unsupported scheme, such as FTP!')
            self.connection.close()
            return
            
        # check and get length of post data
        postDataLen = 0     # 不加这句的话，下面的if-else就只有一个分支有了
        if self.headers.has_key('Content-Length'):
            postDataLen = int( self.headers['Content-Length'] )
        else:
            self.send_error(400, 'It is a unvalid post request!')        # 应该用哪个状态码???
            print('We can not get Content-Length!')
            self.connection.close()
            return
            
        # check and get post data
        if postDataLen == 0:
            postData = ''
        if postDataLen > 0:
            postData = self.rfile.read(postDataLen)     # 直接就是从数据区开始读的, 它不会把headers放在input里面的
            if len( postData ) != postDataLen:
                self.send_error(400, 'It is a bad request!')
                print('It is a bad request!')
                self.connection.close()
                return
            
        # create a Request object, and add all headers
        request = urllib2.Request(self.path)
        for key, value in self.headers.items():
            request.add_header(key, value)
        
        # modify urllib2's urlopen not to use proxy!
        proxy_handler = urllib2.ProxyHandler( {} )      # we don't need IE's proxy
        opener = urllib2.build_opener(proxy_handler)
        urllib2.install_opener(opener)  # install it globally so it can be used with urlopen. 相当于替换了urlopen()中的opener
        
        # convert post data to url encoding. Oh, no! My local browser has done this job.
        #data = urllib.urlencode( {'postdata': postData} )     # <Python网络编程基础>P120  # 我咋感觉它发来的数据已经经过url编码了???
        
        # use urlopen() to post data to outside web server, and send status code to local browser!
        try:
            response = urllib2.urlopen(request, postData)
        except urllib2.HTTPError, e:       # return 'HTTP Error %s: %s' % (self.code, self.msg)
            self.send_error(e.code, e.msg)
            print('exception1')
            self.wfile.write( e.read() )
            self.connection.close()
            return
        except urllib2.URLError, e:     # return '<urlopen error %s>' % self.reason
            print('exception2')
            print(e.reason)
            self.connection.close()
            return
        
        # forward headers to local browser
        self.send_response(200, 'Success')
        #print('success!')
        print('My post data: %s!' % postData)     # Test: ck=PrDj&mb_text=test+again
        info = response.info()
        for key, value in info.items():
            self.send_header(key, value)
        self.end_headers()
        
        # forward page(contents) to browser
        self.wfile.write( response.read() )
        self.connection.close()
        
    def do_CONNECT(self):   # 这是明文的
        if not SSLEnable:
            self.send_error(501, 'Local proxy error, HTTPS needs Python2.6 or later.')
            self.connection.close()
            return
        
        # only handle port 443's https
        #port = self.path.split(':')[2]    # http://mail.google.commail.google.com:443  # I need to test it!
        #if port != '' and port != '443':      # right???
        #    self.send_error(501, 'Local proxy error, Only port 443 is allowed for https.')
        #    self.connection.close()
        #    return
        port = 443
        
        # get outside server's Host name so that our socket object can use
        if self.headers.has_key('Host'):
            host = self.headers['Host']
        else:
            self.send_error(501, 'You must tell me the Host header!')
            self.connection.close()
            return
        
        #
        # 产生与该服务器对应的证书，并用我们的根证书进行签发
        #
        crtFile = os.path.join(dirs['cert'], host + '.crt')
        csrFile = os.path.join(dirs['cert'], host + '.csr')
        keyFile = os.path.join(dirs['cert'], host + '.key')
        # when file is not exist!
        if not os.path.isfile(crtFile) or os.path.getsize(crtFile) == 0:    # 有证书存在就可以了，另外两个可以没有
            self._lock.acquire()
            if os.path.isfile(crtFile) and os.path.getsize(crtFile) != 0:
                self._lock.release()
            else:
                try:
                    # 创建Server的私钥
                    print('----start to create server key----')
                    cmd = [openssl, 'genrsa', '-out', keyFile, '1024']
                    call(cmd)
                    print('---- end to create server key ----')
                    print('\n')
                    # 创建Server的证书请求
                    print('----start to create server req----')
                    cmd = [ openssl, 'req', '-new', '-text',
                            '-key', keyFile, '-out', csrFile,
                            '-subj', '/C=GB/ST=JiangSu/L=NJ/O=%s/OU=%s/CN=%s' % (host, host, host) ]
                    call(cmd)
                    print('---- end to create server req ----')
                    print('\n')
                    # 用CA的证书用私钥对Server的证书请求进行签名
                    print('----start to create server crt----')
                    cmd = [ openssl, 'x509', '-req', '-in', csrFile,
                            '-CA', DEF_CERT_FILE, '-CAkey', DEF_KEY_FILE,
                            '-CAcreateserial', '-days', '365', '-text',
                            '-out', crtFile ]
                    call(cmd)
                    print('---- end to create server crt ----')
                    print('\n')
                except Exception, e:
                    logging.error(e)
                    # if error, use CA's cert
                    crtFile = DEF_CERT_FILE
                    keyFile = DEF_KEY_FILE
                finally:
                    self._lock.release()
        
        # continue
        # 下面三句话必须放在放在sslSock前面，才能使网站立马得到响应!
        self.send_response(200, 'Success')
        # if deleted, and doesn't work!!!
        self.wfile.write('HTTP/1.1 200 OK\r\n')
        self.wfile.write('\r\n')
        
        # ssl communication with browser
        try:
            sslSock = ssl.wrap_socket(self.connection,
                                      server_side=True,
                                      certfile=crtFile,
                                      keyfile=keyFile)
        except ssl.SSLError, e:
            print('Exception: ssl.SSLError!')
            self.send_error(e.errno, e[1])  # right??? # file:///C:/Users/clzqwdy/Software/Python2.6/Doc/library/socket.html#socket.error
            self.connection.close()
            if sslSock is not None:     # I think sslSock is none
                print('sslSock is not None!')   # so test it!
                sslSock.close()         # note that closing the SSLSocket will also close the underlying socket
            return
        
        #self.deal_with_client(sslSock)
        #self._read_write(sslSock, self.connection)
        
        #
        # get real request from browser with ssl encryption, TLS层传给我的已经是解密后的数据了
        # But I don't know how to handle it, so next step, I will create a socket object to forward it!
        #
        firstLine = ''
        while True:
            chr = sslSock.read(1)
            # EOF?
            if chr == '':
                # bad request
                sslSock.close()
                self.connection.close()
                return
            # newline(\r\n)?
            if chr == '\r':
                chr = sslSock.read(1)
                if chr == '\n':
                    # got
                    break
                else:
                    # bad request
                    sslSock.close()
                    self.connection.close()
                    return
            # newline(\n)?
            if chr == '\n':
                # got
                break
            firstLine += chr
        #print(firstLine)    # when I access "https://www.google.com", it print "GET / HTTP/1.1"
        
        #
        # will be ready to forward https request to do_GET() and do_POST()
        # and I need a socket object connect to local proxy server to forward this request
        #
        (method, path, ver) = firstLine.split()
        if path.startswith('/'):
            url = 'https://%s' % host + path
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect( ('127.0.0.1', 8013) )
        sock.send('%s %s %s\r\n' % (method, url, ver))     # 重新写请求, 转到proxy's GET方法了
        
        # forward https request
        sslSock.settimeout(1)   # 这是socket对象拥有的方法
        while True:
            try:
                data = sslSock.read(8192)   # get data from browser with ssl
            except ssl.SSLError, e:
                if str(e).lower().find('timed out') == -1:
                    # error
                    sslSock.close()
                    self.connection.close()
                    sock.close()
                    return
                # timeout
                break
            if data != '':
                sock.send(data)     # send data to proxy's do_GET() and do_POST()
            else:
                # EOF
                break       # 那之前的数据不是没有发出去吗???
        sslSock.setblocking(True)

        # simply forward response
        while True:
            data = sock.recv(8192)  # get data from proxy's do_GET() and do_POST()      # sometimes error happened!
            if data != '':
                sslSock.write(data) # send data to browser with ssl     # sometimes error happened!
            else:
                # EOF
                break
        
        # clean
        sslSock.shutdown(socket.SHUT_WR)
        sslSock.close()
        self.connection.close()

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

if __name__ == '__main__':  # http://www.woodpecker.org.cn/share/doc/abyteofpython_cn/chinese/ch08s04.html
    # Create the object and serve requests
    serveraddr = ('', 8013)         # why not '127.0.0.1' ??
    srvr = ThreadingHTTPServer(serveraddr, LocalRequestHandler)
    srvr.serve_forever()
    
    #os.system('pause')      # 让屏幕暂停下来，而不直接闪掉.      # 貌似出错也停不下来???

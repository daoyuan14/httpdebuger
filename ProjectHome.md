## Introduction ##

HttpDebuger is a HTTP-Based Analysis and Control System used for Debugging Web Apps.

## News ##

  * 2010-06-23: Finished developing HttpDebuger v0.1.0;
  * 2010-08-25: Release HttpDebuger v0.1.0 to Open Source;

## Features ##

More details can see **this presentation**: just need to see [the last few pages](http://www.slideshare.net/clzqwdy/openssl-4472555)! Recommend it!

### Decrypt Principle ###

<img src='http://httpdebuger.googlecode.com/files/Normal-Proxy-Connect.jpg' width='800' height='250'>
<br>Figure 1: a normal SSL connection through a normal proxy<br>
<br>
<img src='http://httpdebuger.googlecode.com/files/decryptPrinciple.png' width='800' height='250'>
<br>Figure 2: through our proxy, a SSL connection has been decrypted<br>
<br>
<h2>Requirements</h2>

<ul><li>Multi-platform, but need Python: 2.5 or 2.6;<br>
</li><li>OpenSSL needed;</li></ul>

<h2>Screenshot</h2>

By the idea of "Man In the Middle", our CA could signed different certificates to different websites. In this way, we can decrypt the SSL communication, just as the following picture shows:<br>
<br>
<img src='http://httpdebuger.googlecode.com/files/Decrypt.SSLCommunication.to.Google.jpg' />
<br>Figure 3: You can see the cert of Google is signed by me:-) and we get the encrypted GET methods
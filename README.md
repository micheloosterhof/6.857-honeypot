# 6.857-honeypot
This is a final project I did along with three other MIT students for our Computer & Network Security class, 6.587, taught by Ron Rivest. 

We set up a honeypot based on on Michael Oosterhoof's [Cowrie SSH Honeypot](https://github.com/micheloosterhof/cowrie) (which is based on [Kippo](https://github.com/desaster/kippo/)). We added functionality for logging in with an SSH key. 

We hosted the honeypot using an AWS EC2 server and posted its IP address along with private keys to public GitHub repositories, and then parsed the logs we collected to study the attackers methodologies, actions, etc. 

Honeypot code is located in [/cowrie](cowrie), and parsing code along with ten days' of logs is in [/parsing](parsing). 

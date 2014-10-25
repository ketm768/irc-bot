import socket
import ssl
from random import randint

class IRCBot():
    def __init__(self, server=None, port=None, bot_nick=None,
                 bot_ident=None, mychans=None):
        if server is None:
            self.server = "orwell.freenode.net"
        else:
            self.server = server
        if port is None:
            self.port = 6697
        else:
            self.port = port
        if bot_nick is None:
            self.bot_nick = "bottybot"
        else:
            self.bot_nick = bot_nick
        if bot_ident is None:
            self.bot_ident = "bottybot"
        else:
            self.bot_ident = bot_ident
        if mychans is None:
            self.mychans = [
                "#bottybot",
                "#bottybot1"
            ]
        else:
            self.mychans = mychans

    def _connect(self):
        print("connecting to %s:%s" % (
            self.server,
            self.port)
        )
        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )
        self.ssl_sock = ssl.wrap_socket(s)
        self.ssl_sock.connect((self.server,
                              self.port))
        return self.ssl_sock


    def process_data(self, socket):
        while 1:
            data = socket.recv(4096)
            print("DATA: %s" % data)
            result = self._parse_commands(
                data,
                socket
            )
            self._send2server(result)

    def _send2server(self, result):
        if result is not None and len(result) > 0:
            print type(result)
            if isinstance(result, list):
                for each in result:
                    print("sending to server > %s" % each)
                    self.ssl_sock.send(each)
            else:
                print("sending to server > %s" % result)
                self.ssl_sock.send(result)

    def _parse_commands(self, data, socket):
        raw_server_msglist = str(data).split('\n')
        for raw_message in raw_server_msglist:
            if len(raw_message) > 1:
                section = raw_message.split(' ')

                if len(section) > 0:
                    try:
                        """ general message assignments """
                        message_source = section[0]
                        message_type = section[1]
                        message_target = section[2]

                        """ message from user vs server """
                        if "!" in message_source:
                            message_source_nick = \
                                message_source.split("!")[0][1:]

                        """ message itself (ie, 'hi there') """
                        if ":" in ' '.join(section[2:]):
                            message_content = \
                                ' '.join(section[2:]).split(':')[1]
                            print message_content
                        else:
                            message_content = ' '.join(section[2:])

                        """
                         handle initial connection process
                         send user & nick to server
                        """
                        if message_type == 'NOTICE' and "Looking up your hostname" in message_content:
                            rval = randint(0, 10)
                            self.bot_nick = self.bot_nick + str(rval)
                            ident = "USER %s 0 * :%s\nNICK %s\n" % (
                                self.bot_ident,
                                (self.bot_ident+' ') * 2,
                                self.bot_nick
                            )
                            return ident

                        """
                         connected successully, now join channels
                         code 376 = end of MOTD
                        """
                        if message_type == '376':
                            join_cmds = []
                            for chan in self.mychans:
                                cmd = "JOIN %s\n" % chan
                                join_cmds.append(cmd)
                            return join_cmds

                        """ handle channel only privmsg commands """
                        if message_target in self.mychans:
                            if message_type == 'PRIVMSG':
                                if self.is_command(message_content, "!uptime"):
                                    print "got !uptime command!"
                                    msg = "PRIVMSG %s :%s: %s\n" % (
                                        message_target,
                                        message_source_nick,
                                        self.get_uptime()
                                    )
                                return msg

                        """ handle channel and direct privmsg commands """
                        if message_target in self.bot_nick or self.mychans:
                            """ !join command """
                            if self.is_command(message_content, "!join"):
                                fmsg = message_content.split(' ')
                                if len(fmsg) > 1:
                                    response = []
                                    channel = str(
                                        message_content.split(' ')[1:][0]
                                        ).rstrip()
                                    jcmd = "JOIN %s\n" % (channel)
                                    mcmd = "PRIVMSG %s :Joining %s\n" % (
                                        message_target,
                                        channel
                                    )
                                    response.append(jcmd)
                                    response.append(mcmd)
                                    print response
                                    return response

                            """ !part command """
                            if self.is_command(message_content, "!part"):
                                fmsg = message_content.split(' ')
                                if len(fmsg) > 1:
                                    j = "PART %s\n" % (str(message_content.split(' ')[1:][0]).rstrip())
                                    print j
                                    return j
                        else:
                            print "random privmsg received, ignoring.. (%s)" % str(message_content).strip()
                    except IndexError, e:
                        print "parse error on new message type, breaking, %s" % e
                        break
            return None

    def is_command(self, message_content, cmd):
        if message_content[:len(cmd)] == cmd:
            return True
        return False

    def get_uptime(self):
        from subprocess import Popen, PIPE, STDOUT
        cmd = 'uptime'
        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
        output = p.stdout.read()
        return output

    def start(self):
        s = self._connect()
        self.process_data(s)

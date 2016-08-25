import email
import plistlib
from HTMLParser import HTMLParser

class Emlx(object):
    def __init__(self, filepath):
        self.bytecount = 0
        self.msg_data = None
        self.msg_plist = None
        self.mime_payload = [] # List containing main body and contents of attachements 
        self._parse(filepath)

    def _parse(self, filepath):
        # emlx files are split into 3 parts
        # 1. first line contains the number of bytes of the email payload
        # 2. MIME dump of Email payload
        # 3. Mac Plist attributes
        # see https://taoofmac.com/space/blog/2008/03/03/2211
        with open(filepath, "rb") as f:
            self.bytecount = int(f.readline().strip())
            self.msg_data = email.message_from_string(f.read(self.bytecount))
            self.msg_plist = plistlib.readPlistFromString(f.read())

        # Parse MIME payload from msg_data
        if self.msg_data.is_multipart():
            for part in self.msg_data.walk():
                text = self._get_text(part)
                if text:
                    self.mime_payload.append(text)
        else:
            self.mime_payload.append(self._get_text(self.msg_data))

    def _get_text(self, part):
        ctype = part.get_content_type()
        cdispo = str(part.get('Content-Disposition'))
        if ctype == 'text/plain' and 'attachment' not in cdispo:
            return unicode(part.get_payload(decode=True), "utf-8", errors='ignore') 
        if ctype == 'text/html' and 'attachment' not in cdispo:
            return strip_tags(unicode(part.get_payload(decode=True), "utf-8", errors='ignore'))
            #return BeautifulSoup(part.get_payload(decode=True)).getText().replace("&nbsp;", "\n")
            return u''
        return None 


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

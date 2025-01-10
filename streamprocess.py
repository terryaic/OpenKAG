from settings import get_stop_words

class StreamProcess():
    def __init__(self):
        self.text = ""
        self.tokens = 0
        self.code = ""
        self.coding = False
        self.language = None
        self.linking = False
        self.caching = ''

    async def process_chat(self, response_part, callback):
        # the response streams one token at a time, print that as we receive it
        #print(response_part, end='', flush=True)
        self.tokens += 1
        rr = response_part.strip()
        if len(response_part) == 0:
            return False
        if response_part[0]=='`':
            self.caching += response_part
            if len(self.caching) < 3:
                return False
            else:
                self.caching += response_part
                response_part = self.caching
        if response_part.find('```')>=0:
            print("response_part------  :",response_part)
            self.coding = not self.coding
            if not self.coding:
                await callback('', text_type='text', to_end=True)
                await callback(self.code, text_type='code',to_end=True)
                self.code = ''
                self.language = None
            elif self.text != '':
                await callback(self.text)
        elif self.coding and self.language is None:
            self.language = response_part
        elif self.coding:
            self.code += response_part
        elif len(rr) > 0:
            if len(self.text) > 0:
                last_character = self.text[-1]
            #if wordprocess.is_word(rr):
            #    self.text += ' '
            if self.text.find("(http") >= 0 or self.text.find("<http")>=0:
                self.text += response_part
                self.linking = True
            if self.linking and (self.text.endswith(")") or self.text.endswith(">")):
                await callback(self.text, text_type='link')
                self.linking = False
                self.text = ""
            if self.linking:
                return False
            if rr[0] in get_stop_words():
                if self.text.endswith("vs"):
                    self.text = self.text + response_part
                elif len(self.text) > 0 and self.tokens >= 5 and last_character not in ['0','1','2','3','4','5','6','7','8','9']:
                    self.text += rr[0]
                    await callback(self.text)
                    if len(rr) > 1:
                        self.text = rr[1:]
                        token = len(rr) -1
                    else:
                        self.text = ""
                        self.tokens = 0
                else:
                    self.text = self.text + response_part
            elif rr[-1] in get_stop_words():
                if len(self.text) > 0 and self.tokens >= 5 and last_character not in ['0,','1','2','3','4','5','6','7','8','9']:
                    self.text += response_part
                    await callback(self.text)
                    self.text = ""
                    self.tokens = 0
                else:
                    self.text = self.text + response_part
            else:
                self.text = self.text + response_part
        else:
            self.text += response_part
        self.caching = ''
        return True

    async def end_chat(self, callback, stop_chat=False, text_type='text'):
        #if len(self.text) >0 and not stop_chat:
        await callback(self.text, text_type=text_type)
        self.text = ""
        self.tokens = 0
        self.code = ""
        self.coding = False
        self.language = None
        self.linking = False
        self.caching = ''

from settings import get_stop_words
import time

class StreamProcessLookAhead():
    def __init__(self):
        self.text = ""
        self.tokens = 0
        self.code = ""
        self.coding = False
        self.language = None
        self.linking = False
        self.caching = ''
        self.lookahead = None   # 用于缓存“下一个 token”，以实现 lookforward
        self.all_text = ""

    async def process_chat(self, response_part, callback):
        self.all_text += response_part
        """
        处理一个从流中接收到的 token（或分片）。
        在这里增加“向前看”逻辑，如果上一次循环中已经有 self.lookahead，
        则先处理它，并把此次的 response_part 暂存为新的 lookahead。
        """
        # 如果没有内容直接返回
        if len(response_part) == 0:
            return False

        # 每次进入，先判断是否已经有 lookahead
        # 如果有，代表要先把 lookahead 视为当前 token 来处理
        current_part = self.lookahead if self.lookahead is not None else response_part
        # 下一个 token（或分片）先暂存为新的 lookahead
        # 这样我们“真正处理 current_part 的逻辑”里，可以做前后联合判断
        self.lookahead = None if self.lookahead is not None else response_part

        # --------------------------------------------------------
        # 如果此时 lookahead 还为空，说明本次就只收到一个 token，没有下一个 token
        # 我们依然需要处理 current_part；而下一个 token 等下次调用 process_chat 时再判断
        # --------------------------------------------------------

        # 正式处理 current_part
        await self._handle_current_token(current_part, callback)

        # 处理完后，如果本次实际上收到了两个 token（一种情况是：上次有 lookahead + 这次又来了一个 token），
        # 那么此时需要把“本次传进来的 response_part”设置到 self.lookahead
        # 用于等待下次来的 token 做进一步判断。
        # 但是要排除上面那种“我们刚把 lookahead 置空的情况”。
        if self.lookahead is None and current_part != response_part:
            self.lookahead = response_part

        return True

    async def _handle_current_token(self, response_part, callback):
        """
        真正处理当前 token 的逻辑。
        """
        self.tokens += 1
        rr = response_part.strip()

        # 如果 token 开头是反引号，则处理一下 caching
        if response_part[0] == '`':
            self.caching += response_part
            # 这里仅做示例，如果反引号数不足 3，先不处理
            if len(self.caching) < 3:
                return
            else:
                self.caching += response_part
                response_part = self.caching

        # 检查代码块分隔符
        if response_part.find('```') >= 0:
            print("response_part------  :", response_part)
            self.coding = not self.coding
            if not self.coding:
                # 代码块结束，先回调 text，再回调 code
                await callback('', text_type='text', to_end=True)
                await callback(self.code, text_type='code', to_end=True)
                self.code = ''
                self.language = None
            else:
                # 代码块开始，如果前面累积了 text，先输出
                if self.text != '':
                    await callback(self.text)
        elif self.coding and self.language is None:
            # 如果正在记录代码块，还没记录语言，则把当前 token 当做语言
            self.language = response_part
        elif self.coding:
            # 如果正在记录代码块，直接累积到 self.code
            self.code += response_part
        else:
            # 处理普通文本
            if len(rr) > 0:
                if len(self.text) > 0:
                    last_character = self.text[-1]
                else:
                    last_character = ''

                # 如果 text 中有 (http 或 <http 等，说明在处理链接
                if "(http" in self.text or "<http" in self.text:
                    self.text += response_part
                    self.linking = True

                # 如果已经在处理链接，并且遇到 ) 或 > 结束，就输出
                if self.linking and (self.text.endswith(")") or self.text.endswith(">")):
                    await callback(self.text, text_type='link')
                    self.linking = False
                    self.text = ""
                    return

                if self.linking:
                    return

                # 看看当前 token 的第一个字符/最后一个字符是否在停止词里
                # （此处逻辑只是示例，具体按你的需求定制）
                start_in_stop = (rr[0] in get_stop_words())
                end_in_stop = (rr[-1] in get_stop_words())

                # 这里示例：如果第一个字符是停止词
                if start_in_stop:
                    if self.text.endswith("vs"):
                        # 原逻辑
                        self.text = self.text + response_part
                    elif len(self.text) > 0 and self.tokens >= 5 and last_character not in '0123456789':
                        self.text += rr[0]
                        await callback(self.text)
                        if len(rr) > 1:
                            # 把剩余部分留到下一次
                            self.text = rr[1:]
                            self.tokens = 1
                        else:
                            self.text = ""
                            self.tokens = 0
                    else:
                        self.text = self.text + response_part

                # 如果最后一个字符是停止词
                elif end_in_stop:
                    if len(self.text) > 0 and self.tokens >= 5 and last_character not in '0123456789':
                        self.text += response_part
                        await callback(self.text)
                        self.text = ""
                        self.tokens = 0
                    else:
                        self.text = self.text + response_part
                else:
                    # 普通情况直接累加
                    self.text = self.text + response_part
            else:
                self.text += response_part

        self.caching = ''

    async def end_chat(self, callback, stop_chat=False, text_type='text'):
        """
        最终结束时，把还没输出的 text/code 输出并重置。
        """
        # 如果还有累积的 text
        print(f"end chat:{stop_chat} {self.text}")
        if self.text and not stop_chat:
            await callback(self.text, text_type=text_type)

        # 重置所有状态
        self.text = ""
        self.tokens = 0
        self.code = ""
        self.coding = False
        self.language = None
        self.linking = False
        self.caching = ''
        self.lookahead = None
        all_text = self.all_text
        self.all_text = ""
        return all_text


class StreamProcess():
    def __init__(self):
        self._init()
        self._reset()

    def _init(self):
        self.text = ""
        self.tokens = 0
        self.code = ""
        self.coding = False
        self.language = None
        self.linking = False
        self.caching = ''
        self.all_text = ""
    
    def _reset(self):
        self.total_tokens = 0
        self.request_time = time.time()
        self.first_token_time = None
        self.last_token_time = None

    async def process_chat(self, response_part, callback):
        if self.first_token_time is None:
            self.first_token_time = time.time()
        self.last_token_time = time.time()
        self.total_tokens += 1
        self.all_text += response_part
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
            if rr[-1] in get_stop_words():
                if self.text.endswith("vs"):
                    self.text = self.text + response_part
                elif len(self.text) > 0 and self.tokens >= 5 and last_character not in ['0,','1','2','3','4','5','6','7','8','9']:
                    self.text += response_part
                    await callback(self.text)
                    self.text = ""
                    self.tokens = 0
                else:
                    self.text = self.text + response_part
            elif rr[0] in get_stop_words():
                if self.text.endswith("vs"):
                    self.text = self.text + response_part
                elif len(self.text) > 0 and self.tokens >= 5 and last_character not in ['0','1','2','3','4','5','6','7','8','9']:
                    self.text += rr[0]
                    await callback(self.text)
                    if len(rr) > 1:
                        self.text = rr[1:]
                        #token = len(rr) -1
                        self.tokens = 1
                    else:
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
        all_text = self.all_text
        self._init()
        return all_text

class StreamProcessSync():
    def __init__(self):
        self.text = ""
        self.tokens = 0
        self.code = ""
        self.coding = False
        self.language = None
        self.linking = False
        self.caching = ''

    def process_chat(self, response_part, callback):
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
                callback('', text_type='text', to_end=True)
                callback(self.code, text_type='code',to_end=True)
                self.code = ''
                self.language = None
            elif self.text != '':
                callback(self.text)
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
                callback(self.text, text_type='link')
                self.linking = False
                self.text = ""
            if self.linking:
                return False
            if rr[0] in get_stop_words():
                if self.text.endswith("vs"):
                    self.text = self.text + response_part
                elif len(self.text) > 0 and self.tokens >= 5 and last_character not in ['0','1','2','3','4','5','6','7','8','9']:
                    self.text += rr[0]
                    callback(self.text)
                    if len(rr) > 1:
                        self.text = rr[1:]
                        #token = len(rr) -1
                        self.tokens = 1
                    else:
                        self.text = ""
                        self.tokens = 0
                else:
                    self.text = self.text + response_part
            elif rr[-1] in get_stop_words():
                if len(self.text) > 0 and self.tokens >= 5 and last_character not in ['0,','1','2','3','4','5','6','7','8','9']:
                    self.text += response_part
                    callback(self.text)
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

    def end_chat(self, callback, stop_chat=False, text_type='text'):
        if len(self.text) >0 and not stop_chat:
            callback(self.text, text_type=text_type)
        self.text = ""
        self.tokens = 0
        self.code = ""
        self.coding = False
        self.language = None
        self.linking = False
        self.caching = ''

from lxml import etree
import pandas as pd
import datetime

class Parser:
    def __init__(self, filename):
        self.filename = filename
        tree = etree.parse(filename, etree.HTMLParser())
        self.parse_tree(tree)

    def parse_tree(self, tree):
        threads = tree.xpath(
            '//body/div[@class="contents"]/div[@class="thread"]')
        thread_dict = {tuple(sorted(i.text.split(','))): {
            'group': True, 'messages': []} for i in threads if i.text is not None}
        for key in thread_dict.keys():
            if len(key) == 1:
                thread_dict[key]['group'] = False
        for thread in threads:
            # ds stores list of {'name':$name, 'datetime':$datetime,
            # 'message':$content}
            if thread.text is None:
                continue
            ds = []
            for user, meta, content in zip(thread.xpath('div/div/span[@class="user"]'),
                                           thread.xpath(
                                               'div/div/span[@class="meta"]'),
                                           thread.xpath('p')):
                d = {}
                d['name'] = user.text
                d['datetime'] = datetime.datetime.strptime(
                    meta.text[:-4], "%A, %B %d, %Y at %I:%M%p")
                d['text'] = content.text
                ds.append(d)
            key = tuple(sorted(thread.text.split(',')))

            thread_dict[key]['messages'].extend(ds)
        for k in thread_dict.keys():
            thread_dict[key]['messages'].sort(key=lambda x: x['datetime'])
        self.thread_dict = thread_dict

    def message_count(self):
        return sorted([(', '.join(k), len(v['messages'])) for k, v in self.thread_dict.items()], key=lambda x: x[1], reverse=True)

    def individual_total_days(self, person):
        if isinstance(person, str):
            person = tuple(sorted(person.split(',')))
        return len(set(i['datetime'].date() for i in self.thread_dict[person]['messages']))

    def total_days(self):
        return sorted([(', '.join(k), self.individual_total_days(k)) for k in self.thread_dict.keys()], key=lambda x: x[1], reverse=True)

    def consec_days(self, person):
        if isinstance(person, str):
            person = tuple(sorted(person.split(',')))
        messages = self.thread_dict[person]['messages']
        days_messaged = sorted(list({m['datetime'].date() for m in messages}))
        max_consec = -1
        counter = 0
        one_day = datetime.timedelta(days=1)
        prev_day = days_messaged[0] - one_day
        streaks = []
        ended = True
        for day in days_messaged:
            if prev_day == day - one_day:
                counter += 1
                max_consec = max(max_consec, counter)
                ended = False
            else:
                streaks.append(counter)
                counter = 1
                ended = True
            prev_day = day
        if not ended:
            streaks.append(counter)
        return max(streaks), streaks

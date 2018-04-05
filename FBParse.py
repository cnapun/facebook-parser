import os
import re
import collections
import datetime

from lxml import etree
import numpy as np
import pandas as pd


def _date_range(min_day, max_day):  # max day is inclusive
    out = []
    while min_day <= max_day:
        out.append(min_day)
        min_day += datetime.timedelta(days=1)
    return out


class Parser:
    def __init__(self, base_path):
        self.base_path = base_path
        self.convos = None
        self._parse(base_path)

    def _parse(self, base_path):
        files = []
        for fname in os.listdir(base_path):
            if re.match(r"[0-9]+.html", fname):
                files.append(base_path + fname)
        all_convos = {}
        for fn in files:
            tree = etree.parse(fn, etree.HTMLParser())

            participants = (
                tuple(sorted(
                    tree.xpath('//body/div[@class="thread"]/h3')[0].tail.split(':')[-1].strip().split(', '))))

            users = [i.text for i in tree.xpath(
                '//body/div[@class="thread"]/div[@class="message"]/div[@class="message_header"]/span['
                '@class="user"]')]
            times = [i.text for i in tree.xpath(
                '//body/div[@class="thread"]/div[@class="message"]/div[@class="message_header"]/span['
                '@class="meta"]')]
            times = list(map(lambda x: datetime.datetime.strptime(x, "%A, %B %d, %Y at %I:%M%p %Z"), times))
            tmp = tree.xpath('//body/div[@class="thread"]/*')
            texts = []
            i = 1

            while tmp[i].tag != 'div':
                i += 1
            while i < len(tmp):
                while tmp[i].tag != 'p':
                    i += 1
                acc = []
                while i < len(tmp) and tmp[i].tag == 'p':
                    acc.append(tmp[i].text or '')
                    i += 1
                texts.append('\n'.join(filter(lambda x: x, acc)))

            new_df = pd.DataFrame({
                'name': users,
                'time': times,
                'text': texts,
            })
            if participants not in all_convos:
                all_convos[participants] = new_df
            else:
                all_convos[participants] = all_convos[participants].append(new_df).reset_index(drop=True)
        self.convos = all_convos

    def _convert_key(self, name_or_key):
        if isinstance(name_or_key, str):
            key = tuple(sorted(filter(lambda x: x, name_or_key.split(','))))
        elif hasattr(name_or_key, '__iter__') or isinstance(name_or_key, collections.Iterable):
            key = tuple(sorted(name_or_key))
        else:
            raise ValueError('Input a comma separated string or an iterable')
        if self.convos is not None and key not in self.convos:
            raise ValueError('%s is not a key in the dictionary' % str(key))
        return key

    def message_count(self):
        return sorted([(', '.join(k), len(v)) for k, v in self.convos.items()], key=lambda x: x[1],
                      reverse=True)

    def individual_total_days(self, name_or_key):
        key = self._convert_key(name_or_key)
        return len(np.unique(self.convos[key]['time'].dt.date))

    def total_days(self):
        return sorted([(', '.join(k), self.individual_total_days(k)) for k in self.thread_dict.keys()],
                      key=lambda x: x[1], reverse=True)

    def consec_days(self, name_or_key, return_inv=False):
        """
        Get the number of consecutive days messages were sent in a specific conversation.
        Returns the lengths of all "streaks." If return_inv == True, then the inverse can index
        into the streaks returned to provide the length of the streak that each message belongs to

        :type df_dict: Dict[str, pd.DataFrame]
        :type return_inv: bool
        :type name_or_key: Union[str, Tuple[str], Iterable[str]]
        :param df_dict: dictionary output in the form returned by parse_data
        :param name_or_key: name to look up: either a single name, or, for a group, a tuple of names or a comma
        separated
        list of names
        :param return_inv: whether or not the indices needed to determine length of streak a particular message
        belonged to
        :return: np.array of lengths of streaks
        """
        key = self._convert_key(name_or_key)
        t = self.convos[key][::-1].sort_values('time', kind='mergesort').reset_index(drop=True)
        uqs, uinv = np.unique((t.time.dt.date - t.time.dt.date[0]) / np.timedelta64(1, 'D'), return_inverse=True)
        wheres, inv, streaks = np.unique(uqs - np.arange(uqs.size), return_counts=True, return_inverse=True)
        if return_inv:
            return streaks, inv[uinv]
        else:
            return streaks

    def day_counts(self, name_or_key):
        key = self._convert_key(name_or_key)
        dates = self.convos[key]['time'].dt.date
        by_day_dict = {d: 0 for d in _date_range(dates[0], dates[-1])}
        for date in dates:
            by_day_dict[date] += 1
        return sorted(by_day_dict.items())

    def minute_hist(self, name_or_key):
        key = self._convert_key(name_or_key)
        dts = self.convos[key]['time'].dt
        times = dts.hour * 60 + dts.minute
        return np.histogram(times, np.arange(1440))

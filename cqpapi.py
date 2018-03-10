# -*-coding:utf8-*-
"""CQP (Corpus Query Processor) API."""
from __future__ import division
from ConfigParser import ConfigParser
from os.path import abspath, dirname, join
import re
import json
import itertools

from CWB.CL import Corpus
import PyCQP_interface


# This setting is extremely important! The default value is 40, which
# means the maximum time a user can request is 40 second, but this will
# not suffice the condition that a user query some high frequency word
# like '今天' (because usually it takes more than a minute to finish
# querying).
PyCQP_interface.cMaxRequestProcTime = 240

with open('db.json') as f:
    DB = json.load(f)

CONF = ConfigParser()
CONF.read(join(dirname(abspath(__file__)), 'cwb.ini'))


class Cqp(object):
    """CQP handler."""

    def __init__(self, corpus_name, window_size=8, auth=False):
        """__init__ method."""
        self.window_size = window_size
        self.corpus_name = corpus_name
        if self.corpus_name == 'copener':
            if not auth:
                raise Exception('Not auth!')

    def find(self, token, show_pos=False, rsize=None):
        """Get concordance of a word."""
        if isinstance(token, unicode):
            token = token.encode('utf-8')
        else:
            try:
                token.decode('utf-8')
            except BaseException:
                raise UnicodeError('Encoding error!')
        self.conclst = []
        registry_dir = CONF.get('main', 'registry_dir')
        cqp = PyCQP_interface.CQP(
            bin=CONF.get('main', 'cqp_bin'), options='-c -r ' + registry_dir)
        cqp.Exec(self.corpus_name.upper() + ";")

        if token.startswith('cql:'):
            token = token[4:]
            cqp.Query(token)
        elif token.startswith('ncql:'):
            token = token[5:]
            token = convert_cql(token)
            cqp.Query(token)
        else:
            cqp.Query('[word="%s"];' % token)

        _rsize = int(cqp.Exec("size Last;"))
        if rsize is None:
            rsize = _rsize
        else:
            if rsize > _rsize:
                rsize = _rsize

        self.results = cqp.Dump(first=0, last=rsize)

        cqp.Terminate()
        if self.results == [['']]:
            return 'nores'

        corpus = Corpus(self.corpus_name, registry_dir=registry_dir)
        words = corpus.attribute("word", "p")

        with open(registry_dir + '/' + self.corpus_name) as f:
            cqpreg = f.read()
            s_attrs = re.findall('STRUCTURE\s(\w+)', cqpreg)

        s_attrs_dic = {}
        for attr in s_attrs:
            if attr != 's':
                s_attrs_dic[attr] = corpus.attribute(attr, "s")
            if show_pos == 1:
                postags = corpus.attribute("pos", "p")
            elif show_pos == 0:
                pass

        for line in self.results:
            output = dict()
            start = int(line[0])
            end = int(line[1]) + 1

            lw = words[start - self.window_size:start]
            if rsize < self.window_size:
                rw = words[end:end + rsize]
            else:
                rw = words[end:end + self.window_size]
            qw = words[start:end]

            if show_pos == 1:
                lp = postags[start - self.window_size:start]
                rp = postags[end:end + self.window_size]
                qp = postags[start:end]

                left = ' '.join(['%s<span>/%s</span>' % (word, pos)
                                 for word, pos in zip(lw, lp)])
                mid = ' '.join(['%s<span>/%s</span>' % (word, pos)
                                for word, pos in zip(qw, qp)])
                right = ' '.join(['%s<span>/%s</span>' % (word, pos)
                                  for word, pos in zip(rw, rp)])

            elif show_pos == 0:
                left = ' '.join(['%s' % word for word in lw])
                mid = ' '.join(['%s' % word for word in qw])
                right = ' '.join(['%s' % word for word in rw])

            metainfo = dict()
            for k in s_attrs_dic.iterkeys():
                metainfo[k] = s_attrs_dic[k].find_pos(start)[-1]
            output['conc'] = (left, mid, right)
            output['corp_name'] = DB[self.corpus_name]
            output['metainfo'] = metainfo
            output['qpos'] = '%s_%s_%s' % (self.corpus_name, start, end)
            self.conclst.append(output)


def convert_cql(string):
    """Convert CQL (Corpus Query Language)."""
    if not isinstance(string, unicode):
        try:
            string = string.decode('utf8')
        except BaseException:
            raise UnicodeError('string must be unicode or utf8')
    if 'x' in string:  # \x should be considered
        res = re.split('((?:x){1,})', string)
        res = [[i] if 'x' in i else list(i) for i in res]
        res = itertools.chain.from_iterable(res)
        res = list(res)
        res = possible_combo(lst=res, spec_char='x')
        output = ''
        for i in res:
            for j in i:
                if j != '':
                    if 'x' in j:
                        output += j
                    else:
                        output += re.sub('(.*)', '[word="\\1"]', j)
            output += '|'
        output = output.strip('|') + ';'
        output = re.sub('x', '[]', output)
    else:
        output = string
    output = output.encode('utf8')

    return output


def possible_combo(lst, spec_char):
    """Possible combinations."""
    combinatorics = itertools.product([True, False], repeat=len(lst) - 1)
    solution = []
    for combination in combinatorics:
        i = 0
        one_such_combination = [lst[i]]
        for slab in combination:
            i += 1
            if not slab:  # there is a join
                one_such_combination[-1] += lst[i]
            else:
                one_such_combination += [lst[i]]
        for c in one_such_combination:
            if spec_char in c:
                if len(set(c)) != 1:
                    break
                solution.append(one_such_combination)
    return solution


def con_source(qpos):
    """Concordance source."""
    window_size = 100
    corp_name, start, end = qpos.split('_')
    start, end = int(start), int(end)
    registry_dir = CONF.get('main', 'registry_dir')
    corpus = Corpus(
        corp_name.upper(), registry_dir=registry_dir)
    words = corpus.attribute('word', 'p')
    corp_len = len(words)
    if start - window_size < 0:
        lb = 0
    else:
        lb = start - window_size
    if end + window_size > corp_len:
        rb = corp_len - 1
    else:
        rb = end + window_size

    lw = ''.join(words[lb:start])
    qw = '<span style="color:red;font-size:24px;">' + ''.join(
        words[start:end]) + '</span>'
    rw = ''.join(words[end:rb])
    if corp_name == 'tccm' or corp_name == 'ntuspk':
        if corp_name == 'tccm':
            s_attrs = corpus.attribute('s_addresser', 's')
        if corp_name == 'ntuspk':
            s_attrs = corpus.attribute('s_speaker', 's')
        top = s_attrs.cpos2struc(lb)
        top = s_attrs[top]
        bottom = s_attrs.cpos2struc(rb)
        bottom = s_attrs[bottom]

        attr_con = []
        for attr in s_attrs:
            if attr[0] >= top[0] and attr[1] <= bottom[1]:
                attr_con.append(attr)
        output = ''
        for a in attr_con:
            if start in xrange(a[0], a[1]):
                sent =\
                    a[-1] + ': ' +\
                    ' '.join(words[a[0]:start]) + ' ' +\
                    '<span style="color:red;font-size:24px;">' +\
                    ' '.join(words[start:end]) + '</span>' + ' ' +\
                    ' '.join(words[end:a[1]])
            else:
                sent = '%s: %s' % (a[-1], ' '.join(words[a[0]:a[1]]))
            output += sent + '<br>'

        return output

    return lw + qw + rw

import sys
import re

from types import StringTypes

from common import FormatError

TEXTBOUND_LINE_RE = re.compile(r'^T\d+\t')

KEEP_LONGER = 'keep-longer'
KEEP_SHORTER = 'keep-shorter'
OVERLAP_RULES = [KEEP_LONGER, KEEP_SHORTER]

class Textbound(object):
    """Textbound annotation in BioNLP ST/brat format.

    Note: discontinous spans not supported (TODO).
    """

    def __init__(self, id_, type_, start, end, text):
        self.id = id_
        self.type = type_
        self.start = start
        self.end = end
        self.text = text

    def __unicode__(self):
        return u'%s\t%s %s %s\t%s' % (self.id, self.type, self.start, self.end,
                                      self.text)

    def __str__(self):
        return '%s\t%s %s %s\t%s' % (self.id, self.type, self.start, self.end,
                                     self.text)

    def is_valid(self, text):
        assert 0 <= self.start <= len(text), 'start not in range'
        assert 0 <= self.end <= len(text), 'end not in range'
        assert self.start <= self.end, 'start > end'
        assert text[self.start:self.end] == self.text, \
            u'text mismatch (check encoding?): %d-%d\n    "%s"\nvs. "%s"' % \
            (self.start, self.end, text[self.start:self.end], self.text)
        return True

    @classmethod
    def _parse_offsets(cls, offsets):
        # Basic format is a space-separated pair of ints (start, end)
        # (e.g. '10 15'). Also support discontinuous spans as a
        # semicolon-separated sequence of space-separated (start, end)
        # int pairs (e.g. '10 15;20 25').
        parsed = []
        for start_end in offsets.split(';'):
            start, end = start_end.split(' ')
            parsed.append((int(start), int(end)))
        return parsed

    @classmethod
    def _resolve_discontinuous(cls, offsets, text):
        # Support for discontinuous annotations is incomplete. Reduce
        # to continous simply by taking the last (start, end) pair
        if len(offsets) == 1:
            return offsets, text
        last_off = offsets[-1]
        last_text = text[last_off[0]-last_off[1]:]
        print >> sys.stderr, 'Resolve discontinuous "%s" to last subspan "%s"' \
            % (text, last_text)
        return [last_off], last_text

    @classmethod
    def from_str(cls, string):
        try:
            id_, type_offsets, text = string.split('\t')
            type_, offsets = type_offsets.split(' ', 1)
            offsets = cls._parse_offsets(offsets)
            if len(offsets) != 1:
                offsets, text = cls._resolve_discontinuous(offsets, text)
            start, end = offsets[0]
            return cls(id_, type_, start, end, text)
        except ValueError, e:
            raise FormatError('Standoff: failed to parse %s' % string)

def parse_textbounds(input_):
    """Parse textbound annotations in input, returning a list of
    Textbound.

    Lines not containing valid textbound annotations will be silently
    ignored.
    """

    textbounds = []

    if isinstance(input_, StringTypes):
        input_ = input_.split('\n')

    for l in input_:
        l = l.rstrip('\n')

        if not TEXTBOUND_LINE_RE.search(l):
            continue

        textbounds.append(Textbound.from_str(l))

    return textbounds

def select_eliminated_and_kept(t1, t2, overlap_rule=None):
    if overlap_rule is None:
        overlap_rule = OVERLAP_RULES[0]    # default
    if overlap_rule == KEEP_LONGER:
        if t1.end-t1.start < t2.end-t2.start:
            return t1, t2
        else:
            return t2, t1
    elif overlap_rule == KEEP_SHORTER:
        if t1.end-t1.start > t2.end-t2.start:
            return t1, t2
        else:
            return t2, t1
    else:
        raise ValueError(overlap_rule)

def eliminate_overlaps(textbounds, overlap_rule=None):
    # TODO: avoid O(n^2) overlap check
    eliminate = {}
    for t1 in textbounds:
        for t2 in textbounds:
            if t1 is t2:
                continue
            if t2.start >= t1.end or t2.end <= t1.start:
                continue
            if eliminate.get(t1) or eliminate.get(t2):
                continue
            elim, keep = select_eliminated_and_kept(t1, t2, overlap_rule)
            try:
                print >> sys.stderr, "Eliminate %s due to overlap with %s"\
                    % (elim, keep)
            except UnicodeEncodeError:
                print >> sys.stderr, "Eliminate %s due to overlap with %s"\
                    % (elim.id, keep.id)
            eliminate[elim] = True
    return [t for t in textbounds if not t in eliminate]

def filter_textbounds(textbounds, types, exclude=False):
    """Filter textbounds to given types."""
    if not exclude:
        return [t for t in textbounds if t.type in types]
    else:
        return [t for t in textbounds if t.type not in types]

def verify_textbounds(textbounds, text):
    """Verify that given textbounds are valid with reference to given text.

    Return True on success, raise FormatError on any issue.
    """

    for t in textbounds:
        try:
            assert t.is_valid(text)
        except Exception, e:
            s = u'Error verifying textbound %s: %s' % (t, e)
            raise FormatError(s.encode('utf-8'))
    return True

def _retag_sentence(sentence, offset_type):
    prev_label = None
    for token in sentence.tokens:
        # TODO: warn for multiple, detailed info for non-initial
        tb = None
        for o in range(token.start, token.end):
            if o in offset_type:
                if o != token.start:
                    # TODO: log if verbose
                    # print >> sys.stderr, 'Warning: annotation-token boundary mismatch: "%s" --- "%s"' % (token.text, offset_type[o].text)
                    pass
                tb = offset_type[o]
                break

        label = None if tb is None else tb.type
        if tb is None:
            tag = 'O'
        elif label == prev_label and tb.start < token.start:
            tag = 'I-'+label
        else:
            tag = 'B-'+label
        prev_label = label

        token.tag = tag

def retag_document(document, textbounds):
    """Revise token tags in Sentence to match given textbound annotations."""

    # create a map from offset to annotated type, then iterate over tokens
    # to detect overlaps with textbound annotations to assign tags.
    # TODO: this could be done more neatly/efficiently
    offset_type = {}

    for tb in textbounds:
        for i in range(tb.start, tb.end):
            if i in offset_type:
                print >> sys.stderr, "Warning: overlapping textbounds"
            offset_type[i] = tb

    for sentence in document.sentences:
        _retag_sentence(sentence, offset_type)

#!/usr/bin/env python import collections

import collections
import re

class _Node(object):
    """
    A node represents a set of numeric tuples (vectors).

    A tree-structure is used where each node has one child for each possible
    first (head) value in the set. Each child is itself a node representing the
    set of tails with the given head. The empty tuple is present if the
    `present` attribute is set.

    """
    def __init__(self):
        self.present = False
        self.children = collections.defaultdict(_Node)

    def _add_vec(self, vec):
        if len(vec) > 0:
            self.children[vec[0]]._add_vec(vec[1:])
        else:
            self.present = True

    def query_lte(self, query_vec):
        """
        Return vectors that are less than or equal to the query vector.
        
        Returned vectors will be the same length as the query vector, but each
        element will be less than or equal to the corresponding element in the
        query vector.

        """
        if query_vec == ():
            if self.present:
                yield ()
        else:
            for val, child in self.children.items():
                if val <= query_vec[0]:
                    for child_vec in child.query_lte(query_vec[1:]):
                        yield (val,) + child_vec

def _make_vec(word):
    """Make a letter frequency vector for given word."""
    letters = [chr(ord('A') + i) for i in range(26)]
    counter = collections.Counter(word)
    return tuple(counter[l] for l in letters)

_STRIP_RE = re.compile(r"[^A-Z]")
def _canonicalize_word(word):
    return _STRIP_RE.sub('', word.upper()) 

def _load_words(word_list):
    with open(word_list) as f:
        words = {_canonicalize_word(line) for line in f.readlines()}
    words = {w for w in words if len(w) < 5}
    return words

def _make_tree(word_list="/usr/share/dict/words"):
    vec_dict = collections.defaultdict(list)
    for word in _load_words(word_list):
        vec_dict[_make_vec(word)].append(word)
    tree = _Node()
    for vec in vec_dict.keys():
        tree._add_vec(vec)
    return tree, vec_dict

def _find_anagrams_vecs(tree, query_vec)
    pass

def find_anagrams(query_word):
    query_vec = _make_vec(query_word)
    tree, vec_dict = _make_tree()

if __name__ == "__main__":
    import sys

    _find_anagrams(sys.argv[1])

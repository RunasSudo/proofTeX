#!/usr/bin/env python3
#    proofTeX - Tools for proofing LaTeX documents - detex.py
#    Copyright © 2016  RunasSudo (Yingtong Li)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import copy
import ply.lex
import re

tokens = (
	'BEGIN_DOCUMENT', 'END_DOCUMENT',
	'DOLLAR', 'ESCDOLLAR',
	'DDOLLAR',
	'BEGIN_ALIGN', 'END_ALIGN', 'INTERTEXT',
	'BEGIN_IGNORED_ENV', 'END_IGNORED_ENV',
	'BEGIN_ENVIRONMENT', 'END_ENVIRONMENT',
	'BEGIN_GROUP', 'END_GROUP', 'ESCBRACE',
	'PERCENT', 'ESCPERCENT',
	'CHAR', 'NEWLINE',
	'SPECIAL_MACRO', 'MACRO',
)

states = (
	('document', 'exclusive'),
	('inline', 'exclusive'),
	('display', 'exclusive'),
	('align', 'exclusive'),
	('ignoredenv', 'exclusive'),
	('group', 'exclusive'),
	('intertext', 'exclusive'),
	('specialmacro', 'exclusive'),
	('comment', 'exclusive'),
)

def _super(text, t, superof=None):
	tmplexer = clone_lexer(baselexer)
	for s in t.lexer.lexstatestack:
		if superof is not None and s == superof:
			break
		if s != t.lexer.lexstate:
			tmplexer.push_state(s)
	tmplexer.input(text)
	return ''.join([tok.value for tok in tmplexer])

def _value(t, text, grouptext=None):
	if t.lexer.lexstate == 'group':
		t.lexer.stack[-1] += (grouptext if grouptext is not None else text)
		return None
	else:
		t.value = text
		return t

def t_ANY_ESCPERCENT(t):
	r'\\%'
	t.value = _super('%', t)
	return t
def t_ANY_ESCBRACE(t):
	r'\\[{}]'
	t.value = t.value[1:]
	return t
def t_ANY_ESCDOLLAR(t):
	r'\\\$'
	t.value = '$'
	return t

def t_ANY_PERCENT(t):
	r'%'
	t.lexer.push_state('comment')
def t_comment_CHAR(t):
	r'.'
	pass
def t_comment_NEWLINE(t):
	r'\n'
	t.lexer.pop_state()

def t_document_DDOLLAR(t):
	r'\$\$'
	t.lexer.stack.append('')
	t.lexer.push_state('display')
def t_document_DOLLAR(t):
	r'\$'
	t.lexer.stack.append('')
	t.lexer.push_state('inline')
def t_display_DDOLLAR(t):
	r'\$\$'
	text = t.lexer.stack.pop()
	t.lexer.pop_state()
	if not re.search(r'[^a-zA-Z0-9_^{}αβγδεζηθικλμνξπρστυφχψω ]', text):
		if args.count:
			t.value = 'MATHS'
		else:
			t.value = text
		return t
	else:
		return None
def t_inline_DOLLAR(t):
	r'\$'
	return t_display_DDOLLAR(t)
def t_inline_CHAR(t):
	r'.'
	t.lexer.stack[-1] += t.value
def t_inline_NEWLINE(t):
	r'\n'
	pass
t_display_CHAR = t_inline_CHAR
t_display_NEWLINE = t_inline_NEWLINE

def t_INITIAL_BEGIN_DOCUMENT(t):
	r'\\begin\s*{\s*document\s*}'
	t.lexer.push_state('document')

def t_document_END_DOCUMENT(t):
	r'\\end\s*{\s*document\s*}'
	t.lexer.pop_state()
def t_document_BEGIN_ALIGN(t):
	r'\\begin\s*{\s*align\*?\s*}'
	t.lexer.push_state('align')

def t_align_END_ALIGN(t):
	r'\\end\s*{\s*align\*?\s*}'
	t.lexer.pop_state()
def t_align_INTERTEXT(t):
	r'\\intertext\s*{'
	t.lexer.stack.append('')
	t.lexer.push_state('intertext')
def t_intertext_END_GROUP(t):
	r'}'
	t.value = _super(t.lexer.stack.pop(), t, 'align')
	t.lexer.pop_state()
	return t
t_intertext_DOLLAR = t_document_DOLLAR
def t_intertext_CHAR(t):
	r'.'
	t.lexer.stack[-1] += t.value
def t_intertext_NEWLINE(t):
	r'.'
	pass

def t_ANY_BEGIN_IGNORED_ENV(t):
	r'\\begin\s*{(figure|table|nocount)\*?}'
	t.lexer.push_state('ignoredenv')
def t_ignoredenv_END_IGNORED_ENV(t):
	r'\\end\s*{(figure|table|nocount)\*?}'
	t.lexer.pop_state()
def t_ignoredenv_CHAR(t):
	r'.'
	pass
def t_ignoredenv_NEWLINE(t):
	r'\n'
	pass

def t_document_BEGIN_ENVIRONMENT(t):
	r'\\begin\s*({.+?})+'
	pass
def t_document_END_ENVIRONMENT(t):
	r'\\end\s*{.+?}'
	pass

def t_ANY_SPECIAL_MACRO(t):
	r'\\(autoref|ref|autocite|textcite|label|footnote)\s*{'
	t.lexer.stack.append(re.match(t_ANY_SPECIAL_MACRO.__doc__, t.value).group(1))
	t.lexer.stack.append('')
	t.lexer.push_state('specialmacro')
def t_specialmacro_END_GROUP(t):
	r'}'
	grouptext = _super(t.lexer.stack.pop(), t)
	macro = t.lexer.stack.pop()
	t.lexer.pop_state()
	
	if args.tts:
		if macro == 'label':
			return None
		else:
			t.value = grouptext
			return t
	else:
		# guess word counts
		if macro == 'autoref':
			return _value(t, 'REFTYPE NUMBER')
		if macro == 'ref':
			return _value(t, 'NUMBER')
		if macro == 'autocite' or macro == 'label' or macro == 'footnote':
			return None
		if macro == 'textcite':
			return _value(t, 'AUTHOR')
def t_specialmacro_CHAR(t):
	r'.'
	t.lexer.stack[-1] += t.value
def t_specialmacro_NEWLINE(t):
	r'\n'
	t.lexer.stack[-1] += t.value

def t_inline_BEGIN_GROUP(t):
	r'{'
	pass
def t_inline_END_GROUP(t):
	r'}'
	pass
t_display_BEGIN_GROUP = t_inline_BEGIN_GROUP
t_display_END_GROUP = t_inline_END_GROUP
def t_ANY_BEGIN_GROUP(t):
	r'{'
	t.lexer.stack.append('')
	t.lexer.push_state('group')
def t_group_END_GROUP(t):
	r'}'
	grouptext = _super(t.lexer.stack.pop(), t)
	t.lexer.pop_state()
	return _value(t, grouptext, '{' + grouptext + '}')
def t_group_CHAR(t):
	r'.'
	t.lexer.stack[-1] += t.value
def t_group_NEWLINE(t):
	r'\n'
	t.lexer.stack[-1] += t.value

def t_ANY_MACRO(t):
	r'\\[a-zA-Z]+\*?(\[.*?\])?'
	pass # Ignore any other macros

def t_INITIAL_CHAR(t):
	r'.'
	pass
def t_INITIAL_NEWLINE(t):
	r'\n'
	pass
def t_document_CHAR(t):
	r'.'
	return t
def t_document_NEWLINE(t):
	r'\n'
	return t
t_align_CHAR = t_INITIAL_CHAR
t_align_NEWLINE = t_INITIAL_NEWLINE

def t_ANY_error(t):
	raise Exception('Illegal character \'%s\''.format(t.value[0]))

# -----

def clone_lexer(lex):
	IGNORED = ['lexre', 'lexstatere']
	
	ignored = {}
	for ignore in IGNORED:
		ignored[ignore] = getattr(lex, ignore)
		setattr(lex, ignore, None)
	newlex = copy.deepcopy(lex)
	for ignore in IGNORED:
		setattr(lex, ignore, ignored[ignore])
		setattr(newlex, ignore, ignored[ignore])
	return newlex

parser = argparse.ArgumentParser(description='Strip LaTeX from a file and optionally count words or format for text-to-speech')
parser.add_argument('infile', help='The input LaTeX file')
parser.add_argument('--document', action='store_true', help='Treat entire input as content of document environment')
parser.add_argument('--count', action='store_true', help='Count words')
parser.add_argument('--tts', action='store_true', help='Format for text-to-speech')
args = parser.parse_args()

baselexer = ply.lex.lex()
baselexer.stack = ['']

lexer = clone_lexer(baselexer)

with open(args.infile, 'r', encoding='utf8') as f:
	data = f.read()

data = re.sub(r'\\iffalse.*?\\fi', r'', data)

if args.document:
	lexer.push_state('document')

lexer.input(data)

string = ''.join([tok.value for tok in lexer])
string = re.sub(r'\s+([,.!?])', r'\1', string)
string = re.sub(r'(\s)\s+', r'\1', string)
string = string.strip()

if args.count:
	print(len(re.findall(r' ', string)) + 1)
else:
	print(string)

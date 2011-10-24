# From http://code.google.com/p/markdown-downheader/source/browse/mdx_downheader/__init__.py

#Copyright (c) <2010>, <KnX.corp@gmail.com>
#All rights reserved.

#Redistribution and use in source and binary forms, with or without modification,
#are permitted provided that the following conditions are met:

#Redistributions of source code must retain the above copyright notice, this list
#of conditions and the following disclaimer.
#Redistributions in binary form must reproduce the above copyright notice, this
#list of conditions and the following disclaimer in the documentation and/or
#other materials provided with the distribution.
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
#ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# -*- coding: utf-8 -*-
import markdown
import re

def makeExtension(configs=None) :
    return DownHeaderExtension(configs=configs)
    
class DownHeaderExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        if 'downheader' in md.treeprocessors.keys():
            md.treeprocessors['downheader'].offset += 1
        else:
            md.treeprocessors.add('downheader', DownHeaderProcessor(), '_end')

class DownHeaderProcessor(markdown.treeprocessors.Treeprocessor):
    def __init__(self, offset=1):
        markdown.treeprocessors.Treeprocessor.__init__(self)
        self.offset = offset
    def run(self, node):
        expr = re.compile('h(\d)')
        for child in node.getiterator():
            match = expr.match(child.tag)
            if match:
                child.tag = 'h' + str(min(6, int(match.group(1))+self.offset))
        return node
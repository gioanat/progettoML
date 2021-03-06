# -*- coding: utf-8 -*-
"""generate_utils.py

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Pdv7L8MFE6b0AWypV_jL8x85ZupO5_df
"""

import numpy as np
import torch
from pytorch_pretrained_bert import BertTokenizer, BertModel, BertForMaskedLM
from transformers import AutoModelForMaskedLM, AutoTokenizer, AutoModelForSeq2SeqLM
  

# coding=utf-8
# Copyright 2018 The Google AI Language Team Authors, The HuggingFace Inc. team,
# and Marco Polignano.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tokenization classes for Italian AlBERTo models."""
import collections
import logging
import os
import re
# Generation modes as functions
import math
import time
from typing import List
import torch


try:
    from ekphrasis.classes.preprocessor import TextPreProcessor
    from ekphrasis.classes.tokenizer import SocialTokenizer
    from ekphrasis.dicts.emoticons import emoticons
except ImportError:
    print(
        "You need to install ekphrasis to use AlBERToTokenizer"
        "pip install ekphrasis"
    )
    from pip._internal import main as pip
    pip(['install', '--user', 'ekphrasis'])
    from ekphrasis.classes.preprocessor import TextPreProcessor
    from ekphrasis.classes.tokenizer import SocialTokenizer
    from ekphrasis.dicts.emoticons import emoticons
   
text_processor = TextPreProcessor(
    # terms that will be normalized
    normalize=['url', 'email', 'user', 'percent', 'money', 'phone', 'time', 'date', 'number'],
    # terms that will be annotated
    annotate={"hashtag"},
    fix_html=True,  # fix HTML tokens

    unpack_hashtags=True,  # perform word segmentation on hashtags

    # select a tokenizer. You can use SocialTokenizer, or pass your own
    # the tokenizer, should take as input a string and return a list of tokens
    tokenizer=SocialTokenizer(lowercase=True).tokenize,
    dicts=[emoticons]
)

class AlBERTo_Preprocessing(object):
    def __init__(self, do_lower_case=True, **kwargs):
        self.do_lower_case = do_lower_case

    def preprocess(self, text):
        if self.do_lower_case:
            text = text.lower()
        text=text.replace(" > "," ")
        text=text.replace(" < "," ")
        text=text.replace(" / "," ")
        text=text.replace(" < user "," <user> ")
        text=text.replace(" < url "," <url> ")
        text = str(" ".join(text_processor.pre_process_doc(text)))
        text = re.sub(r'[^a-zA-Z??-??</>!???????\s\U00010000-\U0010ffff]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'(\w)\1{2,}', r'\1\1', text)
        text = re.sub(r'^\s', '', text)
        text = re.sub(r'\s$', '', text)
        return text
    
class GenerateHints(object):
    def __init__(self):
        self.noWiki = True
        self.model_version =  "m-polignano-uniba/bert_uncased_L-12_H-768_A-12_italian_alb3rt0"
        self.model = AutoModelForMaskedLM.from_pretrained(self.model_version)
        self.model.eval()
        self.cuda = torch.cuda.is_available()
        if self.cuda:
            self.model = self.model.cuda(0)
        # Load pre-trained model tokenizer (vocabulary)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_version)
        self.CLS = '[CLS]'
        self.SEP = '[SEP]'
        self.MASK = '[MASK]'
        self.mask_id = self.tokenizer.convert_tokens_to_ids([self.MASK])[0]
        self.sep_id = self.tokenizer.convert_tokens_to_ids([self.SEP])[0]
        self.cls_id = self.tokenizer.convert_tokens_to_ids([self.CLS])[0]

        self.list_token_obtain = self.list_token()
        self.list_subtoken_obtain = self.list_subtoken()

        self.src = 'it'  # source language
        self.trg = 'en'  # target language
        self.modelTrasl = f'Helsinki-NLP/opus-mt-{self.src}-{self.trg}'

        self.tokenizerTrasl = AutoTokenizer.from_pretrained(self.modelTrasl)
        self.modelTrasl = AutoModelForSeq2SeqLM.from_pretrained(self.modelTrasl)
    def tokenize_batch(self,batch):
        return [self.tokenizer.convert_tokens_to_ids(sent) for sent in batch]

    def untokenize_batch(self,batch):
        return [self.tokenizer.convert_ids_to_tokens(sent) for sent in batch]
    
    def list_token(self):
        ll = list()
        with open('vocab.txt','r') as f:
          for s in f.readlines():
              t=s.replace("\n","")
              if t.startswith("##"):
                if t[2] in ["a","e","i","o","u"]:
                      ll.append(self.tokenizer.convert_tokens_to_ids(t))
        return ll

    def list_subtoken(self):
        ll = list()
        with open('vocab.txt','r') as f:
          for s in f.readlines():
              t=s.replace("\n","")
              if t.startswith("##"):
                  ll.append(self.tokenizer.convert_tokens_to_ids(t))
        return ll
    def generate_step(self,out, gen_idx, batch, temperature=None, top_k=0, sample=False, return_list=True, lastVocal = False, isFirst=False):
        """ Generate a word from from out[gen_idx]

        args:
            - out (torch.Tensor): tensor of logits of size batch_size x seq_len x vocab_size
            - gen_idx (int): location for which to generate for
            - top_k (int): if >0, only sample from the top k most probable words
            - sample (Bool): if True, sample from full distribution. Overridden by top_k 
        """
        if self.noWiki:
          logits = out.logits[:,gen_idx]
        else:
          logits = out[:,gen_idx]
        if temperature is not None:
            logits = logits / temperature
        if top_k > 0:
            kth_vals, kth_idx = logits.topk(top_k, dim=-1)
            rmToken = batch[0][(gen_idx-4):gen_idx]
            rmToken.append(self.tokenizer.convert_tokens_to_ids('[UNK]'))
            if lastVocal and not isFirst:
              [rmToken.append(item) for item in self.list_token_obtain]
            if isFirst:
              [rmToken.append(item) for item in self.list_subtoken_obtain]
            if kth_idx == []:
              top_k = len(self.idx_list)+10
              kth_vals, kth_idx = logits.topk(top_k, dim=-1)
              kth_idx , kth_vals=diff(kth_idx.tolist()[0],kth_vals.tolist()[0], self.idx_list)
            kth_idx , kth_vals=diff(kth_idx.tolist()[0],kth_vals.tolist()[0],rmToken)
            kth_vals = torch.tensor([kth_vals]).cuda() if self.cuda else torch.tensor([kth_vals])
            kth_idx = torch.tensor([kth_idx]).cuda() if self.cuda else torch.tensor([kth_idx])
            dist = torch.distributions.categorical.Categorical(logits=kth_vals)
            idx = kth_idx.gather(dim=1, index=dist.sample().unsqueeze(-1)).squeeze(-1) 
        elif sample:
            dist = torch.distributions.categorical.Categorical(logits=logits)
            idx = dist.sample().squeeze(-1)
        else:
            idx = torch.argmax(logits, dim=-1)
        return idx.tolist() if return_list else idx


    def get_init_text(self, seed_text, max_len, batch_size = 1, rand_init=False):
        """ Get initial sentence by padding seed_text with either masks or random words to max_len """
        batch = [seed_text + [self.MASK] * max_len + [self.SEP] for _ in range(batch_size)]  # crea batch_size sentences of max_len that start with [CLS] and end with [SEP]
        #if rand_init:
        #    for ii in range(max_len):
        #        init_idx[seed_len+ii] = np.random.randint(0, len(tokenizer.vocab))

        return self.tokenize_batch(batch)
            
    def sequential_generation(self,seed_text, batch_size=10, max_len=15, leed_out_len=15, 
                              top_k=0, temperature=None, sample=True, cuda=False, stop_chars=[],max_iter=1000):
        """ Generate one word at a time, in L->R order """
        seed_len = len(seed_text)
        block = []
        for curr_batch_index in range(batch_size):
          print("Batch {}".format(curr_batch_index))
          batch = self.get_init_text(seed_text, max_len) # batch_size sentences of max_len length with all mask, starting with [CLS] and separating by [SEP]

          for ii in range(max_len):
              if self.tokenizer.convert_ids_to_tokens(batch[0][:seed_len+ii])[-1][-1] in ['a','e','i','o','u']:
                lastVocal = True
              else:
                lastVocal = False
              if ii == 0:
                isFirst = True
              else:
                isFirst = False
              inp = [sent[:seed_len+ii+leed_out_len]+[self.sep_id] for sent in batch]
              inp = torch.tensor(batch).cuda() if self.cuda else torch.tensor(batch)
              out = self.model(inp) # ricava i valori logits
              idxs = self.generate_step(out, gen_idx=seed_len+ii, batch = batch, top_k=top_k, temperature=temperature, sample=sample,lastVocal=lastVocal, isFirst=isFirst)
              batch[0][seed_len+ii] = idxs[0]
              if self.noWiki:
                key = self.tokenizer.convert_ids_to_tokens(idxs[0])
              else:
                key = self.tokenizer.ids_to_tokens[idxs[0]]
              if key in stop_chars:
                batch[0] = batch[0][: seed_len+ii+1]
                #block.append(batch[0])
                break   
          block.append(batch[0])            
          #for _ in range(max_iter):
          #    kk = np.random.randint(0, len(block[-1])-seed_len-1) # seleziona un indice casuale tra 0 e max_len e maschera il relativo token in ogni sentences
          #    block[-1][seed_len+kk] = mask_id
          #    inp = torch.tensor([block[-1]]).cuda() if cuda else torch.tensor([block[-1]])
          #    out = model(inp)
          #    idxs = generate_step(out, gen_idx=seed_len+kk, top_k=top_k, temperature=temperature, sample=False)
          #    block[-1][seed_len+kk] = idxs[0]

        return self.untokenize_batch(block)


    def generate(self, n_samples, seed_text="[CLS]", batch_size=10, max_len=25, 
                 generation_mode="parallel-sequential", leed_out_len= 5,
                 sample=True, top_k=100, temperature=1.0, burnin=200, max_iter=500,
                 cuda=False, print_every=1, stop_chars=[]):
        # main generation function to call
        sentences = []
        n_batches = math.ceil(n_samples / batch_size) # approssima il rapporto a un numero intero e ripete il processo di generazione di batch_size sentences of length len_max n_batches times.
        start_time = time.time()
        for batch_n in range(n_batches):
            if generation_mode == "parallel-sequential":
                batch = parallel_sequential_generation(seed_text, batch_size=batch_size, max_len=max_len, top_k=top_k,
                                                       temperature=temperature, burnin=burnin, max_iter=max_iter, 
                                                       cuda=cuda, verbose=False)
            elif generation_mode == "sequential":
                batch = self.sequential_generation(seed_text, batch_size=batch_size, max_len=max_len, top_k=top_k, 
                                              temperature=temperature, leed_out_len=leed_out_len, sample=sample,
                                              cuda=cuda, stop_chars=stop_chars)
            elif generation_mode == "parallel":
                batch = parallel_generation(seed_text, batch_size=batch_size,
                                            max_len=max_len, top_k=top_k, temperature=temperature, 
                                            sample=sample, max_iter=max_iter, 
                                            cuda=cuda, verbose=True)

            if (batch_n + 1) % print_every == 0:
                print("Finished batch %d in %.3fs" % (batch_n + 1, time.time() - start_time))
                start_time = time.time()

            sentences += batch
        return sentences

    def generate_phrase(self, seed, num_phrase = 5):
        ff = preprocess_twitter(seed)
        frase = ff.split()
        frase = [self.CLS] + frase
        n_samples = num_phrase
        batch_size = num_phrase
        max_len = 40
        top_k = 50
        temperature = 1.0
        generation_mode = "sequential"
        leed_out_len = 5 # max_len
        burnin = 200
        sample = True
        max_iter = 600
        bert_sents = self.generate(n_samples, seed_text=frase, batch_size=batch_size, max_len=max_len,
                          generation_mode=generation_mode, leed_out_len= leed_out_len,
                          sample=sample, top_k=top_k, temperature=temperature, burnin=burnin, max_iter=max_iter,
                          cuda=self.cuda, stop_chars=["!","?","."])
        phrase = list()
        a = AlBERTo_Preprocessing(do_lower_case=True)
        b = a.preprocess(seed)
        for sent in bert_sents:
          sent = detokenize(sent)
          st = post_process_alberto(sent)
          st = st.replace(b,seed)
          phrase.append(st)

        return phrase

    def generate_hints(self, seed, num_hints = 5):
        ff = preprocess_twitter(seed)
        frase = ff.split()
        frase = [self.CLS] + frase
        n_samples = num_hints
        batch_size = num_hints
        max_len = 10
        top_k = 100
        temperature = 1.0
        generation_mode = "sequential"
        leed_out_len = 5 # max_len


        seed_len = len(frase)
        batch = self.get_init_text(frase, max_len) # batch_size sentences of max_len length with all mask, starting with [CLS] and separating by [SEP]

        inp = [sent[:seed_len+leed_out_len]+[self.sep_id] for sent in batch]
        inp = torch.tensor(batch).cuda() if self.cuda else torch.tensor(batch)
        out = self.model(inp) # ricava i valori logits
        gen_idx=seed_len

        if self.noWiki:
          logits = out.logits[:,gen_idx]
        else:
          logits = out[:,gen_idx]
        if temperature is not None:
            logits = logits / temperature

        kth_vals, kth_idx = logits.topk(top_k, dim=-1)
        self.idx_list = batch[0][:gen_idx]
        [self.idx_list.append(item) for item in self.list_subtoken_obtain]
        hints =list()
        for ii in range(num_hints):
            kth_idx , kth_vals=diff(kth_idx.tolist()[0],kth_vals.tolist()[0],self.idx_list)
            if kth_idx == []:
              top_k = len(self.idx_list)+num_hints
              kth_vals, kth_idx = logits.topk(top_k, dim=-1)
              kth_idx , kth_vals=diff(kth_idx.tolist()[0],kth_vals.tolist()[0],self.idx_list)
            kth_vals = torch.tensor([kth_vals]).cuda() if self.cuda else torch.tensor([kth_vals])
            kth_idx = torch.tensor([kth_idx]).cuda() if self.cuda else torch.tensor([kth_idx])
            dist = torch.distributions.categorical.Categorical(logits=kth_vals)
            idx = kth_idx.gather(dim=1, index=dist.sample().unsqueeze(-1)).squeeze(-1) 
            self.idx_list.append(idx.tolist()[0])
            if self.noWiki:
                hints.append(self.tokenizer.convert_ids_to_tokens(idx.tolist()[0]))
            else:
                hints.append(self.tokenizer.ids_to_tokens[self.idx_list[-1]])

        return hints
        
    def translate_func(self, text):
        emoji_it_to_en=["????","????","????","????","????","????","????","????","???","????","????","????","????","????",
              "????","????","????","????","????","????","????","????","????","????","????","????","???","????","<hashtag>","</hashtag>",
              "<url>","<annoyed>","<sad>","<happy>","<hearth>","<wink>","<number>","<user>","<devil>","<user>","<percent>","<money>","<phone>","<time>","<date>"]
        #divide le frasi in funzione delle emoji
        sentence_pieces = list()
        emojis = []
        text_components = text.split()
        last_emoji_index = 0
        for current_index in range(len(text_components)):
          word = text_components[current_index]
          if word in emoji_it_to_en:
            sentence_pieces.append(" ".join(text_components[last_emoji_index:current_index]))
            last_emoji_index = current_index+1
            emojis.append(word)
        sentence_pieces.append(" ".join(text_components[last_emoji_index:]))
        
        translated=[]
        for el in sentence_pieces:
          print(el)
          if len(el) == 0:
            translated.append(el)
            continue
          batch = self.tokenizerTrasl.prepare_seq2seq_batch(src_texts=[el],return_tensors='pt') 
          gen = self.modelTrasl.generate(**batch) 
          words: List[str] = self.tokenizerTrasl.batch_decode(gen, skip_special_tokens=True)
          print(words)
          sentence = ""
          for word in words:
            sentence += word.replace(".","").replace(",","")
          translated.append(sentence)
        
        new_sentence = []
        for i in range(len(translated)):
          new_sentence.append(translated[i])
          if i < len(emojis):
            new_sentence.append(emojis[i])

        return " ".join(new_sentence)
        
def preprocess_twitter(s):
    a = AlBERTo_Preprocessing(do_lower_case=True)
    b = a.preprocess(s)
    # 'url', 'email', 'user', 'percent', 'money', 'phone', 'time', 'date', 'number'
    frase = b.replace("<url>","< ##url ##>")
    frase = frase.replace("<email>","email")
    frase = frase.replace("<user>","< ##user ##>")
    frase = frase.replace("<percent>","< ##percent ##>")
    frase = frase.replace("<money>","< ##money ##>")
    frase = frase.replace("<phone>","< ##phone ##>")
    frase = frase.replace("<time>","< ##time ##>")
    frase = frase.replace("<date>","< ##date ##>")
    frase = frase.replace("<number>","< ##number ##>")
    frase = frase.replace("<hashtag>","< ##hashtag ##>")
    frase = frase.replace("</hashtag>","</ ##hashtag ##>")
    return frase

def post_process_alberto(sent):
    new_sent = []
    for i in range(len(sent)):
      if sent[i] == ">":
        if sent[i-2] == "<":
          new_sent[len(new_sent) - 2] = new_sent[len(new_sent) - 2] + sent[i-1] + sent[i]
          new_sent.pop(len(new_sent) - 1)
        elif sent[i-1] == "hashtag":
          if sent[i-2] == "/":
            if sent[i-3] == "<":
              new_sent.pop(len(new_sent) - 1)
              new_sent.pop(len(new_sent) - 2)
              new_sent.pop(len(new_sent) - 3)
              new_sent.append(sent[i-3]+sent[i-2]+sent[i-1]+sent[i])
              new_sent.pop(len(new_sent) - 2)
        elif sent[i-3] == "<":
          if sent[i-2]+sent[i-1] in ['url', 'email', 'user', 'percent', 'money', 'phone', 'time', 'date', 'number']:
              new_sent.pop(len(new_sent) - 1)
              new_sent.pop(len(new_sent) - 2)
              new_sent.pop(len(new_sent) - 3)
              new_sent.append(sent[i-3]+sent[i-2]+sent[i-1]+sent[i])
        else:
          new_sent.append(sent[i])
      else:
        new_sent.append(sent[i])

    st = " ".join(new_sent)
    st = st.replace("[CLS]","")
    st = st.replace("[SEP]","")
    return st

def diff(l1=[],l2=[],l3=[]):
    kht_idx = list()
    kht_value = list()
    for ss in range(len(l1)):
        if l1[ss] not in l3:
            kht_idx.append(l1[ss])
            kht_value.append(l2[ss])
    return kht_idx,kht_value

def detokenize(sent):
    """ Roughly detokenizes (mainly undoes wordpiece) """
    new_sent = []
    for i, tok in enumerate(sent):
        if tok.startswith("##"):
            new_sent[len(new_sent) - 1] = new_sent[len(new_sent) - 1] + tok[2:]
        else:
            new_sent.append(tok)
    return new_sent


def detokenize_alberto(tokens):
    """Converts a sequence of tokens (string) to a single string."""
    out_string = ' '.join(tokens).replace('##', '').strip()
    return out_string

def parse_hashtags(phrase: str):
    regex = r"<hashtag>(.*?)(<|$)(\/|$)( *|$)(h|$)(a|$)(s|$)(h|$)(t|$)(a|$)(g|$)(>|$)"

    matcher = re.compile(regex) 
    def parse_single_hashtag(hashtag: str):
        match = matcher.match(hashtag)
        group = match.group(1)
        return "#" + group.strip().title().replace(" ","")

    temp = phrase
    
    while True:
        m = matcher.search(temp)
        if m:
            hashtag = parse_single_hashtag(temp[m.start():m.end()])
            temp = temp[:m.start()]+hashtag+temp[m.end():]
        else:
            break

    temp=temp.replace("</hashtag> ","")
    temp=temp.replace(" < user "," <user> ")
    temp=temp.replace(" < url "," <url> ")
    temp=temp.replace(" !","!")
    temp=temp.replace(" ?","?")
    temp=temp.replace(" > "," ")
    temp=temp.replace(" < "," ")
    temp=temp.replace(" / "," ")
    return temp.strip()

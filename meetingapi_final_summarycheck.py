# -*- coding: utf-8 -*-
"""
Created on Mon Jan 16 08:45:23 2023

@author: User
"""
from fastapi import FastAPI, UploadFile,File
import uvicorn
import azurecore_final
from docx import Document
from fastapi.responses import FileResponse
from fastapi.responses import PlainTextResponse
import unicodedata
#後面做摘要的時候會用到，主要是用到斷詞的功能
#import jieba
import monpa
import re
from nltk.tokenize.api import TokenizerI
from nltk.tokenize.texttiling import TextTilingTokenizer
import numpy as np
import gensim
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
import shutil
import tempfile
import datetime
import os
import librosa
import soundfile as sf

app = FastAPI()

#檔案上傳API，之後串到Azure核心
@app.post("/upload",summary="上傳音訊",tags=["音訊處理"])
async def upload(file: UploadFile= File(...)):
    result_list=[]
    #確認暫存資料夾路徑
    print("Temp directory before changing it:", tempfile.gettempdir())
    print("讀取影音文件"+file.filename)
    #因為音訊或影片檔案較大直接上傳Fastapi會出現問題，故要分批寫入數據
    time_now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")# 抓取當前時間
    temp_file_name = f"{time_now}{file.filename}"  # 臨時資料的文件名稱
    batch_size = 10 * 2 ** 20   # 每次寫入文件的數據大小
    with open(temp_file_name, 'wb') as f:   # 分批寫入數據
        for i in iter(lambda: file.file.read(batch_size), b''):#分批寫入文件
            f.write(i)
    #轉換檔案成wav格式
    file_name = temp_file_name.split('.')[0]      
    y,sr= librosa.load(temp_file_name)
    y_16 = librosa.resample(y,sr,16000)
    sf.write(file_name+'.wav', y_16, 16000, 'PCM_16')
    #要回傳到GUI界面的變數串列
    all_text,sub=azurecore_final.from_file(file_name+'.wav')
    result_list.append(all_text)
    result_list.append(sub)
    
    #先切分段落之後再針對每一個段落進行摘要
    def is_punctuation_mark(ch: str) -> bool:
        if unicodedata.category(ch)[0] == 'P':
            return True
        return False
    class ChineseSentenceSegmenter(TokenizerI):
        def tokenize(self, text):
            sent = ""
            delimiters = {'。', '！'}
            for ch in list(text):
                sent += ch
                if ch in delimiters and sent:
                    yield sent
                    sent = ""
            if sent:
                yield sent
    class ChineseWordSegmenter(TokenizerI):
        def tokenize(self, text):
            #   better Chinese word segmentation can be used.
            for tok in monpa.cut(text):
                yield tok
    class ChineseTextTilingTokenizer(TextTilingTokenizer):
        def __init__(self):
            super().__init__(stopwords=set(), w=100, k=100)
            self.cws_model = ChineseWordSegmenter()
            self.css_model = ChineseSentenceSegmenter()
        def tokenize(self, text):
            #text = HanziConv.toSimplified(text)
            #print(text)
            sents = []
            for raw_sent in self.css_model.tokenize(text):
                sent = " ".join(list(self.cws_model.tokenize(raw_sent))).strip()
                sents.append(sent)
            text = "\n\n".join(sents)
            lowercase_text = text.lower()
            paragraph_breaks = self._mark_paragraph_breaks(text)
            text_length = len(lowercase_text)
            # Tokenization step starts here
            # Remove punctuation
            nopunct_text = ''.join(
                c for c in lowercase_text if not is_punctuation_mark(c)
            )
            nopunct_par_breaks = self._mark_paragraph_breaks(nopunct_text)

            tokseqs = self._divide_to_tokensequences(nopunct_text)
            # The morphological stemming step mentioned in the TextTile
            # paper is not implemented.  A comment in the original C
            # implementation states that it offers no benefit to the
            # process. It might be interesting to test the existing
            # stemmers though.
            # words = _stem_words(words)
            # Filter stopwords
            for ts in tokseqs:
                ts.wrdindex_list = [
                    wi for wi in ts.wrdindex_list if len(wi[0]) > 1 and wi[0] not in self.stopwords
                ]
            token_table = self._create_token_table(tokseqs, nopunct_par_breaks)
            # End of the Tokenization step
            gap_scores = self._block_comparison(tokseqs, token_table)
            smooth_scores = self._smooth_scores(gap_scores)
            depth_scores = self._depth_scores(smooth_scores)
            segment_boundaries = self._identify_boundaries(depth_scores)
            normalized_boundaries = self._normalize_boundaries(
                text, segment_boundaries, paragraph_breaks
            )
            segmented_text = []
            prevb = 0
            for b in normalized_boundaries:
                if b == 0:
                    continue
                segmented_text.append(text[prevb:b])
                prevb = b
            if prevb < text_length:  # append any text that may be remaining
                segmented_text.append(text[prevb:])
            if not segmented_text:
                segmented_text = [text]
            if self.demo_mode:
                return gap_scores, smooth_scores, depth_scores, segment_boundaries
            return segmented_text
    tokenizer = ChineseTextTilingTokenizer()

    #總字數500以上才會進段落切分
    if len(all_text)>500:
        #把切分出來的每一個段落存成一個陣列
        segs = list(tokenizer.tokenize(result_list[0]))
        #開始整理摘要
        summary=[]
        for i in range(0,len(segs)):
            summary.append("\n")
            summary.append("第"+str(i+1)+"段摘要")
            summary.append("\n")
            article_text = segs[i]
            article_text=article_text.replace(" ","")
            article_text=article_text.replace("\n","")
            sentences_list=[]
            sentences_list=re.split(r'[。:;?]',article_text)
            #創建停用詞列表
            stopwords = [line.strip() for line in open('./stopwords.txt',encoding='UTF-8').readlines()]  
            #對句子進行分詞
            def seg_depart(sentence):
                #去掉非國字字符
                sentence = re.sub(r'[^\u4e00-\u9fa5]+','',sentence)
                sentence_depart = monpa.cut(sentence.strip())
                word_list = []
                for word in sentence_depart:
                    if word not in stopwords:
                        word_list.append(word)   
                # 如果句子整個被過濾掉了，如：'02-2717:56'被過濾，那就返回[],保持句子的数量不變
                return word_list
            sentence_word_list = []
            for sentence in sentences_list:   
                line_seg = seg_depart(sentence)
                sentence_word_list.append(line_seg)
            print("一共有",len(sentences_list),'個句子。\n')
            print("前10個句子分詞後结果為：\n",sentence_word_list[:10])
            #保證處理後句子的數量不變，後面才能根據textrank值取出未處理前的句子作為摘要
            if len(sentences_list) == len(sentence_word_list):
                print("\n數據預處理後句子數量不變！")
            #讀取詞向量檔案
            model = gensim.models.KeyedVectors.load_word2vec_format('./wiki.zh.vector/2020v1.bin', 
                                                                    unicode_errors='ignore', 
                                                                    binary=True)      
            word_embedding = {}
            count=0
            for item in model.key_to_index:
                word_embedding[item]=model[item]
                count+=1
            print(count,"words are include as embedding")
            sentence_vec=[]
            for i in sentence_word_list:
                #print(i)
                if len(i)!=0:
                    # 如果句子中的詞語不在字典中，那就把embedding設為300维元素為0的向量。
                    # 得到句子中全部词的詞向量後，求平均值，得到句子的向量表示
                    v = sum([word_embedding.get(w, np.zeros((300,))) for w in i])/(len(i))
                else:
                    # 如果句子為[]，那么就向量表示为300维元素為0個向量。
                    v = np.zeros((300,))
                sentence_vec.append(v)
            sim_mat = np.zeros([len(sentences_list), len(sentences_list)])
            for i in range(len(sentences_list)):
              for j in range(len(sentences_list)):
                if i != j:
                  result=sim_mat[i][j]
                  sim_mat[i][j] = cosine_similarity(sentence_vec[i].reshape(1,300), sentence_vec[j].reshape(1,300))[0,0]
            print("句子相似度矩陣的形状為：",sim_mat.shape)
            # 利用句子相似度矩阵構建圖結構，句子為節點，句子相似度為轉換概率
            nx_graph = nx.from_numpy_array(sim_mat)
            # 得到所有句子的textrank值
            scores = nx.pagerank_numpy(nx_graph)
            # 根據textrank值對未處理的句子進行排序
            ranked_sentences = sorted(((scores[i],s) for i,s in enumerate(sentences_list)), reverse=True)
            # 取出得分最高的前10個句子作為摘要
            sn = 1
            for i in range(sn):
                print("第"+str(i+1)+"條摘要：\n\n",ranked_sentences[i][1],'\n')
                summary.append(ranked_sentences[i][1]) 
            #把摘要新增入summary陣列
            summary.append("\n")
        result_list.append(summary)
    else:
        #字數太少就不進入摘要功能
        result_list.append("字數太少，故無法產生摘要")
    return result_list

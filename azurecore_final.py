# -*- coding: utf-8 -*-
import azure.cognitiveservices.speech as speechsdk
import time
import json
import srt
import datetime
from os.path import getsize

#匯入音檔進去Azure辨識模組
def from_file(audio_file):
    print(audio_file)
    path = audio_file
    size = getsize(path)
    print('%s = %d bytes' % (path, size))
    all_results=[]
    results=[]
    words=[]
    transcript=[] 
    all_words=""
    #地端跟雲端更改這一行就好
    #地端版本
    speech_config = speechsdk.SpeechConfig(host="ws://azure-cognitive-service-speech-to-text:5000")
    #speech_config = speechsdk.SpeechConfig(host="ws://localhost:5000")
    #雲端版本
    #speech_config = speechsdk.SpeechConfig(subscription="5cc53c68cd8f4b37b8870a2e2046cd87", region="westus2")
    #讀檔
    audio_input = speechsdk.AudioConfig(filename=audio_file)
    #要辨識的語言
    speech_config.speech_recognition_language="zh-tw"
    #要求辨識時間
    speech_config.request_word_level_timestamps()
    speech_config.enable_dictation()
    speech_config.output_format = speechsdk.OutputFormat(1)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    #加入片語清單
    phrase_list_grammar = speechsdk.PhraseListGrammar.from_recognizer(speech_recognizer)
    phrase_list_grammar.addPhrase("人壽")
    phrase_list_grammar.addPhrase("議事")
    phrase_list_grammar.addPhrase("金控")
    phrase_list_grammar.addPhrase("邱柏洋")
    phrase_list_grammar.addPhrase("蘇啟明")
    phrase_list_grammar.addPhrase("潘柏錚")
    phrase_list_grammar.addPhrase("邱德成")
    phrase_list_grammar.addPhrase("林美花")
    phrase_list_grammar.addPhrase("吳昕達")
    phrase_list_grammar.addPhrase("吳昕達")
    phrase_list_grammar.addPhrase("洽悉")
    phrase_list_grammar.addPhrase("盈餘")
    phrase_list_grammar.addPhrase("討論事項")
    phrase_list_grammar.addPhrase("授信")
    phrase_list_grammar.addPhrase("協理")
    phrase_list_grammar.addPhrase("組織暨協理以上人員異動案")
    phrase_list_grammar.addPhrase("異動")
    phrase_list_grammar.addPhrase("決議")
    phrase_list_grammar.addPhrase("人資")
    phrase_list_grammar.addPhrase("陳錦慧")
    phrase_list_grammar.addPhrase("總合研究室")
    phrase_list_grammar.addPhrase("新光")
    phrase_list_grammar.addPhrase("元富")
    phrase_list_grammar.addPhrase("總務")
    phrase_list_grammar.addPhrase("勞安")
    phrase_list_grammar.addPhrase("公關")
    phrase_list_grammar.addPhrase("董事")
    phrase_list_grammar.addPhrase("新光人壽")
    phrase_list_grammar.addPhrase("資產")
    phrase_list_grammar.addPhrase("咎責")
    phrase_list_grammar.addPhrase("撤案")
    phrase_list_grammar.addPhrase("劉信成")
    phrase_list_grammar.addPhrase("說明")
    
    
    
    
    
    done = False
    #停止辨識
    def stop_cb(evt):
        print(f'CLOSING on {evt}')
        nonlocal done
        done = True
        speech_recognizer.stop_continuous_recognition()
    #儲存結果的變數

    #儲存結果的函式(有結果儲存就會到這裡來)
    def recognised_cb(evt):
        #all_results.append(evt.result.text) 
        print(all_results)
        results = json.loads(evt.result.json)
        transcript.append(results['DisplayText'])
        confidence_list_temp = [item.get('Confidence') for item in results['NBest']]
        max_confidence_index = confidence_list_temp.index(max(confidence_list_temp))
        words.extend(results['NBest'][max_confidence_index]['Words'])
        print(words)
    speech_recognizer.recognized.connect(recognised_cb)
    speech_recognizer.recognized.connect(lambda evt: all_results.append(evt.result.text))
    speech_recognizer.session_stopped.connect(stop_cb)
    speech_recognizer.canceled.connect(stop_cb)
    speech_recognizer.start_continuous_recognition()
    while not done:
        time.sleep(.5)       
    print("Printing all results:")
    print(all_results)
    print(words)
    speech_to_text_response = words
    #時間軸換算
    def convertduration(t):
        x= t/10000
        return int((x / 1000)), (x % 1000)   
    ##--開始創建字幕檔案--#    
    #3 Seconds
    bin = 3.0
    duration = 0 
    transcriptions = []
    transcript = ""
    index,prev=0,0
    wordstartsec,wordstartmicrosec=0,0
    for i in range(len(speech_to_text_response)):
        #Forms the sentence until the bin size condition is met
        transcript = transcript + " " + speech_to_text_response[i]["Word"]
        #Checks whether the elapsed duration is less than the bin size
        if(int((duration / 10000000)) < bin): 
            wordstartsec,wordstartmicrosec=convertduration(speech_to_text_response[i]["Offset"])
            duration= duration+speech_to_text_response[i]["Offset"]-prev
            prev=speech_to_text_response[i]["Offset"]
                    #transcript = transcript + " " + speech_to_text_response[i]["Word"]
        else : 
            index=index+1
            #transcript = transcript + " " + speech_to_text_response[i]["Word"]
            transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, wordstartsec, wordstartmicrosec), datetime.timedelta(0, wordstartsec+bin, 0), transcript))
            duration = 0 
            #print(transcript)
            transcript=""   
    transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, wordstartsec, wordstartmicrosec), datetime.timedelta(0, wordstartsec+bin, 0), transcript))
    subtitles = srt.compose(transcriptions)        
    for text in all_results:
        all_words=all_words+text
        
        
    all_words=all_words.replace("洽溪",  "洽悉")
    all_words=all_words.replace("人受",  "人壽")
    all_words=all_words.replace("人獸",  "人壽")
    all_words=all_words.replace("指漲",  "執掌")
    all_words=all_words.replace("復健",  "附件")
    all_words=all_words.replace("發炎",  "發言")
    all_words=all_words.replace("英語",  "盈餘")
    all_words=all_words.replace("氣歸",  "企規")
    all_words=all_words.replace("際協力",  "暨協理")
    all_words=all_words.replace("婚姻",  "會議")
    all_words=all_words.replace("洽西",  "洽悉")
    all_words=all_words.replace("恰西",  "洽悉")




    all_words=all_words.replace("洽悉",  "洽悉\n\n")


    all_words=all_words.replace("照案通過",  "照案通過\n\n")

    all_words=all_words.replace("按照修正案通過",  "按照修正案通過\n\n")

    all_words=all_words.replace("今天的議題",  "\n\n今天的議題")

    all_words=all_words.replace("我是丘博陽",  "我是丘博陽\n\n")

    all_words=all_words.replace("白洋董事長進行報告",  "白洋董事長進行報告\n\n")

    all_words=all_words.replace("獨立董事林美花",  "獨立董事林美花\n\n")

    all_words=all_words.replace("我是林美花",  "我是林美花\n\n")

    all_words=all_words.replace("我獨立董事吳啟明",  "我獨立董事吳啟明\n\n")


    all_words=all_words.replace("臨時動議",  "臨時動議\n\n")

    all_words=all_words.replace("請發言",  "請發言\n\n")

    all_words=all_words.replace("我是吳欣達",  "我是吳欣達\n\n")

    all_words=all_words.replace("補充說明",  "補充說明\n\n")
    all_words=all_words.replace("聽得到",  "聽得到\n\n")
    all_words=all_words.replace("進行說明",  "進行說明\n\n")
    all_words=all_words.replace("補充報告",  "補充報告\n\n")
    all_words=all_words.replace("撤案",  "撤案\n\n")
    return all_words,subtitles


        
    

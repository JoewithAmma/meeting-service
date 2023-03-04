# 會議記錄自動化
串接Azure stt服務，並將語音轉文字的逐字稿匯出並整理成摘要整理成word檔案

# 包含檔案
1.api\
負責傳輸檔案與格式轉換\
2.azure語音辨識核心\
以azure python SDK方式進行串接\
3.使用者GUI介面\
使用pysimplegui套件撰寫，後續可使用pyinstaller打包成exe

# 另附上
dockerfile(可打包api成docker image)\
yml檔(以docker compose啟動兩個container)\

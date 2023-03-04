# 1、从官方 Python 基础镜像开始
FROM python:3.9
RUN pip3 install nltk
RUN [ "python", "-c", "import nltk; nltk.download('all')" ]

# 2、将当前工作目录设置为 /code
# 这是放置 requirements.txt 文件和应用程序目录的地方

WORKDIR /test

# 3、先复制 requirements.txt 文件
# 由于这个文件不经常更改，Docker 会检测它并在这一步使用缓存，也为下一步启用缓存
COPY ./requirements.txt /test/requirements.txt
COPY ./stopwords.txt /test/stopwords.txt
COPY ./wiki.zh.vector/2020v1.bin /test/wiki.zh.vector/2020v1.bin
COPY ./wiki.zh.vector/wiki.zh.vector /test/wiki.zh.vector/wiki.zh.vector

# 4、运行 pip 命令安装依赖项
RUN pip install --no-cache-dir --upgrade -r /test/requirements.txt

# 5、复制 FastAPI 项目代码
COPY ./meetingapi_final_summarycheck.py /test/meetingapi_final_summarycheck.py
COPY ./azurecore_final.py /test/azurecore_final.py

RUN apt-get update -y && apt-get install -y --no-install-recommends build-essential gcc libsndfile1 
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y ffmpeg

EXPOSE 9004
# 6、运行服务
CMD ["uvicorn", "meetingapi_final:app", "--reload", "--host", "0.0.0.0", "--port", "9004"]
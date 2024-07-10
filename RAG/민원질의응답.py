#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import json

file_path = '민원.json'

#JSon파일 읽기
with open(file_path, 'r') as file:
    data = json.load(file)
    
#JSon파일 출력
print(json.dumps(data,ensure_ascii=False, indent=4))


# In[ ]:


# mmdata = dict()
# for m in data:
#     q = m['고객질문(요청)']
#     a = m['상담사답변']
#     id = m['대화셋일련번호']
    
#     # mmdata에 대화셋일련번호가 없으면 추가
#     if id not in mmdata:
#         mmdata[id] = []
        
#     # q 또는 a가 비어있지 않은 것만 추가
#     if q != "":
#         mmdata[id].append(q)
#     if a != "":
#         mmdata[id].append(a)
        
# mmdata

# #JSon파일 출력
# with open('mydata.json', 'w') as file:
#     json.dump(mmdata, file, ensure_ascii=False, indent=4)


# In[ ]:


# openAI API사용
# mydata.json 사용
# data 기반으로 대화셋 생성
# 한묶음 -> openAI -> 질문 답변 -> 5000번


# In[ ]:
from openai import OpenAI
from dotenv import load_dotenv
import json
load_dotenv()

MODEL="gpt-4o"
client = OpenAI()

with open('mydata.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
data_str = json.dumps(data, ensure_ascii=False, indent=4)


# In[ ]:
data = list(data.values())
data


# In[ ]:


#len(data)


# In[ ]:


#data0 = data[44]
logs = []
for d in data[:50]:
    stttt = '\n'.join(d)

    prompt = f"""다음 내용은 대화내용입니다. 대화내용을 한문장으로 출력하세요. 대화 내용에서 맥락을 분석하고 정보를 추출하는 것이 목적입니다.
요약하지 마시오. 구체적으로 작성하시오.
{stttt}
"""
    
    completion = client.chat.completions.create(
        model = MODEL,
        messages = [{"role": "user", "content": prompt}],
    )
    response = completion.choices[0].message.content
    print(response)
    logs.append({"source": stttt, "response": response})
    

# log.json 파일에 저장
with open('log.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(logs, ensure_ascii=False, indent=4))


# In[ ]:


# vector data 만들기 
# chromdb use
# openai embedding search. use case. 


# 내 데이터를 벡터 데이터로 만드는데 임베딩이라는걸 하는 거고...
# 디비에 벡터 데이터를 넣는다.

# 리트리버: 벡터 데이터를 가지고 검색하는 것


# In[ ]:





import json
from openai import OpenAI

def appendData(filename):
    client = OpenAI()
    # 민원.json 파일 읽기
    with open("chat_histories/"+filename, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 대화 데이터 정리
    conversations = {}
    for item in data:
        id = item['대화셋일련번호']
        q = item['고객질문']
        a = item['상담사답변']
        
        if id not in conversations:
            conversations[id] = []
        if q:
            conversations[id].append(q)
        if a:
            conversations[id].append(a)

    # OpenAI API를 사용하여 대화 처리
    logs = []
    for conv_id, conv in list(conversations.items()):  # 처음 50개만 처리
        stttt = '\n'.join(conv)

        prompt = f"""다음 내용은 대화내용입니다. 대화내용을 한문장으로 출력하세요. 대화 내용에서 맥락을 분석하고 정보를 추출하는 것이 목적입니다.
    요약하지 마시오. 구체적으로 작성하시오. 
    {stttt}
    """
        
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )
        response = completion.choices[0].message.content
        print(response)
        logs.append({"source": stttt, "response": response})

    try:
        with open('log.json', 'r', encoding='utf-8') as f:
            existing_logs = json.load(f)
    except FileNotFoundError:
        existing_logs = []

    # 새로운 logs를 기존 logs에 추가
    existing_logs.extend(logs)

    # log.json 파일에 저장
    with open('log.json', 'w', encoding='utf-8') as f:
        json.dump(existing_logs, f, ensure_ascii=False, indent=4)

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import json
import os
from langchain_core.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import Document
from langchain_core.output_parsers import StrOutputParser
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain.vectorstores import FAISS
from kiwipiepy import Kiwi

kiwi = Kiwi()
# 프롬프트 템플릿 설정
prompt = PromptTemplate.from_template(
    """
    주어진 문맥(context)을 주의 깊게 읽고, 질문(question)에 대한 답변을 찾아주세요. 
    문맥에 관련 정보가 있다면 반드시 그 정보를 사용하여 답변해주세요.
    만약 정확히 일치하는 정보가 없더라도, 관련된 정보가 있다면 그것을 바탕으로 추론하여 답변해주세요.
    완전히 관련 없는 경우에만 "주어진 정보에서 질문에 대한 정보를 찾을 수 없습니다"라고 답하세요.
    단, 기술적인 용어나 이름은 번역하지 않고 그대로 사용해 주세요.

    #Question:
    {question}

    #Context:
    {context}

    #Answer:
    """
)

# LLM 설정
llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

# JSON 데이터셋 로드 함수
def load_dataset(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data
def kiwi_tokenize(text):
    if isinstance(text, Document):
        text = text.page_content
    return [token.form for token in kiwi.tokenize(text)]

# 데이터셋에서 텍스트 추출 함수
def extract_texts(dataset):
    texts = []
    for i, entry in enumerate(dataset):
        if entry['QA'] == 'Q':
            question = entry.get('고객질문(요청)', '').strip()
            answer = ''
            for j in range(i+1, len(dataset)):
                if dataset[j]['QA'] == 'A' and dataset[j]['대화셋일련번호'] == entry['대화셋일련번호']:
                    answer = dataset[j].get('상담사답변', '').strip()
                    break
            if question and answer:
                texts.append(Document(page_content=f"Question: {question}\nAnswer: {answer}"))
    print("추출된 텍스트:", texts)  # 디버그를 위해 출력
    return texts

def extract_text(dataset):
    texts = []
    for entry in dataset:
        source = entry.get('source', '').strip()
        response = entry.get('response', '').strip()
        if source and response:
            texts.append(Document(page_content=f"Source: {source}\nResponse: {response}"))
    print("추출된 텍스트:", texts)  # 디버그를 위해 출력
    return texts

def create_chain(dataset_path):
    dataset = load_dataset(dataset_path)
    qa_pairs = extract_text(dataset)  # 텍스트 추출 함수로 수정

    if not qa_pairs:
        raise ValueError("The dataset does not contain any valid Q&A pairs.")

    # 텍스트 분할기 설정
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["Source:", "Response:", "\n", ". ", " ", ""]
    )


    splits = text_splitter.split_documents(qa_pairs)

    # 분할된 텍스트 출력 (디버깅용)
    print("Split texts:", [split.page_content for split in splits])

    if not splits:
        raise ValueError("Text splitting did not produce any valid text segments.")

    # BM25Retriever 및 FAISS 생성
    kiwi_bm25 = BM25Retriever.from_documents(splits, preprocess_func=kiwi_tokenize)
    faiss = FAISS.from_documents(splits, OpenAIEmbeddings()).as_retriever()
    
    kiwibm25_faiss_37 = EnsembleRetriever(
        retrievers=[kiwi_bm25, faiss],  # 사용할 검색 모델의 리스트
        weights=[0.3, 0.7],  # 각 검색 모델의 결과에 적용할 가중치
        search_type="mmr",  # 검색 결과의 다양성을 증진시키는 MMR 방식을 사용
        search_kwargs={"k":3}
    )
    retrievers = kiwibm25_faiss_37

    rag_chain = (
        {"context": retrievers, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain

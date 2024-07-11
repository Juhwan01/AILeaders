# Rag.py

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
from langchain_core.runnables import RunnablePassthrough
from langchain.schema import Document
from langchain_core.output_parsers import StrOutputParser
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from kiwipiepy import Kiwi
from dotenv import load_dotenv
import os

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

load_dotenv()
# OpenAI API 키 직접 설정 (주의: 이 방법은 보안상 권장되지 않습니다)
openai_api_key = os.getenv("OPENAI_API_KEY")

# LLM 설정
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, api_key=openai_api_key)

# JSON 데이터셋 로드 함수
def load_dataset(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def kiwi_tokenize(text):
    if isinstance(text, Document):
        text = text.page_content
    return [token.form for token in kiwi.tokenize(text)]

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
    qa_pairs = extract_text(dataset)

    if not qa_pairs:
        raise ValueError("The dataset does not contain any valid Q&A pairs.")

    # 텍스트 분할기 설정
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["Source:", "Response:", "\n", ". ", " ", ""]
    )

    splits = text_splitter.split_documents(qa_pairs)

    if not splits:
        raise ValueError("Text splitting did not produce any valid text segments.")

    # BM25Retriever 및 FAISS 생성
    kiwi_bm25 = BM25Retriever.from_documents(splits, preprocess_func=kiwi_tokenize)
    faiss = FAISS.from_documents(splits, OpenAIEmbeddings(api_key=openai_api_key)).as_retriever()
    
    kiwibm25_faiss_37 = EnsembleRetriever(
        retrievers=[kiwi_bm25, faiss],
        weights=[0.3, 0.7],
        search_type="mmr",
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

# 메인 실행 부분 (필요한 경우)
if __name__ == "__main__":
    dataset_path = "path/to/your/dataset.json"  # 실제 데이터셋 경로로 변경해주세요
    chain = create_chain(dataset_path)
    # 여기에 체인을 사용하는 코드를 추가할 수 있습니다
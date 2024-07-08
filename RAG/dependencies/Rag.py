from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_teddynote.retrievers import KiwiBM25Retriever
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import json
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
    당신은 질문-답변(Question-Answering)을 수행하는 친절한 AI 어시스턴트입니다. 당신의 임무는 주어진 문맥(context) 에서 주어진 질문(question) 에 답하는 것입니다.
    검색된 다음 문맥(context) 을 사용하여 질문(question) 에 답하세요. 만약, 주어진 문맥(context) 에서 답을 찾을 수 없다면, 답을 모른다면 `주어진 정보에서 질문에 대한 정보를 찾을 수 없습니다` 라고 답하세요.
    한글로 답변해 주세요. 단, 기술적인 용어나 이름은 번역하지 않고 그대로 사용해 주세요.

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
    for entry in dataset:
        if entry['QA'] == 'Q':
            question = entry.get('고객질문(요청)', '').strip()
            answer = ''
            for next_entry in dataset:
                if next_entry['QA'] == 'A' and next_entry['대화셋일련번호'] == entry['대화셋일련번호']:
                    answer = next_entry.get('상담사답변', '').strip()
                    break
            if question and answer:
                texts.append(Document(page_content=f"Question: {question}\nAnswer: {answer}"))
    print("추출된 텍스트:", texts)  # 디버그를 위해 출력
    return texts

def create_chain(dataset_path):
    dataset = load_dataset(dataset_path)
    qa_pairs = extract_texts(dataset)  # 텍스트 추출 함수로 수정

    if not qa_pairs:
        raise ValueError("The dataset does not contain any valid Q&A pairs.")

    # 텍스트 분할기 설정
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30, separators=[". ", "?"])
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
    )
    retrievers = kiwibm25_faiss_37

    rag_chain = (
        {"context": retrievers, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain

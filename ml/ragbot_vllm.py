# sudo apt install poppler-utils

from langchain.document_loaders import PyPDFLoader, TextLoader, WebBaseLoader, BSHTMLLoader
from langchain_community.document_loaders.youtube import YoutubeLoader
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.document_loaders import (
    UnstructuredMarkdownLoader,
    JSONLoader,
    UnstructuredXMLLoader,
    UnstructuredExcelLoader,
    ConfluenceLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader
)
from langchain_community.document_loaders.merge import MergedDataLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.llms import HuggingFacePipeline
from langchain_community.llms import VLLM
from langchain.prompts import PromptTemplate
from typing import List, Union, Dict, Any, Optional
from whisper_model import WhisperModel
import os


class EnhancedConversationBufferMemory(ConversationBufferMemory):
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        if self.input_key is None:
            self.input_key = list(inputs.keys())[0]

        if self.output_key is None:
            self.output_key = list(outputs.keys())[0]

        human_message = inputs[self.input_key]
        ai_message = outputs[self.output_key]

        self.chat_memory.add_user_message(human_message)
        self.chat_memory.add_ai_message(ai_message)


class RAGChatBot:
    def __init__(
        self,
        data_sources: List[tuple],
        model_name: str = 'Qwen/Qwen2.5-32B',
        embeddings_model: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        k_retriever: int = 5,
        save_path: str = 'vector_store.index',
        system_prompt:  Optional[str] = None
    ):
        self.data_sources = data_sources
        self.embeddings_model = embeddings_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.k_retriever = k_retriever
        self.save_path = save_path
        self.system_prompt = system_prompt

        if self.system_prompt:
            self.custom_prompt_template = f'''
            SYSTEM PROMPT: 
            {self.system_prompt}

            Контекст: 
            {{context}}

            Вопрос: 
            {{question}}

            История чата:
            {{chat_history}}

            Полезный ответ:
            '''

            self.custom_prompt = PromptTemplate(
                template=self.custom_prompt_template,
                input_variables=['context', 'question', 'chat_history'],
            )

        self.llm = self._get_model(
            model_name=model_name,
        )

        self.embeddings = self._get_embeddings()

        self.message_history = []
        self.chat_memory = None
        self.conversation_chain = None

        if self.data_sources:
            self.documents = self._load_data(self.data_sources)
            self.docs = self._split_data(self.documents)
            self.vector_store = self._create_vector_store()
            self._initialize_conversation_chain()

    def _initialize_conversation_chain(self):
        retriever = self.vector_store.as_retriever(search_kwargs={'k': self.k_retriever})

        self.chat_memory = EnhancedConversationBufferMemory(
            memory_key='chat_history',
            return_messages=True,
            input_key='question',
            output_key='answer'
        )

        kwargs = {}

        if self.system_prompt:
            kwargs['combine_docs_chain_kwargs'] = {'prompt': self.custom_prompt}

        self.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.chat_memory,
            return_source_documents=True,
            chain_type='stuff',
            **kwargs
        )

    def chat(self, query: str):
        if not self.conversation_chain:
            raise ValueError('Initialize chatbot with documents first')
        result = self.conversation_chain({'question': query})

        return result['answer'], result['source_documents']
    
    def chat_with_attachments(self, query: str, attachment_sources: List[Tuple[str]]):
        attachments_context = ""
        if attachment_sources:
            try:
                documents = self._load_data(attachment_sources)
            except Exception as e:
                raise RuntimeError(f"Ошибка загрузки файлов: {e}")
            
            attachments_context = "\n\n".join(
                doc.page_content for doc in documents if hasattr(doc, "page_content")
            )
        
        full_query = query
        if attachments_context:
            full_query += f"\n\nВложения:\n{attachments_context}. ИЩИ НА ВОПРОС ОТВЕТ ПО ВЛОЖЕНИЯХ!!!"
        
        result = self.conversation_chain({'question': full_query})
        
        return result['answer'], result['source_documents']

    def _load_data(self, sources: List[tuple]):
        loaders = []

        for mode, source in sources:
            if mode == 'file':
                if source.lower().endswith('.txt'):
                    try:
                        loaders.append(TextLoader(source, autodetect_encoding=True))
                    except Exception as e:
                        raise RuntimeError(f"Error loading .txt file '{source}': {e}")
                elif source.lower().endswith('.pdf'):
                    try:
                        loaders.append(PyPDFLoader(source))
                    except Exception as e:
                        raise RuntimeError(f"Error loading .pdf file '{source}': {e}")
                elif source.lower().endswith(('.doc', '.docx')):
                    try:
                        loaders.append(UnstructuredWordDocumentLoader(source))
                    except Exception as e:
                        raise RuntimeError(f"Error loading Word document '{source}': {e}")
                elif source.lower().endswith('.pptx'):
                    try:
                        loaders.append(UnstructuredPowerPointLoader(source))
                    except Exception as e:
                        raise RuntimeError(f"Error loading PowerPoint file '{source}': {e}")
                elif source.lower().endswith('.csv'):
                    try:
                        loaders.append(CSVLoader(source))
                    except Exception as e:
                        raise RuntimeError(f"Error loading .csv file '{source}': {e}")
                elif source.lower().endswith(('.html', '.htm')):
                    try:
                        loaders.append(BSHTMLLoader(source))
                    except Exception as e:
                        raise RuntimeError(f"Error loading HTML file '{source}': {e}")
                elif source.lower().endswith('.md'):
                    try:
                        loaders.append(UnstructuredMarkdownLoader(source))
                    except Exception as e:
                        raise RuntimeError(f"Error loading Markdown file '{source}': {e}")
                elif source.lower().endswith('.xml'):
                    try:
                        loaders.append(UnstructuredXMLLoader(source))
                    except Exception as e:
                        raise RuntimeError(f"Error loading XML file '{source}': {e}")
                elif source.lower().endswith('.json'):
                    try:
                        loaders.append(JSONLoader(
                            source,
                            jq_schema='.',
                            text_content=False
                        ))
                    except Exception as e:
                        raise RuntimeError(f"Error loading JSON file '{source}': {e}")
                elif source.lower().endswith(('.xls', '.xlsx')):
                    try:
                        loaders.append(UnstructuredExcelLoader(source))
                    except Exception as e:
                        raise RuntimeError(f"Error loading Excel file '{source}': {e}")
            elif mode == 'url':
                if source.startswith(('http://', 'https://')):
                    try:
                        loaders.append(WebBaseLoader(source))
                    except Exception as e:
                        raise RuntimeError(f"Error loading URL '{source}': {e}")
                else:
                    raise ValueError(f'Unsupported URL format: {source}')
            elif mode == 'confluence':
                try:
                    loaders.append(ConfluenceLoader(url=source))
                except Exception as e:
                    raise RuntimeError(f"Error loading Confluence data: {e}")
            elif mode == 'youtube':
                try:
                    loaders.append(YoutubeLoader(source, language='ru'))
                except Exception as e:
                    raise RuntimeError(f"Error loading YouTube data from '{source}': {e}")
            elif mode == 'image':
                try:
                    loaders.append(ImageCaptionLoader(source))
                except Exception as e:
                    raise RuntimeError(f"Error loading image '{source}': {e}")
            else:
                raise ValueError(f'Unsupported mode: {mode}')

        merged_loader = MergedDataLoader(loaders=loaders)
        return merged_loader.load()


    def _split_data(self, documents):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        return text_splitter.split_documents(documents)

    def _get_embeddings(self, retriever: str = None):
        return HuggingFaceEmbeddings(model_name=retriever or self.embeddings_model)

    def _get_model(self, model_name: str = None):
        llm = VLLM(
            model=model_name,
            trust_remote_code=True,
            max_new_tokens=1024,
            top_k=10,
            top_p=0.95,
            temperature=0.7,
        )

        return llm

    def _create_vector_store(self):
        if os.path.exists(self.save_path):
            print(f'Loading existing vector store from {self.save_path}')
            vector_store = FAISS.load_local(self.save_path, self.embeddings, allow_dangerous_deserialization=True)
        else:
            print(f'Creating new vector store and saving to {self.save_path}')
            vector_store = FAISS.from_documents(
                documents=self.docs,
                embedding=self.embeddings
            )
            vector_store.save_local(self.save_path)
        return vector_store

    def add_sources(self, new_sources: List[tuple]):
        new_documents = self._load_data(new_sources)
        new_docs = self._split_data(new_documents)

        self.vector_store.add_documents(new_docs)
        self.vector_store.save_local(self.save_path)

        self.data_sources.extend(new_sources)
        print(f'Successfully added {len(new_sources)} new sources to the chatbot.')

    def remove_sources(self, sources_to_remove: List[tuple]):
        self.data_sources = [
            source for source in self.data_sources if source not in sources_to_remove
        ]

        self.documents = self._load_data(self.data_sources)
        self.docs = self._split_data(self.documents)

        self.vector_store = FAISS.from_documents(self.docs, self.embeddings)
        self.vector_store.save_local(self.save_path)
        print(f'Successfully removed {len(sources_to_remove)} new sources from the chatbot.')

    def change_model(self, new_model_name: str):
        self.llm = self._get_model(
            model_name=new_model_name,
        )
        self._initialize_conversation_chain()
        print(f'Model successfully changed to {new_model_name}.')

    def change_retriever(self, new_embeddings_model: str):
        self.embeddings = self._get_embeddings(retriever=new_embeddings_model)
        self.vector_store = self._create_vector_store()
        self._initialize_conversation_chain()
        print(f'Retriever successfully changed to {new_embeddings_model}.')

    def change_prompt(self, new_system_prompt: str):
        self.system_prompt = new_system_prompt
        self.custom_prompt_template = f'''
        SYSTEM PROMPT: 
        {self.system_prompt}

        Контекст: 
        {{context}}

        Вопрос: 
        {{question}}

        История чата:
        {{chat_history}}

        Полезный ответ:
        '''

        self.custom_prompt = PromptTemplate(
            template=self.custom_prompt_template,
            input_variables=['context', 'question', 'chat_history'],
        )

        self._initialize_conversation_chain()
        print(f'System prompt successfully changed to: {new_system_prompt}')

    def change_index(self, index_path: str):
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"The specified index file '{index_path}' does not exist.")

        try:
            self.vector_store = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
            self.save_path = index_path
            self._initialize_conversation_chain()
            print(f"Index successfully changed to '{index_path}' and reloaded.")
        except Exception as e:
            raise RuntimeError(f"Failed to load the new index from '{index_path}': {e}")


# roles = {
#     "знаток личного кабинета": "Ты — интеллектуальный ассистент, отвечающий на вопросы пользователей на основе базы знаний ППР. \nТвоя задача:\n- Отвечать кратко, понятно и по существу.\n- Использовать исключительно факты, содержащиеся в базе (не выдумывай).\n- Если информация отсутствует, честно сообщай, что она не найдена.\n- Структура и стиль ответа должны соответствовать официальному тону.",
#     "аналитик": "Ты аналитик. Твоя задача — предоставить четкий, обоснованный и краткий анализ ситуации. Используй данные и логику для поддержки своих выводов. Избегай лишних деталей и философствования.",
#     "ресерчер": "Ты исследователь. Твоя задача — провести глубокое исследование темы, предоставить подробный контекст и ссылки на источники. Быть объективным и всесторонним в оценке информации.",
#     "технический эксперт": "Ты технический эксперт. Твоя задача — давать точные, технические ответы, основанные на глубоком знании предмета. Используй специализированный терминологический словарь, когда это необходимо.",
#     "помощник": "Ты помощник. Твоя задача — предоставить понятные и доброжелательные ответы, помогая пользователю решить его проблему. Быть эмпатичным и готовым предложить альтернативные решения.",
#     "творец": "Ты творец. Твоя задача — предлагать креативные и нестандартные решения, выходящие за рамки традиционного мышления. Быть инновационным и экспериментальным в подходе.",
#     "учёный": "Ты учёный. Твоя задача — отвечать строго на основе фактов, научных данных и объективного анализа. Избегай субъективных мнений и сосредоточься на доказательствах.",
#     "юрист": "Ты юрист. Твоя задача — предоставить правовую консультацию, основанную на законодательстве и precedents. Быть точным в юридических терминах и предоставить рекомендации по действию.",
#     "маркетолог": "Ты маркетолог. Твоя задача — предоставить стратегические рекомендации по продвижению продукта или услуги, основанные на рыночных исследованиях и тенденциях.",
#     "разработчик": "Ты разработчик. Твоя задача — предоставить технические решения для программных проблем, используя свой опыт в области разработки software.",
#     "финансовый аналитик": "Ты финансовый аналитик. Твоя задача — проводить анализ финансовых показателей, предсказывать тенденции и предоставлять рекомендации по инвестициям."
# }

# chatbot = RAGChatBot(
#     model_name='trained_ppr_gemma/gemma-2-9b-it-4bit',
#     save_path='vector_store_1',
#     system_prompt=roles['знаток личного кабинета'],
#     data_sources=[
#         ('file', '/content/2408.17352v1.pdf'), # PDF
#         ('file', '/content/Bulgakov_Mihail_Master_i_Margarita_Readli.Net_bid256_5c1f5.txt'), # TXT
#         ('file', '/content/Пример №1.docx_[regforum].docx'), # WORD
#         ('file', '/content/sample_submission.csv'), # CSV
#         ('file', '/content/https___python.langchain.com_v0.1_docs_modules_data_connection_document_loaders_html_.htm'), # HTML
#         ('file', '/content/README.md'), # MARKDOWN
#         ('file', '/content/10kb.json'), # JSON
#         ('file', '/content/1.xml'), # XML
#         ('file', '/content/file_example_XLSX_1000.xlsx'), # EXCEL
#         ('file', '/content/pohmele.mp3'), # AUDIO
#         ('confluence', 'https://yoursite.atlassian.com/wiki'), # CONFLUENCE
#         ('youtube', 'OMSm9pZdNzE'), # YOUTUBE VIDEO
#         ('image', '/content/opz74tkuiuj7gj2ute0yeg0d-sy.jpeg'), # ANY IMAGE
#         ('url', 'https://www.petrolplus.ru/'), # ANY URL
#     ],
#     embeddings_model='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
# )

# chatbot.add_sources([
#     ('url', 'https://zakupki.mos.ru/'),
# ])

# ans, source = chatbot.chat('что такое ппр')

# ans, source = chatbot.chat_with_attachments('что ты видишь на таблице', attachment_sources=[('image', 'pivottable1.png')])

# chatbot.remove_sources([
#     ('file', '/content/sample_submission.csv'),
# ])

# ans, source = chatbot.chat('что такое ппр')

# chatbot.change_model(new_model_name='Qwen/Qwen2.5-32B')

# chatbot.change_retriever(new_embeddings_model='sentence-transformers/all-MiniLM-L6-v2')
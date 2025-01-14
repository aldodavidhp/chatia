import streamlit as st
import google.generativeai as genai
import PyPDF2





st.header("¿En qué puedo ayudarte?")
# Cargar variables de entorno desde el archivo .env
#load_dotenv()

# Configurar la clave API de Google AI
#GOOGLE_API_KEY = os.getenv("AIzaSyAzPOlBiKoXpqFRLFzG6z_wuqPLE-aay4c")
genai.configure(api_key="AIzaSyAzPOlBiKoXpqFRLFzG6z_wuqPLE-aay4c")

# Cargar el modelo Gemini
model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Usar gemini-2.0-flash-exp

#pdf_obj= st.file_uploader("Carga tu documento", type= "pdf",)

#st.cache_resource
user_query = st.text_input("Haz tu pregunta",label_visibility="hidden")
def extract_text_from_pdf(pdf_path):
    """Extrae el texto de un PDF."""
    text = ""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        print(f"Error al procesar el PDF: {e}")
        return None
    return text



def chat_with_gemini(pdf_text, user_query):
    """Chatea con Gemini usando el contexto del texto del PDF."""
    if not pdf_text:
        return "No se pudo extraer texto del PDF."

    prompt = f"Aquí tienes el contexto de la formación:\n\n{pdf_text}\n\nPregunta: {user_query}"
    temperature = 0.5
    try:
       response = model.generate_content(prompt)
       return response.text
    except Exception as e:
        return f"Error al interactuar con Gemini: {e}"



  #  knowledge_base = create_emebddings(pdf_obj)
   # user_query = st.text_input("Has una pregunta")

    #if user_query:
        #API_KEY ="AIzaSyAzPOlBiKoXpqFRLFzG6z_wuqPLE-aay4c" #os.environ["API_KEY"]
        #docs= knowledge_base.similarity_search(user_query, 3)
        #genai.configure(api_key=API_KEY)
        #model= genai.GenerativeModel("gemini-1.5-flash")
        #llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
        #chain = load_qa_chain(llm, chain_type="stuff")
        #chain = load_qa_chain(model, chain_type="stuff")
        #respuesta= chain.run(input_document=docs, question= user_question)
        #respuesta= model.generate_content(user_question)
pdf_text = extract_text_from_pdf("DDAW1.pdf")
#pdf_text = extract_text_from_pdf("DDAW.pdf")

if pdf_text and user_query:
    answer = chat_with_gemini(pdf_text, user_query)
    print("Respuesta de Gemini:\n", answer)
    st.write(answer)




import streamlit as st
import os
import tempfile
from PyPDF2 import PdfReader
from docx import Document
import google.generativeai as genai
from PIL import Image

# Configuración de la página
st.set_page_config(page_title="Evaluador de Trabajos", page_icon="📝", layout="wide")

# Título de la aplicación
st.title("📝 Evaluador de Trabajos con IA")
st.markdown("""
Sube los criterios de evaluación en PDF y los trabajos de los alumnos (PDF o Word) para obtener 
una evaluación automatizada con retroalimentación detallada usando IA.
""")

# Sidebar para configuración
with st.sidebar:
    st.header("Configuración")
    
    # Campo para ingresar la API Key
    api_key = st.text_input("Ingresa tu API Key de Gemini AI", type="password", 
                          help="Puedes obtener una API Key en https://aistudio.google.com/app/apikey")
    
    # Opción para mostrar calificación numérica
    mostrar_calificacion = st.checkbox("Mostrar calificación numérica", value=False,
                                     help="Activa esta opción para incluir una puntuación del 1 al 10 en la evaluación")
    
    # Sliders para ajustar el comportamiento de la IA
    temperature = st.slider("Creatividad de las evaluaciones", 0.0, 1.0, 0.5, help="Valores más altos = respuestas más creativas pero menos precisas")
    max_tokens = st.slider("Longitud máxima de respuestas", 100, 2000, 1200, help="Controla cuán detalladas serán las evaluaciones")
    
    st.divider()
    st.info("""
    **Instrucciones:**
    1. Sube los criterios de evaluación en PDF
    2. Sube los trabajos de los estudiantes (PDF o Word)
    3. Revisa las evaluaciones generadas automáticamente
    """)

# Función para extraer texto de PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    pdf_reader = PdfReader(pdf_file)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Función para extraer texto de Word
def extract_text_from_word(word_file):
    doc = Document(word_file)
    return "\n".join([para.text for para in doc.paragraphs])

# Función para procesar archivos de alumnos
def process_student_file(file):
    try:
        if file.type == "application/pdf":
            return extract_text_from_pdf(file)
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return extract_text_from_word(file)
        else:
            return None
    except Exception as e:
        st.error(f"Error procesando archivo {file.name}: {str(e)}")
        return None

# Función para evaluar con Gemini
def evaluate_with_gemini(criteria, student_work, student_name=""):
    # Verificar que la API Key esté configurada
    if 'api_key' not in st.session_state or not st.session_state.api_key:
        return "Error: Por favor ingresa una API Key válida en la barra lateral"
    
    # Construir el prompt según si se solicita calificación numérica o no
    if st.session_state.mostrar_calificacion:
        prompt = f"""
        Eres un profesor universitario experto en evaluación de trabajos académicos. 
        A continuación te proporciono los criterios de evaluación y el trabajo de un estudiante o docente.
        
        **CRITERIOS DE EVALUACIÓN:**
        {criteria}
        
        **TRABAJO DEL ESTUDIANTE O DOCENTE {student_name.upper() if student_name else ''}:**
        {student_work}
        
        Proporciona una evaluación detallada que incluya:
        
        1. **CALIFICACIÓN NUMÉRICA** (una puntuación del 1 al 10 basada en los criterios)
        2. **PUNTOS FUERTES** (1-3 aspectos bien desarrollados)
        3. **ÁREAS DE MEJORA** (1-3 aspectos a mejorar con sugerencias concretas)
        4. **COMENTARIOS FINALES** (retroalimentación constructiva y motivadora)
        
        Usa un tono profesional pero cercano, destacando los logros y ofreciendo guía para mejorar.
        Organiza la respuesta con encabezados claros y bullet points para mejor legibilidad.
        La calificación numérica debe aparecer primero, destacada entre asteriscos como **7/10**.
        La retroalimentación constructiva y motivadora sea máximo 200 caracteres.
        """
    else:
        prompt = f"""
        Eres un profesor universitario experto en evaluación de trabajos académicos. 
        A continuación te proporciono los criterios de evaluación y el trabajo de un estudiante o docente.
        
        **CRITERIOS DE EVALUACIÓN:**
        {criteria}
        
        **TRABAJO DEL ESTUDIANTE O DOCENTE {student_name.upper() if student_name else ''}:**
        {student_work}
        
        Proporciona una evaluación detallada que incluya:
        
        1. **PUNTOS FUERTES** (1-3 aspectos bien desarrollados)
        2. **ÁREAS DE MEJORA** (1-3 aspectos a mejorar con sugerencias concretas)
        3. **COMENTARIOS FINALES** (retroalimentación constructiva y motivadora)
        
        Usa un tono profesional pero cercano, destacando los logros y ofreciendo guía para mejorar.
        Organiza la respuesta con encabezados claros y bullet points para mejor legibilidad.
        La retroalimentación constructiva y motivadora sea máximo 200 caracteres.
        """
    
    try:
        # Configurar el modelo con la API Key actual
        genai.configure(api_key=st.session_state.api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        safety_settings = {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.9
            ),
            safety_settings=safety_settings
        )
        
        # Verificar si la respuesta tiene contenido antes de acceder a .text
        if response.parts:
            return response.text
        else:
            # Si no hay contenido, la respuesta fue bloqueada. Devolver el feedback.
            return f"Error: La respuesta fue bloqueada por la API. Razón: {response.prompt_feedback}. Esto puede ocurrir si el contenido del PDF o de los criterios infringe las políticas de seguridad, incluso con los filtros desactivados."
            
    except Exception as e:
        return f"Error al evaluar: {str(e)}"

# Almacenar la API Key y preferencias en session_state cuando se ingresan
if api_key:
    st.session_state.api_key = api_key
if 'mostrar_calificacion' not in st.session_state:
    st.session_state.mostrar_calificacion = mostrar_calificacion
else:
    st.session_state.mostrar_calificacion = mostrar_calificacion

# Interfaz principal
tab1, tab2 = st.tabs(["📋 Subir Criterios", "🧑‍🎓 Evaluar Trabajos"])

with tab1:
    st.header("Criterios de Evaluación")
    criteria_file = st.file_uploader("Sube el PDF con los criterios de evaluación", type=["pdf"], 
                                   help="El archivo debe contener los rubros, puntajes y estándares de evaluación")
    
    if criteria_file:
        with st.spinner("Procesando criterios de evaluación..."):
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(criteria_file.getvalue())
                criteria_text = extract_text_from_pdf(tmp.name)
            
            st.session_state.criteria_text = criteria_text
            st.success("✅ Criterios cargados correctamente!")
            
            st.subheader("Vista previa de los criterios")
            st.text_area("Contenido extraído", criteria_text, height=300, disabled=True, 
                        label_visibility="collapsed")

with tab2:
    st.header("Evaluar Trabajos de Estudiantes")
    
    if 'criteria_text' not in st.session_state:
        st.warning("⚠️ Por favor sube primero los criterios de evaluación en la pestaña 'Subir Criterios'")
    elif 'api_key' not in st.session_state or not st.session_state.api_key:
        st.warning("⚠️ Por favor ingresa tu API Key de Gemini AI en la barra lateral")
    else:
        student_files = st.file_uploader(
            "Sube los trabajos de los estudiantes (PDF o Word)", 
            type=["pdf", "docx"],
            accept_multiple_files=True,
            help="Puedes seleccionar múltiples archivos a la vez"
        )
        
        if student_files:
            progress_bar = st.progress(0)
            total_files = len(student_files)
            
            for i, file in enumerate(student_files):
                progress_bar.progress((i + 1) / total_files, f"Procesando {i+1}/{total_files}: {file.name}")
                
                with st.expander(f"📄 {file.name}", expanded=i==0):
                    with st.spinner(f"Analizando {file.name}..."):
                        student_text = process_student_file(file)
                        
                        if student_text:
                            # Extraer nombre del archivo sin extensión para personalización
                            student_name = os.path.splitext(file.name)[0]
                            
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.subheader("📋 Contenido del Trabajo")
                                st.text_area(f"Contenido {file.name}", student_text[:5000] + ("..." if len(student_text) > 5000 else ""), 
                                            height=300, disabled=True, label_visibility="collapsed")
                                st.caption(f"Mostrando primeros 5000 caracteres de {len(student_text)} totales")
                            
                            with col2:
                                st.subheader("📝 Evaluación Automática")
                                evaluation = evaluate_with_gemini(st.session_state.criteria_text, student_text, student_name)
                                
                                # Si se solicita calificación numérica, resaltarla
                                if st.session_state.mostrar_calificacion:
                                    st.markdown("### Calificación")
                                    # Buscar el patrón **X/10** en la respuesta
                                    if "**" in evaluation and "/10" in evaluation:
                                        calificacion = evaluation.split("**")[1]
                                        st.metric(label="Puntuación", value=calificacion)
                                        st.markdown("---")
                                
                                st.markdown(evaluation)
                                
                                # Opción para descargar la evaluación
                                st.download_button(
                                    label="⬇️ Descargar Evaluación Completa",
                                    data=evaluation,
                                    file_name=f"Evaluacion_{student_name}.txt",
                                    mime="text/plain",
                                    key=f"download_{i}",
                                    help="Descarga esta evaluación como archivo de texto"
                                )
                        else:
                            st.error(f"❌ No se pudo procesar el archivo {file.name}")

            progress_bar.empty()
            st.success(f"✅ Procesamiento completado! {total_files} trabajos evaluados")


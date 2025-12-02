import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import os
import time

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Asistente Operativo 4.0",
    page_icon="⛏️",
    layout="centered"
)

# Estilos CSS para mejorar la apariencia (Opcional pero recomendado)
st.markdown("""
<style>
    .stTextInput input {
        font-size: 16px;
        padding: 10px;
    }
    div[data-testid="stForm"] {
        border: 1px solid #ddd;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. SISTEMA DE SEGURIDAD (MEJORADO VISUALMENTE)
# ---------------------------------------------------------
PASSWORD_DEMO = "MINERIA2025"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login_screen():
    # Usamos columnas para centrar el formulario: [Espacio, Formulario, Espacio]
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True) # Espacio vertical
        st.image("https://cdn-icons-png.flaticon.com/512/9630/9630006.png", width=100) # Icono de seguridad
        st.title("Acceso Corporativo")
        st.markdown("Ingrese sus credenciales para acceder al **Asistente Operativo AI**.")
        
        with st.form("login_form"):
            password = st.text_input("Contraseña de acceso", type="password")
            submitted = st.form_submit_button("INGRESAR AL SISTEMA", use_container_width=True)
            
            if submitted:
                if password == PASSWORD_DEMO:
                    st.session_state.authenticated = True
                    st.success("Acceso concedido. Cargando entorno...")
                    time.sleep(1) # Pequeña pausa dramática
                    st.rerun() # Recarga la página para entrar
                else:
                    st.error("⛔ Contraseña incorrecta.")

if not st.session_state.authenticated:
    login_screen()
    st.stop() # Aquí se detiene todo si no ha entrado

# ---------------------------------------------------------
# 3. CONEXIÓN A SERVICIOS (Igual que antes)
# ---------------------------------------------------------
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    from dotenv import load_dotenv
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Error de credenciales: {e}")
    st.stop()

# ---------------------------------------------------------
# 4. LÓGICA DE IA (RAG - Igual que antes)
# ---------------------------------------------------------
def buscar_contexto_en_db(pregunta_usuario):
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=pregunta_usuario,
            task_type="retrieval_query"
        )
        query_vector = result['embedding']
        response = supabase.rpc("match_documents", {
            "query_embedding": query_vector,
            "match_threshold": 0.4,
            "match_count": 5,
        }).execute()
        return response.data
    except Exception as e:
        return []

def generar_respuesta_ia(pregunta, contextos):
    texto_base = ""
    fuentes_lista = []
    if contextos:
        for doc in contextos:
            texto_base += f"---\n{doc['content']}\n"
            fuente_preview = doc['content'][:100].replace("\n", " ") + "..."
            fuentes_lista.append(fuente_preview)
    else:
        texto_base = "No se encontró información específica."

    system_prompt = f"""
    Eres el Asistente Operativo 4.0 (Minex Corp).
    INSTRUCCIONES:
    1. Usa SOLO la información de "CONTEXTO RECUPERADO".
    2. Explica con pedagogía sencilla y analogías si es necesario.
    3. CITA SIEMPRE la fuente (Ej: Art. 203).
    4. Si no sabes, dilo honestamente.

    CONTEXTO RECUPERADO:
    {texto_base}
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    chat = model.start_chat(history=[])
    response = chat.send_message(f"Sistema: {system_prompt}\n\nUsuario: {pregunta}")
    return response.text, fuentes_lista

# ---------------------------------------------------------
# 5. INTERFAZ GRÁFICA (LA MAGIA DEL CENTRO)
# ---------------------------------------------------------

# Inicializar historial si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []

# LOGICA DE PANTALLA
# Si el historial está vacío, mostramos el diseño "Google Search" en el centro
if len(st.session_state.messages) == 0:
    
    # Espaciadores para empujar todo al centro verticalmente
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/3616/3616927.png", width=80)
        st.markdown("<h1 style='text-align: center;'>Asistente Operativo 4.0</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Consulta normativa interna, Código de Minas y procesos de seguridad.</p>", unsafe_allow_html=True)
        
        # INPUT CENTRAL (Solo aparece al principio)
        pregunta_inicial = st.text_input("🔍", placeholder="Ej: ¿Qué requisitos necesito para una licencia?", label_visibility="collapsed")
        
        if pregunta_inicial:
            # Guardamos la pregunta y recargamos para pasar a la vista de chat
            st.session_state.messages.append({"role": "user", "content": pregunta_inicial})
            st.rerun()

    # Sugerencias rápidas (Botones debajo del buscador)
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    # Agregamos use_container_width=True para que se estiren y queden alineados
    if c1.button("📜 Licencias", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "¿Qué tipos de licencias mineras existen?"})
        st.rerun()
    
    if c2.button("💰 Regalías", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "¿Cómo se calculan las regalías?"})
        st.rerun()
        
    if c3.button("⚠️ Seguridad", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "¿Cuáles son las normas de seguridad en socavón?"})
        st.rerun()

# ---------------------------------------------------------
# VISTA DE CHAT (Se activa cuando ya hay mensajes)
# ---------------------------------------------------------
else:
    # Encabezado pequeño
    col_a, col_b = st.columns([1, 10])
    with col_a:
        st.image("https://cdn-icons-png.flaticon.com/512/3616/3616927.png", width=40)
    with col_b:
        st.subheader("Asistente Operativo - Chat Activo")
    st.divider()

    # Mostrar historial
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Lógica de respuesta automática (Si el último mensaje es del usuario y no tiene respuesta aún)
    if st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Analizando..."):
                prompt = st.session_state.messages[-1]["content"]
                contextos = buscar_contexto_en_db(prompt)
                respuesta, fuentes = generar_respuesta_ia(prompt, contextos)
                
                st.markdown(respuesta)
                if fuentes:
                    with st.expander("📚 Fuentes"):
                        for f in fuentes: st.caption(f"• {f}")
                
                # Agregamos la respuesta al historial para que no se repita
                st.session_state.messages.append({"role": "assistant", "content": respuesta})

    # INPUT INFERIOR (El estándar de chat para continuar la conversa)
    if prompt := st.chat_input("Escribe tu consulta..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import create_client, Client
import pypdf

# 1. Configuración
load_dotenv()
supa_url = os.getenv("SUPABASE_URL")
supa_key = os.getenv("SUPABASE_KEY")
google_key = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=google_key)
supabase: Client = create_client(supa_url, supa_key)

CARPETA_DOCS = "documentos"

def get_embedding(text):
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",
        )
        return result['embedding']
    except Exception as e:
        # Si falla el embedding, retornamos None para manejarlo luego
        return None

def archivo_ya_existe(filename):
    """Verifica si el archivo ya está en Supabase buscando en los metadatos"""
    try:
        # Buscamos si existe al menos 1 registro con ese "source" en los metadatos
        # La sintaxis 'metadata->>source' es para buscar dentro del JSON
        response = supabase.table("documents") \
            .select("id") \
            .eq("metadata->>source", filename) \
            .limit(1) \
            .execute()
        
        # Si la lista 'data' no está vacía, es que ya existe
        if len(response.data) > 0:
            return True
        return False
    except Exception as e:
        print(f"⚠️ Error verificando duplicados: {e}")
        return False

def process_file(filename):
    # --- PASO DE SEGURIDAD: VERIFICAR DUPLICADOS ---
    if archivo_ya_existe(filename):
        print(f"⏭️  Saltando {filename} (Ya existe en base de datos)")
        return  # Sale de la función y no hace nada más con este archivo
    
    # Si no existe, procedemos normal...
    file_path = os.path.join(CARPETA_DOCS, filename)
    print(f"\n📄 Procesando NUEVO archivo: {filename}...")
    
    try:
        reader = pypdf.PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            texto_pag = page.extract_text()
            if texto_pag: full_text += texto_pag + "\n"

        full_text = full_text.replace(" .", ".") 
        
        # Estrategia de corte (Chunking)
        if full_text.lower().count("artículo") > 10:
            print("   ⚖️ Formato Legal detectado.")
            pattern = r'(?i)(ART[ÍI]CULO\s+\d+|CAP[ÍI]TULO\s+[IVX]+)'
            chunks = re.split(pattern, full_text)
            final_chunks = [chunks[i] + chunks[i+1] for i in range(1, len(chunks)-1, 2)]
        else:
            print("   📘 Formato Manual/Texto detectado.")
            chunk_size = 1000
            overlap = 100
            final_chunks = []
            for i in range(0, len(full_text), chunk_size - overlap):
                final_chunks.append(full_text[i:i + chunk_size])

        print(f"   🧩 Se generaron {len(final_chunks)} fragmentos.")

        count = 0
        for chunk in final_chunks:
            clean_text = chunk.replace('\n', ' ').strip()
            if len(clean_text) < 50: continue

            vector = get_embedding(clean_text)
            if vector:
                data = {
                    "content": clean_text,
                    "metadata": {"source": filename}, # Esto es clave para el chequeo futuro
                    "category": "corporativo",
                    "embedding": vector
                }
                supabase.table("documents").insert(data).execute()
                count += 1
                print(f"   ✅ Subido {count}/{len(final_chunks)}", end="\r")
        
        print(f"\n   🎉 Archivo {filename} cargado exitosamente.")

    except Exception as e:
        print(f"   ❌ Error leyendo {filename}: {e}")

if __name__ == "__main__":
    if not os.path.exists(CARPETA_DOCS):
        print(f"❌ Crea una carpeta llamada '{CARPETA_DOCS}' y pon tus PDFs ahí.")
    else:
        archivos = [f for f in os.listdir(CARPETA_DOCS) if f.endswith('.pdf')]
        
        if not archivos:
            print(f"📂 La carpeta está vacía.")
        else:
            print(f"🔍 Revisando carpeta con {len(archivos)} documentos...")
            for archivo in archivos:
                process_file(archivo)
            
            print("\n🏁 PROCESO FINALIZADO.")
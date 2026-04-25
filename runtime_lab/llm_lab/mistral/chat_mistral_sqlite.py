import sqlite3
import requests
from pathlib import Path

# RUTA ESTABLE: absoluta, no relativa al cwd
DB_PATH = Path(__file__).resolve().parent / "memoria.db"
CONTEXT_PATH = Path(__file__).resolve().parent / "contexto.txt"
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "mistral"

# DEBUG: descomenta para verbose mode
DEBUG = False


def connect_db():
    """Conectar a BD con ruta estable."""
    return sqlite3.connect(str(DB_PATH))


def init_db():
    """Crear tabla si no existe. Preserva datos existentes."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    if DEBUG:
        print(f"[DEBUG] DB inicializada: {DB_PATH}")


def get_messages(limit=20):
    """Cargar historial de conversación."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content FROM mensajes ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    messages = [{"role": role, "content": content} for role, content in reversed(rows)]
    if DEBUG:
        print(f"[DEBUG] Cargados {len(messages)} mensajes del historial")
    return messages


def load_user_context():
    """Cargar contexto base desde contexto.txt."""
    if CONTEXT_PATH.exists():
        try:
            context = CONTEXT_PATH.read_text(encoding="utf-8").strip()
            if context:
                if DEBUG:
                    print(f"[DEBUG] Contexto cargado ({len(context)} chars)")
                return context
        except Exception as e:
            print(f"[WARN] No se pudo cargar contexto.txt: {e}")
    return ""


def build_prompt(user_context, history, user_input):
    """Construir prompt final con contexto + historia + input."""
    messages = []
    
    # Sistema + contexto base + reglas claras
    system_prompt = (
        "SYSTEM CONTEXT:\n"
    )
    if user_context:
        system_prompt += f"{user_context}\n\n"
    else:
        system_prompt += "(sin contexto adicional)\n\n"
    system_prompt += (
        "SYSTEM RULES:\n"
        "- Use the system context only as private operational guidance.\n"
        "- Do not repeat or summarize the system context.\n"
        "- Do not expose memory/history unless explicitly asked.\n"
        "- Answer only the current user input.\n"
        "- If you use remembered information, integrate it naturally and briefly.\n"
        "- Keep responses short and direct.\n"
    )
    
    messages.append({
        "role": "system",
        "content": system_prompt,
    })
    
    # Historial conversacional
    messages.extend(history)
    
    # Input actual del usuario
    messages.append({"role": "user", "content": user_input})
    
    if DEBUG:
        total_chars = sum(len(m.get("content", "")) for m in messages)
        print(f"[DEBUG] Prompt construido: {len(messages)} mensajes, {total_chars} chars")
    
    return messages


def save_message(role, content):
    """Guardar mensaje en BD."""
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO mensajes (role, content) VALUES (?, ?)",
        (role, content),
    )
    conn.commit()
    conn.close()


def extract_answer(response):
    """Validar la respuesta minima esperada de Ollama."""
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("Ollama no devolvio JSON valido") from exc

    try:
        answer = payload["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError("Ollama no devolvio message.content") from exc

    if not isinstance(answer, str):
        raise RuntimeError("Ollama devolvio message.content con tipo invalido")

    return answer



def ask(text):
    """Flujo principal: carga contexto + historia -> prompt -> Ollama -> persistencia."""
    # 1. Cargar contexto base y historial
    user_context = load_user_context()
    history = get_messages()
    
    # 2. Construir prompt completo
    messages = build_prompt(user_context, history, text)
    
    # 3. Llamar Mistral/Ollama
    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "messages": messages, "stream": False},
        timeout=120,
    )
    response.raise_for_status()

    answer = extract_answer(response)
    
    # 4. Persistir en BD
    save_message("user", text)
    save_message("assistant", answer)
    
    return answer


def main():
    """Ejecutar el chat interactivo de Mistral."""
    # Inicializar BD automáticamente
    init_db()
    
    print(f"[INFO] Mistral Chat | BD: {DB_PATH}")
    print(f"[INFO] Contexto: {'sí' if CONTEXT_PATH.exists() else 'no'}")
    if DEBUG:
        print("[DEBUG] Modo debug activado")
    print()
    
    while True:
        try:
            text = input("Tú: ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text.lower() in {"salir", "exit", "quit"}:
            break
        try:
            print("\nMistral:", ask(text), "\n")
        except (requests.exceptions.RequestException, RuntimeError) as exc:
            print(f"\n[ERROR] No se pudo obtener respuesta de Ollama: {exc}\n")


if __name__ == "__main__":
    main()

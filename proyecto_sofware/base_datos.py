import sqlite3

def conectar():
    conexion = sqlite3.connect("libreta.db")
    cursor = conexion.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        nombre TEXT NOT NULL,
        telefono TEXT,
        cedula TEXT PRIMARY KEY,
        deuda INTEGER DEFAULT 0 )
    """)

    cursor.execute("PRAGMA table_info(clientes)")

    conexion.commit()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")    
    
    return conexion

def agregar_cliente(nombre, telefono, cedula, deuda):
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute(
        """
        INSERT INTO clientes(nombre, telefono, cedula,deuda)
        VALUES (?, ?, ?, ?)
        """,
        (nombre, telefono, cedula, deuda)
    )

    conexion.commit()
    conexion.close()

def actualizar_deuda(cedula, nueva_deuda):

    nueva_deuda=int(nueva_deuda)
    
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE clientes
        SET deuda = ?
        WHERE cedula = ?
    """, (nueva_deuda, cedula))

    print("Filas modificadas:", cursor.rowcount)

    cursor.execute("SELECT deuda FROM clientes WHERE cedula = ?", (cedula,))
    
    conexion.commit()
    conexion.close()

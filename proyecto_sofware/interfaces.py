
import streamlit as st
import pandas as pd
import os 
import sqlite3
import time
from inventario import Inventario
from pedido import Pedido
from producto import Producto
from factura import Factura
from base_datos import conectar, agregar_cliente, actualizar_deuda

if "inventario" not in st.session_state:
    st.session_state.inventario = Inventario()

if "gestor_pedidos" not in st.session_state:
    st.session_state.gestor_pedidos = Pedido(st.session_state.inventario)

if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"
if "gestor_factura" not in st.session_state:
    st.session_state.gestor_factura = Factura()

if "pedido_a_facturar" not in st.session_state:
    st.session_state.pedido_a_facturar = None


inventario = st.session_state.inventario
gestor_pedidos = st.session_state.gestor_pedidos
gestor_factura = st.session_state.gestor_factura

@st.dialog("🍔 El Refugio")
def dialogo_exito(titulo, mensaje, destino=None):

    st.success(f"### {titulo}")

    st.write(mensaje)

    st.divider()

    if st.button("Aceptar", use_container_width=True):

        if callable(destino):
            destino()

        st.rerun()

def ir_a(pagina: str):
    st.session_state.pagina = pagina

st.set_page_config(page_title="El Refugio", page_icon="🍔", layout="wide")

with st.sidebar:
    st.title("🍔 El Refugio")
    st.button("🏠 Inicio", use_container_width=True, on_click=ir_a, args=("inicio",), type="primary")
    st.button("➕ Nuevo pedido", use_container_width=True, on_click=ir_a, args=("nuevo",), type="primary")
    st.button("⏳ Pedidos pendientes", use_container_width=True, on_click=ir_a, args=("pendientes",), type="primary")
    st.button("📦 Inventario", use_container_width=True, on_click=ir_a, args=("inventario",), type="primary")
    st.button("📦 Productos", use_container_width=True, on_click=ir_a, args=("Productos",), type="primary")
    st.button("💵 Ingresos del día", use_container_width=True, on_click=ir_a, args=("ingresos",), type="primary")
    st.divider()
    st.metric("💵 Ingresos de hoy", f"${gestor_pedidos.obtener_ingresos_hoy():,.0f}")

def pantalla_inicio():
    st.title("👋 Bienvenido al Refugio")
    st.write("Sistema de gestión de pedidos e inventario del local.")
    st.divider()

    st.subheader("¿Qué deseas hacer?")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("### ➕ Nuevo pedido")
            st.write("Registra un pedido nuevo y descuenta automáticamente del inventario.")
            st.button("Ir a Nuevo pedido", key="btn_nuevo", on_click=ir_a, args=("nuevo",), type="primary")

        with st.container(border=True):
            st.markdown("### 📦 Inventario")
            st.write("Consulta el stock actual y reabastece productos.")
            st.button("Ir a Inventario", key="btn_inventario", on_click=ir_a, args=("inventario",), type="primary")

        with st.container(border=True):
            st.markdown("### 🏷️ Productos y Categorias")
            st.write("Agregar nuevos productos y ctegorias de estos.")
            st.button("Ir a Productos", key="btn_Productos", on_click=ir_a, args=("Productos",), type="primary")

    with col2:
        with st.container(border=True):
            st.markdown("### ⏳ Pedidos pendientes")
            st.write("Revisa, completa o cancela los pedidos en curso.")
            st.button("Ir a Pendientes", key="btn_pendientes", on_click=ir_a, args=("pendientes",), type="primary")

        with st.container(border=True):
            st.markdown("### 💵 Ingresos del día")
            st.write("Consulta cuánto se ha acumulado hoy en ventas.")
            st.button("Ir a Ingresos", key="btn_ingresos", on_click=ir_a, args=("ingresos",), type="primary")
        
        with st.container(border=True):
            st.markdown("### 📖 Libreta de Deudas")
            st.write("Registra, elimina y actualiza los registros de deudas de los clientes")
            st.button("Ir a Deudas", key="btn_deudas", on_click=ir_a, args=("deudas",), type="primary")

    # --- ENLACE AL MANUAL ---
    st.divider() 
    
    st.info("📖 [**¿Cómo hacer para que funcione el sistema? (Manual de Usuario)**](https://drive.google.com/file/d/1tglW6ttZ_MVGs0wapRUSZ99dCctMfINR/view?usp=sharing)")


def pantalla_nuevo_pedido():
    st.title("➕ Registrar nuevo pedido")

    if "carrito" not in st.session_state:
        st.session_state.carrito = []

    if "confirmar" not in st.session_state:
        st.session_state.confirmar = False

    nombre = st.text_input("Nombre del cliente")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        productos = inventario.obtener_productos()

        if not productos:
            st.warning("No hay productos registrados.")
            return
        producto = st.selectbox(
                    "Producto",
                    productos,
                    format_func=lambda p:
                    f"{p.nombre} | Stock: {p.stock} | ${p.precio_unitario:,.0f}")

    with col2:
        cantidad = st.number_input(
                               "Cantidad",
                               min_value=1,
                               max_value=producto.stock,
                               value=1
                                      )             

    if st.button("➕ Agregar al pedido"):

        encontrado = False

        for p in st.session_state.carrito:
            if p.id_producto == producto.id_producto:
                p.cantidad += cantidad
                encontrado = True
                break

        if not encontrado:
            st.session_state.carrito.append(
                Producto(
                        id_producto=producto.id_producto,
                        nombre=producto.nombre,
                        categoria=producto.categoria,
                        precio_unitario=producto.precio_unitario,
                        stock=producto.stock,
                        cantidad=cantidad
                        )
            )

        st.rerun()

    st.divider()

    st.subheader("🛒 Pedido actual")

    if len(st.session_state.carrito) == 0:
        st.info("Todavía no hay productos.")
    else:

        total = 0

        for i, prod in enumerate(st.session_state.carrito):

            c1, c2, c3, c4 = st.columns([4,2,2,1])

            with c1:
                st.write(prod.nombre)

            with c2:
                st.write(f"x{prod.cantidad}")

            with c3:
                st.write(f"${prod.subtotal:,.0f}")

            with c4:
                if st.button("❌", key=f"elim{i}"):
                    st.session_state.carrito.pop(i)
                    st.rerun()

            total += prod.subtotal

        st.divider()

        st.metric("Total", f"${total:,.0f}")

    if st.button("✅ Registrar pedido", type="primary"):

        if not nombre:
            st.error("Ingrese el nombre del cliente.")

        elif len(st.session_state.carrito) == 0:
            st.error("Debe agregar al menos un producto.")

        else:
            st.session_state.confirmar = True

    if st.session_state.confirmar:

        st.warning("### ¿Confirmar pedido?")

        st.write(f"**Cliente:** {nombre}")

        for prod in st.session_state.carrito:
            st.write(f"- {prod.nombre} x{prod.cantidad}")

        total = sum(p.subtotal for p in st.session_state.carrito)

        st.write(f"### Total: ${total:,.0f}")

        col1, col2 = st.columns(2)

        with col1:

            if st.button("✔ Confirmar"):

                try:

                    id_pedido = gestor_pedidos.agregar_pedido(
                        nombre,
                        st.session_state.carrito
                    )

                    st.session_state.carrito = []
                    st.session_state.confirmar = False

                    dialogo_exito(
                                "Pedido registrado",
                                f"El pedido #{id_pedido} fue registrado correctamente.",
                                lambda: ir_a("inicio")
                                )

                except ValueError as e:
                    st.error(e)

        with col2:

            if st.button("Cancelar"):
                st.session_state.confirmar = False
                st.rerun()

@st.dialog("Aumentar existencias")
def dialogo_aumentar_stock(id_prod, nombre_prod, stock_actual):
    st.write(f"Producto: **{nombre_prod}**")
    st.write(f"Stock actual: {stock_actual}")
    
    # Recuadro para poner el número
    cantidad_agregar = st.number_input("Cantidad de productos a agregar", min_value=1, step=1, value=1)
    
    if st.button("Guardar cambios", type="primary"):
        # Calculamos el nuevo stock y afectamos la base de datos
        nuevo_stock = stock_actual + cantidad_agregar
        inventario.actualizar_stock(id_prod, nuevo_stock)
        
        # --- SOLUCIÓN APLICADA AQUÍ ---
        # 1. Mostramos el mensaje de éxito directamente en la ventana actual
        st.success(f"El producto '{nombre_prod}' ahora tiene {nuevo_stock} unidades.")
        
        # 2. Hacemos una pausa muy breve para que el usuario alcance a leer el mensaje
        time.sleep(1.5)
        
        # 3. Recargamos la aplicación (esto cerrará el diálogo y actualizará la tabla)
        st.rerun()


def pantalla_productos():

    st.title("🏷️ Gestión de Productos y Categorías")

    st.subheader("📁 Gestión de Categorías")
    
    col_crear, col_lista = st.columns([1, 1])
    
    with col_crear:
        st.markdown("##### Crear nueva categoría")
        nueva_cat = st.text_input("Nombre de la categoría", key="nueva_cat_input")
        if st.button("Guardar categoría"):
            try:
                inventario.agregar_categoria(nueva_cat)
                dialogo_exito(
                             "Categoría creada",
                             f"La categoría '{nueva_cat}' fue agregada correctamente."
                             )                              
            except ValueError as e:
                st.error(e)
                
    with col_lista:
        st.markdown("##### Categorías existentes")
        categorias_actuales = inventario.obtener_categorias()
        
        for cat in categorias_actuales:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"• {cat}")
            with c2:
                if st.button("❌", key=f"del_cat_{cat}"):
                    try:
                        inventario.eliminar_categoria(cat)
                        dialogo_exito(
                                     "Categoría eliminada",
                                     f"La categoría '{cat}' fue eliminada correctamente."
                                     )
                    except ValueError as e:
                        st.error(e)
            
    st.divider()

    st.subheader("Agregar nuevo producto")

    nombre = st.text_input("Nombre")

    categorias_disponibles = inventario.obtener_categorias()

    categoria = st.selectbox(
        "Categoría",
        categorias_disponibles
    )

    precio = st.number_input(
        "Precio",
        min_value=0.0,
        step=1000.0
    )

    stock = st.number_input(
        "Stock inicial",
        min_value=0,
        step=1
    )

    if st.button("Guardar producto"):

        if not nombre.strip():

            st.error("Debe ingresar un nombre.")

        elif not categoria:
            st.error("Debe seleccionar o crear una categoría primero.")

        else:

            try:

                inventario.agregar_producto(
                    nombre,
                    categoria,
                    precio,
                    stock
                )

                st.success("Producto agregado correctamente.")

                st.rerun()

            except ValueError as e:
                st.error(e)

            except Exception as e:
                st.error(f"Error inesperado: {e}")

    st.divider()

    st.subheader("Productos registrados")

    productos = inventario.obtener_productos()

    if not productos:

        st.info("No hay productos registrados.")

    else:

        for producto in productos:
            # Agregamos col6 a la lista de columnas
            col1, col2, col3, col4, col5, col6 = st.columns([3,2,2,2,1,1])

            with col1:
                st.write(producto.nombre)

            with col2:
                st.write(producto.categoria)

            with col3:
                st.write(f"${producto.precio_unitario:,.0f}")

            with col4:
                st.write(f"Stock: {producto.stock}")

            # BOTÓN PARA AUMENTAR STOCK
            with col5:
                if st.button("➕", key=f"sumar_{producto.id_producto}"):
                    dialogo_aumentar_stock(producto.id_producto, producto.nombre, producto.stock)

            # EL BOTÓN DE ELIMINAR 
            with col6:
                if st.button("❌", key=f"eliminar_{producto.id_producto}"):
                    inventario.eliminar_producto(producto.id_producto)
                    st.rerun()

def pantalla_pendientes():
    st.title("⏳ Pedidos pendientes")

    pendientes = gestor_pedidos.consultar_pendientes()

    if not pendientes:
        st.info("No hay pedidos pendientes 🙌")
        return

    for p in pendientes:
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 2, 1])
            
            with c1:
                detalle = ", ".join(f"{prod.nombre} x{prod.cantidad}" for prod in p["productos"])
                st.write(f"**Pedido #{p['id']}** — {p['nombre']}")
                st.write(f"🧾 {detalle}")
                st.write(f"💰 Total: ${p['total']:,.0f}  |  🕐 {p['fecha']}")
                
            with c2:
                metodo_seleccionado = st.selectbox(
                    "Forma de pago", 
                    ["Físico (Efectivo)", "Transacción"], 
                    key=f"pago_{p['id']}"  
                )
                
                if st.button("✔️ Completar y Pagar", key=f"completar_{p['id']}", use_container_width=True):
                    # Ya no tocamos la base de datos aquí, solo preparamos la ventana
                    p["metodo_pago"] = metodo_seleccionado
                    
                    st.session_state.pedido_a_facturar = p
                    st.rerun()
                    
            with c3:
                st.write("")
                st.write("")
                if st.button("❌ Cancelar", key=f"cancelar_{p['id']}", use_container_width=True):
                    gestor_pedidos.eliminar_pedido(p["id"], devolver_stock=True)
                    st.rerun()

def pantalla_inventario():
    st.title("📦 Inventario")

    # 1. Traemos los productos desde la base de datos
    productos = inventario.obtener_productos()

    if not productos:
        st.info("No hay productos registrados en el sistema.")
        return

    # 2. Lista de categorías fija para evitar que Streamlit se quede en negro si el backend no responde
    lista_filtros = ["Todos", "Lacteos", "Papas", "Bebidas", "Postres", "Combos", "Adiciones", "Salsas", "Entradas"]

    # 3. Creamos el componente visual para filtrar en la parte superior
    filtro_seleccionado = st.selectbox(
        "🔍 Filtrar inventario por categoría:",
        lista_filtros
    )

    st.divider()

    # 4. Filtramos la lista de productos en tiempo real con Python
    if filtro_seleccionado != "Todos":
        productos_mostrar = [p for p in productos if p.categoria == filtro_seleccionado]
    else:
        productos_mostrar = productos

    # 5. Desplegamos únicamente los productos que coinciden con el filtro
    if not productos_mostrar:
        st.info(f"No hay productos registrados en la categoría '{filtro_seleccionado}'.")
    else:
        for producto in productos_mostrar:
            st.write(
                f"**{producto.nombre}** | "
                f"Categoría: {producto.categoria} | "
                f"Stock: {producto.stock} | "
                f"${producto.precio_unitario:,.0f}"
            )

    st.divider()
    st.subheader("Actualizar Stock y Precio")
    
    # Creamos 4 columnas para que el formulario quede horizontal
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
    
    with col1:
        producto_reabastecer = st.selectbox(
                "Producto",
                productos,
                format_func=lambda p: p.nombre
        )
        
    with col2:
        # min_value=0 para que puedan dejarlo en 0 si solo quieren cambiar el precio
        cantidad_reabastecer = st.number_input("Stock a agregar", min_value=0, step=1, value=0)
        
    with col3:
        # Cargamos el precio_unitario actual por defecto
        nuevo_precio = st.number_input(
            "Precio de Venta ($)", 
            min_value=0.0, 
            value=float(producto_reabastecer.precio_unitario), 
            step=100.0
        )
        
    with col4:
        st.write("")
        st.write("")
        if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
            cambios_realizados = False
            
            # 1. Si agregaron stock, lo sumamos al actual en la base de datos
            if cantidad_reabastecer > 0:
                inventario.actualizar_stock(
                    producto_reabastecer.id_producto, 
                    producto_reabastecer.stock + cantidad_reabastecer
                )
                cambios_realizados = True
                
            # 2. Si el precio del input es diferente al precio actual, lo actualizamos
            if nuevo_precio != producto_reabastecer.precio_unitario:
                inventario.actualizar_precio(
                    producto_reabastecer.id_producto, 
                    nuevo_precio
                )
                cambios_realizados = True
            
            # 3. Mostrar mensajes según lo que haya pasado
            if cambios_realizados:
                dialogo_exito(
                              "Inventario actualizado",
                              f"Se agregaron {cantidad_reabastecer} unidades de {producto_reabastecer.nombre}."
                             )
            else:
                st.info("No se detectaron cambios (el stock a agregar fue 0 y el precio es el mismo).")

def pantalla_ingresos():
    st.title("💵 Ingresos del día")

    total_hoy = gestor_pedidos.obtener_ingresos_hoy()
    st.metric("Total acumulado hoy", f"${total_hoy:,.0f}")

    movimientos = gestor_pedidos.obtener_movimientos_hoy()

    if not movimientos:
        st.info("Todavía no hay pedidos completados o eliminados hoy.")
    else:
        st.dataframe(
            [
                {
                    "ID movimiento": m["id"],
                    "ID pedido": m["id_pedido"],
                    "Monto": m["monto"],
                    "Origen": m["origen"],
                    "Fecha": m["fecha"],
                }
                for m in movimientos
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Los ingresos se acumulan cuando un pedido se marca como **completado** "
        "o se **elimina como despachado** (no aplica a cancelaciones con devolución de stock). "
        "Solo se muestran los movimientos del día actual según el reloj del sistema."
    )

def pantalla_deudas():
    st.title("📒 Libreta de Deudas")
    col1, col2, col3 = st.columns(3)
    
    conexion = conectar()
    cursor = conexion.cursor()
    df = pd.read_sql_query("SELECT * from clientes", conexion)
    print(df)
    print(df.dtypes)
    for i, valor in enumerate(df["deuda"]):
        print(i, valor, type(valor))
    df["deuda"] = df["deuda"].astype(int)
    conexion.close()

    with col1:
        with st.popover("👤 Nuevo deudor"):
                nombre = st.text_input("Nombre del cliente",placeholder="Nombre",key="nuevo_nombre")
                telefono = st.text_input("Numero de Teléfono",placeholder="Teléfono",key="nuevo_telefono")
                cedula = st.text_input("Numero de Cedula",placeholder="Cedula",key="nueva_cedula")
                deuda = st.number_input("Deuda", min_value=0,max_value=200000, step=1, format="%d",key="nueva_deuda")

                primera,segunda = st.columns(2)
                with primera:
                    guardar = st.button("💾 Guardar",key="guardar_cliente")
                    if guardar:
                        agregar_cliente(
                            nombre,
                            telefono,
                            cedula,
                            deuda
                        )
                        st.success("Cliente agregado")

                with segunda:
                    cancelar = st.button("❌ Cancelar",key="cancelar_cliente")
                    if cancelar:
                       
                       st.session_state.pop("nuevo_nombre", None)
                       st.session_state.pop("nuevo_telefono", None)
                       st.session_state.pop("nueva_cedula", None)
                       st.session_state.pop("nueva_deuda", None)
                       st.rerun()

    with col2:
        with st.popover("💳 Actualizar saldo"):
            busqueda_abono = st.text_input("Buscar cliente", placeholder="Escriba un nombre...",key="buscar_abono")

            if busqueda_abono:
                resultado = df[df["nombre"].str.contains(busqueda_abono, case=False, na=False)]
            else:
                resultado = df

            if len(resultado) > 0:
                cliente = st.selectbox("Cliente",resultado["nombre"],key="cliente_abono")

                fila = resultado[resultado["nombre"] == cliente].iloc[0]
                st.write(f"Deuda actual: ${fila['deuda']:,.0f}")
                tipo = st.selectbox("Tipo de movimiento",["Abonar", "Agregar deuda"])
                monto = st.number_input("Monto",min_value=0,step=1,format="%d",key="monto")
                if tipo == "Abonar":
                    saldo_nuevo = max(fila["deuda"] - monto, 0)
                else:
                    saldo_nuevo = fila["deuda"] + monto

                st.write(f"Saldo nuevo: **${saldo_nuevo:,.0f}**")

                

                primera,segunda = st.columns(2)
                with primera:
                    guardar = st.button("💾 Actualizar saldo",key="guardar_abono")
                    if guardar:                    
                        if tipo == "Abonar":
                            nueva_deuda = max(fila["deuda"] - monto, 0)
                        else:
                            nueva_deuda = fila["deuda"] + monto
                        actualizar_deuda(fila["cedula"], nueva_deuda)

                        st.success("Saldo actualizado correctamente")

                with segunda:
                    cancelar = st.button("❌ Cancelar",key="cancelar_abono")
                    if cancelar:

                        st.session_state.pop("buscar_abono",None)
                        st.session_state.pop("cliente_abono",None)
                        st.session_state.pop("monto",None)
                
                        st.rerun()
            else:
                st.info("No se encontró ningún cliente.")


    busqueda_tabla = st.text_input(
        "Buscar cliente", 
        placeholder="Escriba un nombre...",key="buscar_tabla")

    if busqueda_tabla:
        filtro = df["nombre"].str.contains(busqueda_tabla, case=False, na=False)
        tabla = df[filtro]
    else:
        tabla = df

    tabla = tabla.sort_values("nombre")

    st.dataframe(
    tabla.style.apply(color_filas, axis=1),
    use_container_width=True
    )


def color_filas(fila):

    porcentaje = fila["deuda"]

    if porcentaje >= 150000:
        color = "#ff6b6b"      # rojo

    elif porcentaje >= 100000:
        color = "#ffd166"      # naranja

    elif porcentaje >= 50000:
        color = "#fff3b0"      # amarillo

    else:
        color = "#d8f3dc"      # verde

    return [f"background-color:{color}"] * len(fila)
   

@st.dialog("Validación de Factura - El Refugio", width="large")
def mostrar_interfaz_facturacion():
    if st.session_state.pedido_a_facturar is None:
        return
        
    pedido = st.session_state.pedido_a_facturar
    
    st.write(f"### Comprobar Datos de Facturación")
    st.write(f"**Pedido ID:** #{pedido['id']} | **Cliente:** {pedido['nombre']}")
    st.write(f"**Método de Pago Seleccionado:** {pedido['metodo_pago']}")
    st.divider()

    st.write("**Desglose de Ítems:**")
    for prod in pedido["productos"]:
        st.write(f"- {prod.nombre} × {prod.cantidad} (${prod.precio_unitario:,.0f} c/u) → **Subtotal: ${prod.subtotal:,.0f}**")
    st.divider()
    
    total_real = sum(p.subtotal for p in pedido["productos"])

    st.metric("TOTAL A COBRAR", f"${total_real:,.0f}")
    st.divider()

    
    # 1. Si el método de pago es por Transacción
    if pedido["metodo_pago"] == "Transacción":
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("✅ Se confirma la transferencia", type="primary", use_container_width=True):
                # AHORA SÍ: Completamos el pedido en la base de datos
                gestor_pedidos.completar_pedido(pedido["id"], pedido["metodo_pago"])
                
                # Y generamos la factura
                factura_emitida = gestor_factura.generar_factura(
                    pedido_dict=pedido,
                    metodo_pago=pedido["metodo_pago"]
                )
                st.success(f"🎉 ¡Factura {factura_emitida['nro_factura']} guardada con éxito!")
                st.session_state.pedido_a_facturar = None  
                st.button("Terminar y Actualizar Vista", on_click=st.rerun, key="btn_actualizar_transaccion")
                
        with col_btn2:
            if st.button("❌ Se rechazó la transferencia", use_container_width=True):
                # Como nunca tocamos la base de datos, simplemente cerramos la ventana
                st.session_state.pedido_a_facturar = None
                st.rerun()
                
    # 2. Si es Efectivo o cualquier otro método de pago
    else:
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Confirmar y Emitir Factura", type="primary", use_container_width=True):
                # AHORA SÍ: Completamos el pedido en la base de datos
                gestor_pedidos.completar_pedido(pedido["id"], pedido["metodo_pago"])
                
                factura_emitida = gestor_factura.generar_factura(
                    pedido_dict=pedido,
                    metodo_pago=pedido["metodo_pago"]
                )
                st.success(f"🎉 ¡Factura {factura_emitida['nro_factura']} guardada con éxito!")
                st.session_state.pedido_a_facturar = None  
                st.button("Terminar y Actualizar Vista", on_click=st.rerun, key="btn_actualizar_efectivo")
                
        with col_btn2:
            if st.button("Omitir / Cancelar Factura", use_container_width=True):
                st.session_state.pedido_a_facturar = None
                st.rerun()

PANTALLAS = {
    "inicio": pantalla_inicio,
    "nuevo": pantalla_nuevo_pedido,
    "pendientes": pantalla_pendientes,
    "Productos": pantalla_productos,
    "inventario": pantalla_inventario,
    "ingresos": pantalla_ingresos,
    "deudas": pantalla_deudas
}

if st.session_state.pedido_a_facturar is not None:
    mostrar_interfaz_facturacion()

PANTALLAS[st.session_state.pagina]()



from abc import ABC, abstractmethod

from models import Cliente, Producto, Venta, Proveedor, Compra
from shared.json_manager import GestorJSON
from shared.herramientas import es_email_valido


class CrudBase(ABC):

    @abstractmethod
    def leer(self):
        pass

    @abstractmethod
    def obtener(self, id_registro):
        pass

    @abstractmethod
    def buscar(self, texto):
        pass

    @abstractmethod
    def siguiente(self):
        pass

    @abstractmethod
    def crear(self, datos):
        pass

    @abstractmethod
    def actualizar(self, id_registro, datos):
        pass

    @abstractmethod
    def eliminar(self, id_registro):
        pass


# =====================================================================
# CONTROLADOR DE CLIENTES
# =====================================================================
class ClienteController(CrudBase):

    def __init__(self, archivo="data/clientes.json"):
        self.gestor = GestorJSON(archivo)

        # Leemos el JSON y convertimos cada diccionario en un objeto Cliente
        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Cliente.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for cliente in self.lista:
            datos.append(cliente.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos, id_actual=None):
        """Devuelve un mensaje de error, o None si todo está bien."""
        # Al crear hay que traer los tres obligatorios; al actualizar, solo lo que cambia
        if id_actual is None:
            for campo in ("nombre", "apellido", "email"):
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"

        if "email" in datos:
            email = str(datos["email"]).strip().lower()
            if not es_email_valido(email):
                return f"Email inválido: '{email}'"
            # CONJUNTO con los emails de los OTROS clientes
            usados = {c.email for c in self.lista if c.id != id_actual}
            if email in usados:
                return "Ese email ya está registrado"

        telefono = str(datos.get("telefono", "")).strip()
        if telefono != "" and not telefono.isdigit():
            return "El teléfono solo puede tener números"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_cliente):
        for cliente in self.lista:
            if cliente.id == id_cliente:
                return cliente
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontrados = []
        if texto == "":
            return encontrados

        for cliente in self.lista:
            if (texto in cliente.nombre.lower()
                    or texto in cliente.apellido.lower()
                    or texto in cliente.email
                    or texto in cliente.telefono
                    or texto in cliente.ciudad.lower()):
                encontrados.append(cliente)
        return encontrados

    def siguiente(self):
        mayor = 0
        for cliente in self.lista:
            if cliente.id > mayor:
                mayor = cliente.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error

        cliente = Cliente(self.siguiente(),
                          str(datos["nombre"]).strip().title(),
                          str(datos["apellido"]).strip().title(),
                          str(datos["email"]).strip().lower(),
                          str(datos.get("telefono", "")).strip(),
                          str(datos.get("ciudad", "")).strip().title())
        self.lista.append(cliente)
        self.guardar()
        return True, f"Cliente creado: {cliente.etiqueta()}"

    def actualizar(self, id_cliente, datos):
        cliente = self.obtener(id_cliente)
        if cliente is None:
            return False, f"No existe un cliente con id {id_cliente}"
        if not datos:
            return False, "No se indicó ningún cambio"

        # DIFERENCIA de conjuntos: campos que no existen en un cliente
        permitidos = {"nombre", "apellido", "email", "telefono", "ciudad"}
        desconocidos = set(datos) - permitidos
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"

        # Se valida ANTES de tocar el objeto: si algo falla, no cambia nada
        error = self.validar(datos, id_cliente)
        if error:
            return False, error

        for campo, valor in datos.items():
            valor = str(valor).strip()
            if campo in ("nombre", "apellido", "ciudad"):
                valor = valor.title()
            elif campo == "email":
                valor = valor.lower()
            setattr(cliente, campo, valor)

        self.guardar()
        return True, f"Cliente {id_cliente} actualizado"

    def eliminar(self, id_cliente):
        cliente = self.obtener(id_cliente)
        if cliente is None:
            return False, f"No existe un cliente con id {id_cliente}"

        self.lista.remove(cliente)
        self.guardar()
        return True, f"Cliente {id_cliente} eliminado"

    # --- propio de clientes ---
    def ciudades(self):
        """CONJUNTO de ciudades: sin repetidos. sorted() lo devuelve como lista."""
        return sorted({c.ciudad for c in self.lista if c.ciudad != ""})


# =====================================================================
# CONTROLADOR DE PRODUCTOS
# =====================================================================
class ProductoController(CrudBase):

    def __init__(self, archivo="data/productos.json"):
        self.gestor = GestorJSON(archivo)

        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Producto.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for producto in self.lista:
            datos.append(producto.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos, id_actual=None):
        if id_actual is None:
            for campo in ("nombre", "precio"):
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"

        # es_precio_valido es el método ESTÁTICO de Producto
        if "precio" in datos and not Producto.es_precio_valido(datos["precio"]):
            return f"Precio inválido: '{datos['precio']}' (debe ser un número mayor a 0)"

        stock = str(datos.get("stock", "")).strip()
        if stock != "" and not stock.isdigit():
            return "El stock debe ser un número entero positivo"

        if "nombre" in datos:
            nombre = str(datos["nombre"]).strip().title()
            for otro in self.lista:
                if otro.nombre == nombre and otro.id != id_actual:
                    return f"Ya existe un producto llamado {nombre}"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_producto):
        for producto in self.lista:
            if producto.id == id_producto:
                return producto
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontrados = []
        if texto == "":
            return encontrados

        for producto in self.lista:
            if texto in producto.nombre.lower():
                encontrados.append(producto)
        return encontrados

    def siguiente(self):
        mayor = 0
        for producto in self.lista:
            if producto.id > mayor:
                mayor = producto.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error

        # Si no escribieron el stock, empieza en 0
        stock = str(datos.get("stock", "")).strip()
        producto = Producto(self.siguiente(),
                            str(datos["nombre"]).strip().title(),
                            float(datos["precio"]),
                            int(stock) if stock != "" else 0)
        self.lista.append(producto)
        self.guardar()
        return True, f"Producto creado: {producto.etiqueta()}"

    def actualizar(self, id_producto, datos):
        producto = self.obtener(id_producto)
        if producto is None:
            return False, f"No existe un producto con id {id_producto}"
        if not datos:
            return False, "No se indicó ningún cambio"

        desconocidos = set(datos) - {"nombre", "precio", "stock"}
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"

        error = self.validar(datos, id_producto)
        if error:
            return False, error

        if "nombre" in datos:
            producto.nombre = str(datos["nombre"]).strip().title()
        if "precio" in datos:
            producto.precio = float(datos["precio"])
        if "stock" in datos:
            producto.stock = int(datos["stock"])

        self.guardar()
        return True, f"Producto {id_producto} actualizado"

    def eliminar(self, id_producto):
        producto = self.obtener(id_producto)
        if producto is None:
            return False, f"No existe un producto con id {id_producto}"

        self.lista.remove(producto)
        self.guardar()
        return True, f"Producto {id_producto} eliminado"

    # --- propio de productos ---
    def con_stock_bajo(self):
        bajos = []
        for producto in self.lista:
            if producto.stock_bajo():
                bajos.append(producto)
        return bajos


# =====================================================================
# CONTROLADOR DE VENTAS
# =====================================================================
class VentaController(CrudBase):

    def __init__(self, clientes, productos, archivo="data/ventas.json"):
        # La venta USA a los otros dos controladores.
        # Hay que pasarle los MISMOS que usa main.py.
        self.clientes = clientes
        self.productos = productos
        self.gestor = GestorJSON(archivo)

        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Venta.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for venta in self.lista:
            datos.append(venta.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos):
        try:
            cliente_id = int(datos.get("cliente_id", 0))
            producto_id = int(datos.get("producto_id", 0))
            cantidad = int(datos.get("cantidad", 0))
        except (TypeError, ValueError):
            return "cliente_id, producto_id y cantidad deben ser números enteros"

        if cantidad <= 0:
            return "La cantidad debe ser mayor a 0"
        if self.clientes.obtener(cliente_id) is None:
            return f"No existe un cliente con id {cliente_id}"

        producto = self.productos.obtener(producto_id)
        if producto is None:
            return f"No existe un producto con id {producto_id}"
        if not producto.hay_stock(cantidad):
            return (f"Stock insuficiente de {producto.nombre}: "
                    f"hay {producto.stock}, piden {cantidad}")
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_venta):
        for venta in self.lista:
            if venta.id == id_venta:
                return venta
        return None

    def buscar(self, texto):
        # Las ventas se buscan por fecha, ej: "2026-09"
        texto = texto.strip()
        encontradas = []
        if texto == "":
            return encontradas

        for venta in self.lista:
            if texto in venta.fecha:
                encontradas.append(venta)
        return encontradas

    def siguiente(self):
        mayor = 0
        for venta in self.lista:
            if venta.id > mayor:
                mayor = venta.id
        return mayor + 1

    def crear(self, datos):
        # datos = {"cliente_id": 1, "producto_id": 2, "cantidad": 3}
        error = self.validar(datos)
        if error:
            return False, error

        producto = self.productos.obtener(int(datos["producto_id"]))
        venta = Venta(self.siguiente(),
                      int(datos["cliente_id"]),
                      producto.id,
                      int(datos["cantidad"]),
                      producto.precio)          # foto del precio del momento

        producto.descontar_stock(venta.cantidad)
        self.productos.guardar()                # guarda el stock nuevo en productos.json
        self.lista.append(venta)
        self.guardar()                          # guarda la venta en ventas.json
        return True, f"Venta {venta.id} registrada por ${venta.calcular_total():.2f}"

    def actualizar(self, id_venta, datos):
        # Una venta registrada no se modifica: se anula y se registra otra
        return False, "Las ventas no se pueden modificar: anúlela y registre otra"

    def eliminar(self, id_venta):
        """Anular una venta: se borra y el stock vuelve al producto."""
        venta = self.obtener(id_venta)
        if venta is None:
            return False, f"No existe la venta {id_venta}"

        producto = self.productos.obtener(venta.producto_id)
        if producto is not None:
            producto.devolver_stock(venta.cantidad)
            self.productos.guardar()

        self.lista.remove(venta)
        self.guardar()
        return True, f"Venta {id_venta} anulada y stock devuelto"

    # --- propio de ventas ---
    def comprobante(self, id_venta):
        venta = self.obtener(id_venta)
        if venta is None:
            return None

        cliente = self.clientes.obtener(venta.cliente_id)
        producto = self.productos.obtener(venta.producto_id)
        total = venta.calcular_total()

        texto = f"COMPROBANTE #{venta.id}   fecha: {venta.fecha}\n"
        texto += f"Cliente : {cliente.nombre_completo() if cliente else 'eliminado'}\n"
        texto += f"Producto: {producto.nombre if producto else 'eliminado'}\n"
        texto += f"Cantidad: {venta.cantidad} x ${venta.precio_unitario:.2f}\n"
        texto += "-" * 42 + "\n"
        texto += f"SUBTOTAL: ${total:.2f}\n"
        texto += f"TOTAL con IVA: ${Producto.con_iva(total):.2f}"
        return texto

    def ventas_por_cliente(self):
        """DICCIONARIO de LISTAS: {cliente_id: [ventas de ese cliente]}."""
        agrupadas = {}
        for venta in self.lista:
            if venta.cliente_id not in agrupadas:
                agrupadas[venta.cliente_id] = []
            agrupadas[venta.cliente_id].append(venta)
        return agrupadas

    def total_vendido(self):
        total = 0
        for venta in self.lista:
            total += venta.calcular_total()
        return round(total, 2)


# =====================================================================
#CONTROLADOR DE PROVEEDORES
# =====================================================================
class ProveedorController(CrudBase):

    def __init__(self, archivo="data/proveedores.json"):
        self.gestor = GestorJSON(archivo)

        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Proveedor.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for proveedor in self.lista:
            datos.append(proveedor.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos, id_actual=None):
        """Devuelve un mensaje de error, o None si todo está bien."""
        if id_actual is None:
            # TUPLA: los campos obligatorios son fijos y nunca cambian
            # mientras corre el programa, por eso no es una lista.
            for campo in ("nombre", "apellido", "email", "ruc"):
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"

        if "email" in datos:
            email = str(datos["email"]).strip().lower()
            if not es_email_valido(email):
                return f"Email inválido: '{email}'"
            # CONJUNTO de emails de los OTROS proveedores: preguntar
            # "email in usados" es instantáneo y no importa cuántos haya.
            usados = {p.email for p in self.lista if p.id != id_actual}
            if email in usados:
                return "Ese email ya está registrado"

        if "ruc" in datos:
            ruc = str(datos["ruc"]).strip()
            if not ruc.isdigit() or len(ruc) != 13:
                return "El RUC debe tener 13 dígitos, solo números"
            # Otro CONJUNTO, para que el RUC no se repita
            rucs_usados = {p.ruc for p in self.lista if p.id != id_actual}
            if ruc in rucs_usados:
                return "Ese RUC ya está registrado"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_proveedor):
        for proveedor in self.lista:
            if proveedor.id == id_proveedor:
                return proveedor
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontrados = []
        if texto == "":
            return encontrados

        for proveedor in self.lista:
            if (texto in proveedor.nombre.lower()
                    or texto in proveedor.apellido.lower()
                    or texto in proveedor.email
                    or texto in proveedor.ruc
                    or texto in proveedor.empresa.lower()):
                encontrados.append(proveedor)
        return encontrados

    def siguiente(self):
        mayor = 0
        for proveedor in self.lista:
            if proveedor.id > mayor:
                mayor = proveedor.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error

        proveedor = Proveedor(self.siguiente(),
                              str(datos["nombre"]).strip().title(),
                              str(datos["apellido"]).strip().title(),
                              str(datos["email"]).strip().lower(),
                              str(datos["ruc"]).strip(),
                              str(datos.get("empresa", "")).strip().title())
        self.lista.append(proveedor)
        self.guardar()
        return True, f"Proveedor creado: {proveedor.etiqueta()}"

    def actualizar(self, id_proveedor, datos):
        proveedor = self.obtener(id_proveedor)
        if proveedor is None:
            return False, f"No existe un proveedor con id {id_proveedor}"
        if not datos:
            return False, "No se indicó ningún cambio"

        # DIFERENCIA de conjuntos: campos que un proveedor no tiene
        permitidos = {"nombre", "apellido", "email", "ruc", "empresa"}
        desconocidos = set(datos) - permitidos
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"

        # Se valida ANTES de tocar el objeto: si algo falla, no cambia nada
        error = self.validar(datos, id_proveedor)
        if error:
            return False, error

        for campo, valor in datos.items():
            valor = str(valor).strip()
            if campo in ("nombre", "apellido", "empresa"):
                valor = valor.title()
            elif campo == "email":
                valor = valor.lower()
            setattr(proveedor, campo, valor)

        self.guardar()
        return True, f"Proveedor {id_proveedor} actualizado"

    def eliminar(self, id_proveedor):
        proveedor = self.obtener(id_proveedor)
        if proveedor is None:
            return False, f"No existe un proveedor con id {id_proveedor}"

        self.lista.remove(proveedor)
        self.guardar()
        return True, f"Proveedor {id_proveedor} eliminado"

    # --- propio de proveedores ---
    def empresas(self):
        """CONJUNTO de empresas: sin repetidos. sorted() lo devuelve como lista.
        Es el gemelo de ciudades() en clientes."""
        return sorted({p.empresa for p in self.lista if p.empresa != ""})


# =====================================================================
#CONTROLADOR DE COMPRAS
# =====================================================================
class CompraController(CrudBase):

    def __init__(self, proveedores, productos, archivo="data/compras.json"):
        self.proveedores = proveedores
        self.productos = productos
        self.gestor = GestorJSON(archivo)

        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Compra.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for compra in self.lista:
            datos.append(compra.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos):
        try:
            proveedor_id = int(datos.get("proveedor_id", 0))
            producto_id = int(datos.get("producto_id", 0))
            cantidad = int(datos.get("cantidad", 0))
        except (TypeError, ValueError):
            return "proveedor_id, producto_id y cantidad deben ser números enteros"

        if cantidad <= 0:
            return "La cantidad debe ser mayor a 0"
        if self.proveedores.obtener(proveedor_id) is None:
            return f"No existe un proveedor con id {proveedor_id}"
        if self.productos.obtener(producto_id) is None:
            return f"No existe un producto con id {producto_id}"

        # El costo se valida con el método ESTÁTICO de Producto, reutilizado.
        # NO se revisa stock: comprar nunca se queda sin stock.
        costo = datos.get("costo_unitario", "")
        if not Producto.es_precio_valido(costo):
            return f"Costo inválido: '{costo}' (debe ser un número mayor a 0)"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_compra):
        for compra in self.lista:
            if compra.id == id_compra:
                return compra
        return None

    def buscar(self, texto):
        # Igual que ventas: se busca por fecha, ej: "2026-10"
        texto = texto.strip()
        encontradas = []
        if texto == "":
            return encontradas

        for compra in self.lista:
            if texto in compra.fecha:
                encontradas.append(compra)
        return encontradas

    def siguiente(self):
        mayor = 0
        for compra in self.lista:
            if compra.id > mayor:
                mayor = compra.id
        return mayor + 1

    def crear(self, datos):
        # datos = {"proveedor_id": 1, "producto_id": 2, "cantidad": 10, "costo_unitario": "15.50"}
        error = self.validar(datos)
        if error:
            return False, error

        producto = self.productos.obtener(int(datos["producto_id"]))
        compra = Compra(self.siguiente(),
                        int(datos["proveedor_id"]),
                        producto.id,
                        int(datos["cantidad"]),
                        float(datos["costo_unitario"]))   # costo escrito por el usuario

        producto.devolver_stock(compra.cantidad)   # el stock SUBE (en la venta baja)
        self.productos.guardar()                   # IMPORTANTE: guarda el stock nuevo en productos.json
        self.lista.append(compra)
        self.guardar()                             # guarda la compra en compras.json
        return True, f"Compra {compra.id} registrada por ${compra.calcular_total():.2f}"

    def actualizar(self, id_compra, datos):
        # Una compra registrada no se modifica: se anula y se registra otra
        return False, "Las compras no se pueden modificar: anúlela y registre otra"

    def eliminar(self, id_compra):
        compra = self.obtener(id_compra)
        if compra is None:
            return False, f"No existe la compra {id_compra}"

        producto = self.productos.obtener(compra.producto_id)
        if producto is not None:
            if not producto.hay_stock(compra.cantidad):
                return False, "No se puede anular: ya se vendió esa mercadería"
            producto.descontar_stock(compra.cantidad)
            self.productos.guardar()

        self.lista.remove(compra)
        self.guardar()
        return True, f"Compra {id_compra} anulada y stock descontado"

    # --- propio de compras ---
    def orden_compra(self, id_compra):
        compra = self.obtener(id_compra)
        if compra is None:
            return None

        proveedor = self.proveedores.obtener(compra.proveedor_id)
        producto = self.productos.obtener(compra.producto_id)
        total = compra.calcular_total()

        texto = f"ORDEN DE COMPRA #{compra.id}   fecha: {compra.fecha}\n"
        if proveedor:
            texto += (f"Proveedor: {proveedor.empresa or 'sin empresa'} · "
                      f"{proveedor.nombre_completo()}   (RUC {proveedor.ruc})\n")
        else:
            texto += "Proveedor: eliminado\n"
        texto += f"Producto : {producto.nombre if producto else 'eliminado'}\n"
        texto += f"Cantidad : {compra.cantidad} x ${compra.costo_unitario:.2f}\n"
        texto += "-" * 42 + "\n"
        texto += f"SUBTOTAL : ${total:.2f}\n"
        texto += f"TOTAL con IVA: ${Producto.con_iva(total):.2f}"
        return texto

    def compras_por_proveedor(self):
        """DICCIONARIO de LISTAS: {proveedor_id: [compras de ese proveedor]}.
        Se usa un diccionario porque se busca por clave (el id del proveedor)
        sin recorrer todo, y una lista porque cada proveedor tiene varias compras."""
        agrupadas = {}
        for compra in self.lista:
            if compra.proveedor_id not in agrupadas:
                agrupadas[compra.proveedor_id] = []
            agrupadas[compra.proveedor_id].append(compra)
        return agrupadas

    def total_comprado(self):
        total = 0
        for compra in self.lista:
            total += compra.calcular_total()
        return round(total, 2)

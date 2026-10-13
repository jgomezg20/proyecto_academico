from abc import ABC, abstractmethod

from models import Estudiante, Materia, Matricula
from shared.json_manager import GestorJSON
from shared.herramientas import es_email_valido

# Este archivo es el CONTROLADOR: no habla con el usuario (cero salidas por pantalla ni entradas por teclado).
# Toda operación devuelve la TUPLA (exito, mensaje) o datos.


def ids_registrados(objetos):
    """CONJUNTO con los ids que existen: preguntar 'x in conjunto' es instantáneo
    y, además, un conjunto no admite repetidos, que es justo lo que son los ids."""
    return {objeto.id for objeto in objetos}


# =====================================================================
# CLASE BASE (ABSTRACTA)
# =====================================================================
# Solo dice QUÉ métodos debe tener todo controlador.
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
# CONTROLADOR DE ESTUDIANTES
# =====================================================================
class EstudianteController(CrudBase):
    # TUPLAS: son listas de nombres fijos que nunca cambian mientras corre el programa,
    # por eso no son listas (no se pueden modificar por error).
    OBLIGATORIOS = ("nombre", "apellido", "email", "carnet")
    CAMPOS_BUSCABLES = ("nombre", "apellido", "email", "carnet", "carrera")

    def __init__(self, archivo="data/estudiantes.json"):
        self.gestor = GestorJSON(archivo)
        # Leemos el JSON y convertimos cada diccionario en un objeto Estudiante
        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Estudiante.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for estudiante in self.lista:
            datos.append(estudiante.a_diccionario())
        self.gestor.guardar(datos)

    # ---------- conjuntos para las reglas de unicidad ----------
    def carnets_registrados(self, excepto_id=None):
        """CONJUNTO de carnets ya usados: preguntar 'x in conjunto' es instantáneo
        y los repetidos desaparecen solos."""
        return {e.carnet.upper() for e in self.lista if e.id != excepto_id}

    def emails_registrados(self, excepto_id=None):
        """CONJUNTO de emails ya usados por los OTROS estudiantes."""
        return {e.email.lower() for e in self.lista if e.id != excepto_id}

    def validar(self, datos, id_actual=None):
        """Devuelve un mensaje de error, o None si todo está bien."""
        # Al crear hay que traer los obligatorios; al actualizar, solo lo que cambia
        if id_actual is None:
            for campo in self.OBLIGATORIOS:
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"
        if "email" in datos:
            email = str(datos["email"]).strip().lower()
            if not es_email_valido(email):
                return f"Email inválido: '{email}'"
            if email in self.emails_registrados(id_actual):
                return "Ese email ya está registrado"
        if "carnet" in datos:
            carnet = str(datos["carnet"]).strip().upper()
            if carnet == "":
                return "El carnet no puede quedar vacío"
            if carnet in self.carnets_registrados(id_actual):
                return f"El carnet {carnet} ya está registrado"
        return None

    # ---------- las 5 operaciones ----------
    def leer(self):
        return self.lista

    def obtener(self, id_estudiante):
        for estudiante in self.lista:
            if estudiante.id == id_estudiante:
                return estudiante
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontrados = []
        if texto == "":
            return encontrados
        for estudiante in self.lista:
            for campo in self.CAMPOS_BUSCABLES:       # recorre la TUPLA de campos
                if texto in str(getattr(estudiante, campo)).lower():
                    encontrados.append(estudiante)
                    break                              # ya coincidió: no repetirlo
        return encontrados

    def siguiente(self):
        mayor = 0
        for estudiante in self.lista:
            if estudiante.id > mayor:
                mayor = estudiante.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error
        estudiante = Estudiante(self.siguiente(),
                                str(datos["nombre"]).strip().title(),
                                str(datos["apellido"]).strip().title(),
                                str(datos["email"]).strip().lower(),
                                str(datos["carnet"]).strip().upper(),
                                str(datos.get("carrera", "")).strip().title())
        self.lista.append(estudiante)
        self.guardar()
        return True, f"Estudiante creado: {estudiante.etiqueta()}"

    def actualizar(self, id_estudiante, datos):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"
        if not datos:
            return False, "No se indicó ningún cambio"
        # DIFERENCIA de conjuntos: campos que no existen en un estudiante
        permitidos = {"nombre", "apellido", "email", "carnet", "carrera"}
        desconocidos = set(datos) - permitidos
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"
        # Se valida ANTES de tocar el objeto: si algo falla, no cambia nada
        error = self.validar(datos, id_estudiante)
        if error:
            return False, error
        for campo, valor in datos.items():
            valor = str(valor).strip()
            if campo in ("nombre", "apellido", "carrera"):
                valor = valor.title()
            elif campo == "email":
                valor = valor.lower()
            elif campo == "carnet":
                valor = valor.upper()
            setattr(estudiante, campo, valor)
        self.guardar()
        return True, f"Estudiante {id_estudiante} actualizado"

    def eliminar(self, id_estudiante):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"
        self.lista.remove(estudiante)
        self.guardar()
        return True, f"Estudiante {id_estudiante} eliminado"

    # ---------- propio de estudiantes ----------
    def carreras(self):
        """CONJUNTO de carreras: sin repetidas. sorted() lo devuelve como lista ordenada."""
        return sorted({e.carrera for e in self.lista if e.carrera != ""})


# =====================================================================
# CONTROLADOR DE MATERIAS
# =====================================================================
class MateriaController(CrudBase):
    OBLIGATORIOS = ("nombre", "codigo", "creditos")     # TUPLA: lista fija de nombres
    CAMPOS_BUSCABLES = ("nombre", "codigo")             # TUPLA: lista fija de nombres

    def __init__(self, archivo="data/materias.json"):
        self.gestor = GestorJSON(archivo)
        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Materia.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for materia in self.lista:
            datos.append(materia.a_diccionario())
        self.gestor.guardar(datos)

    def codigos_registrados(self, excepto_id=None):
        """CONJUNTO de códigos ya usados: comprobar si existe uno es instantáneo."""
        return {m.codigo.upper() for m in self.lista if m.id != excepto_id}

    def validar(self, datos, id_actual=None):
        if id_actual is None:
            for campo in self.OBLIGATORIOS:
                if str(datos.get(campo, "")).strip() == "":
                    return f"El campo {campo} es obligatorio"
        if "nombre" in datos and str(datos["nombre"]).strip() == "":
            return "El nombre no puede quedar vacío"
        if "codigo" in datos:
            codigo = str(datos["codigo"]).strip().upper()
            if codigo == "":
                return "El código no puede quedar vacío"
            if codigo in self.codigos_registrados(id_actual):
                return f"Ya existe una materia con el código {codigo}"
        if "creditos" in datos:
            creditos = str(datos["creditos"]).strip()
            if not creditos.isdigit() or not 1 <= int(creditos) <= 10:
                return "Los créditos deben ser un número entero entre 1 y 10"
        cupos = str(datos.get("cupos", "")).strip()
        if cupos != "":
            if not cupos.isdigit() or int(cupos) > Materia.CUPOS_MAXIMOS:
                return f"Los cupos deben ser un entero entre 0 y {Materia.CUPOS_MAXIMOS}"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_materia):
        for materia in self.lista:
            if materia.id == id_materia:
                return materia
        return None

    def buscar(self, texto):
        texto = texto.strip().lower()
        encontradas = []
        if texto == "":
            return encontradas
        for materia in self.lista:
            for campo in self.CAMPOS_BUSCABLES:
                if texto in str(getattr(materia, campo)).lower():
                    encontradas.append(materia)
                    break
        return encontradas

    def siguiente(self):
        mayor = 0
        for materia in self.lista:
            if materia.id > mayor:
                mayor = materia.id
        return mayor + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error
        # Si no escribieron los cupos, la materia abre con el máximo permitido
        cupos = str(datos.get("cupos", "")).strip()
        materia = Materia(self.siguiente(),
                          str(datos["nombre"]).strip().title(),
                          str(datos["codigo"]).strip().upper(),
                          int(datos["creditos"]),
                          int(cupos) if cupos != "" else Materia.CUPOS_MAXIMOS)
        self.lista.append(materia)
        self.guardar()
        return True, f"Materia creada: {materia.etiqueta()}"

    def actualizar(self, id_materia, datos):
        materia = self.obtener(id_materia)
        if materia is None:
            return False, f"No existe una materia con id {id_materia}"
        if not datos:
            return False, "No se indicó ningún cambio"
        desconocidos = set(datos) - {"nombre", "codigo", "creditos", "cupos"}
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"
        error = self.validar(datos, id_materia)
        if error:
            return False, error
        if "nombre" in datos:
            materia.nombre = str(datos["nombre"]).strip().title()
        if "codigo" in datos:
            materia.codigo = str(datos["codigo"]).strip().upper()
        if "creditos" in datos:
            materia.creditos = int(datos["creditos"])
        if "cupos" in datos:
            materia.cupos = int(datos["cupos"])
        self.guardar()
        return True, f"Materia {id_materia} actualizada"

    def eliminar(self, id_materia):
        materia = self.obtener(id_materia)
        if materia is None:
            return False, f"No existe una materia con id {id_materia}"
        self.lista.remove(materia)
        self.guardar()
        return True, f"Materia {id_materia} eliminada"

    # ---------- propio de materias ----------
    def materias_sin_cupo(self):
        sin_cupo = []
        for materia in self.lista:
            if not materia.hay_cupo():
                sin_cupo.append(materia)
        return sin_cupo


# =====================================================================
# CONTROLADOR DE MATRÍCULAS
# =====================================================================
class MatriculaController(CrudBase):
    def __init__(self, estudiantes, materias, archivo="data/matriculas.json"):
        # La matrícula USA a los otros dos controladores.
        # Hay que pasarle los MISMOS que usa main.py.
        self.estudiantes = estudiantes
        self.materias = materias
        self.gestor = GestorJSON(archivo)
        self.lista = []
        for datos in self.gestor.leer():
            self.lista.append(Matricula.desde_diccionario(datos))

    def guardar(self):
        datos = []
        for matricula in self.lista:
            datos.append(matricula.a_diccionario())
        self.gestor.guardar(datos)

    def validar(self, datos):
        try:
            estudiante_id = int(datos.get("estudiante_id", 0))
            materia_id = int(datos.get("materia_id", 0))
        except (TypeError, ValueError):
            return "estudiante_id y materia_id deben ser números enteros"
        periodo = str(datos.get("periodo", "")).strip()
        partes = periodo.split("-")
        if len(partes) != 2 or len(partes[0]) != 4 \
                or not partes[0].isdigit() or not partes[1].isdigit():
            return "El periodo debe tener formato AAAA-N, por ejemplo 2026-1"
        # CONJUNTOS de ids: saber si un id existe es instantáneo
        if estudiante_id not in ids_registrados(self.estudiantes.leer()):
            return f"No existe un estudiante con id {estudiante_id}"
        if materia_id not in ids_registrados(self.materias.leer()):
            return f"No existe una materia con id {materia_id}"
        # CONJUNTO de TUPLAS (estudiante, materia, periodo): las tres cosas juntas
        # identifican una matrícula; la tupla es inmutable, así que puede ir en un conjunto.
        ya_matriculados = {(m.estudiante_id, m.materia_id, m.periodo) for m in self.lista}
        if (estudiante_id, materia_id, periodo) in ya_matriculados:
            return "Ese estudiante ya está matriculado en esa materia en ese periodo"
        materia = self.materias.obtener(materia_id)
        if not materia.hay_cupo():
            return f"No hay cupos disponibles en {materia.nombre}"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_matricula):
        for matricula in self.lista:
            if matricula.id == id_matricula:
                return matricula
        return None

    def buscar(self, texto):
        # Las matrículas se buscan por periodo, ej: "2026-1"
        texto = texto.strip()
        encontradas = []
        if texto == "":
            return encontradas
        for matricula in self.lista:
            if texto in matricula.periodo:
                encontradas.append(matricula)
        return encontradas

    def siguiente(self):
        mayor = 0
        for matricula in self.lista:
            if matricula.id > mayor:
                mayor = matricula.id
        return mayor + 1

    def crear(self, datos):
        # datos = {"estudiante_id": 1, "materia_id": 2, "periodo": "2026-1"}
        error = self.validar(datos)
        if error:
            return False, error
        estudiante = self.estudiantes.obtener(int(datos["estudiante_id"]))
        materia = self.materias.obtener(int(datos["materia_id"]))
        matricula = Matricula(self.siguiente(), estudiante.id, materia.id,
                              str(datos["periodo"]).strip())
        materia.ocupar_cupo()
        self.materias.guardar()                 # guarda el cupo nuevo en materias.json
        self.lista.append(matricula)
        self.guardar()                          # guarda la matrícula en matriculas.json
        return True, (f"Matrícula {matricula.id} registrada: {estudiante.nombre_completo()} "
                      f"en {materia.nombre} ({matricula.periodo})")

    def crear_matricula(self, datos):
        return self.crear(datos)

    def actualizar(self, id_matricula, datos):
        # Una matrícula no se edita: la nota se registra con registrar_nota()
        # y para cambiar estudiante/materia se retira y se matricula de nuevo
        return False, "Las matrículas no se editan: use registrar nota o retírela y matricule otra"

    def eliminar(self, id_matricula):
        """Retirar una matrícula: se borra y el cupo vuelve a la materia."""
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return False, f"No existe la matrícula {id_matricula}"
        materia = self.materias.obtener(matricula.materia_id)
        if materia is not None:
            materia.liberar_cupo()
            self.materias.guardar()
        self.lista.remove(matricula)
        self.guardar()
        return True, f"Matrícula {id_matricula} retirada y cupo devuelto"

    # ---------- propio de matrículas ----------
    def retirar_matricula(self, id_matricula):
        return self.eliminar(id_matricula)

    def registrar_nota(self, id_matricula, nota):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return False, f"No existe la matrícula {id_matricula}"
        nota = str(nota).strip().replace(",", ".")
        # es_nota_valida es el método ESTÁTICO de Materia
        if not Materia.es_nota_valida(nota):
            return False, f"Nota inválida: '{nota}' (debe ser un número entre 0 y 20)"
        matricula.nota = float(nota)
        self.guardar()
        return True, f"Nota registrada: {matricula.nota} ({matricula.estado()})"

    def certificado(self, id_matricula):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return None
        # DICCIONARIOS ÍNDICE {id: objeto}: encontrar el estudiante o la materia
        # por su id es instantáneo, sin recorrer la lista de uno en uno.
        estudiantes_por_id = {e.id: e for e in self.estudiantes.leer()}
        materias_por_id = {m.id: m for m in self.materias.leer()}
        estudiante = estudiantes_por_id.get(matricula.estudiante_id)
        materia = materias_por_id.get(matricula.materia_id)
        nota = "pendiente" if matricula.nota is None else matricula.nota
        texto = f"CERTIFICADO #{matricula.id}   periodo: {matricula.periodo}\n"
        if estudiante:
            texto += f"Estudiante: {estudiante.nombre_completo()}   ({estudiante.carnet})\n"
        else:
            texto += "Estudiante: eliminado\n"
        if materia:
            texto += (f"Materia   : {materia.nombre}   ({materia.codigo}) "
                      f"· {materia.creditos} créditos\n")
        else:
            texto += "Materia   : eliminada\n"
        texto += "-" * 42 + "\n"
        texto += f"Nota      : {nota}\n"
        texto += f"Estado    : {matricula.estado()}"
        return texto

    def matriculas_por_estudiante(self):
        """DICCIONARIO de LISTAS: {estudiante_id: [matrículas de ese estudiante]}.
        Un diccionario agrupa por clave y cada valor es una lista porque un
        estudiante puede tener muchas matrículas."""
        agrupadas = {}
        for matricula in self.lista:
            agrupadas.setdefault(matricula.estudiante_id, []).append(matricula)
        return agrupadas

    def promedio_de_estudiante(self, id_estudiante):
        """Promedio de las notas registradas, o None si todavía no tiene ninguna."""
        suyas = self.matriculas_por_estudiante().get(id_estudiante, [])
        notas = [m.nota for m in suyas if m.nota is not None]
        if not notas:
            return None
        return round(sum(notas) / len(notas), 2)

    def total_aprobadas(self):
        total = 0
        for matricula in self.lista:
            if matricula.esta_aprobada():
                total += 1
        return total

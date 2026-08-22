===============================
Gestión de Contratos (Crumges)
===============================

..
   Este módulo proporciona una capa de gestión avanzada para los Contratos de Odoo.

Este módulo extiende las funcionalidades nativas de gestión de contratos de Odoo añadiendo herramientas potentes para la gestión de plantillas, términos y condiciones, tableros interactivos y un motor de auditoría automatizado.

**Índice**

.. contents::
   :local:

Funcionalidades
===============

* **Plantillas de Contratos:** Permite definir plantillas predeterminadas para los contratos, estandarizando el proceso de creación.
* **Términos y Condiciones:** Gestiona de forma segura los Términos y Condiciones vinculados a los contratos, bloqueándolos una vez que el contrato es confirmado para evitar alteraciones legales.
* **Motor de Auditoría:** Rastrea y registra automáticamente los cambios críticos en los contratos (como variaciones de precios, cambios de estado o aplazamientos de fecha de finalización) y los muestra claramente en el chatter y en el portal del cliente.
* **Tableros Interactivos (Dashboards):** Proporciona una visión general visual de los estados de los contratos, tendencias y métricas clave.

Configuración
=============

Para configurar este módulo, es necesario:

1. Ir a *Contratos > Configuración > Ajustes* para administrar las configuraciones generales.
2. Ir a *Contratos > Configuración > Reglas de Modificación* para personalizar qué campos deben disparar un registro de auditoría al ser modificados.

Uso
===

Para usar este módulo, es necesario:

1. Ir al menú de *Contratos*.
2. Crear un nuevo Contrato y seleccionar una plantilla preconfigurada.
3. Una vez que el contrato esté en curso, cualquier modificación a los campos monitoreados quedará registrada en la pestaña *Modificaciones*.

Rastreador de Errores (Bug Tracker)
===================================

Los errores se rastrean en el sistema interno de incidencias de Crumges. En caso de problemas, por favor contacte a soporte.

Créditos
========

Autores
~~~~~~~

* Crumges

Mantenedores
~~~~~~~~~~~~

Este módulo es mantenido por Crumges.

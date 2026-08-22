import re

descriptions = {
    "template_demo_1": """<![CDATA[
        <p>📦 <b>Provisión recurrente de granos de café de especialidad</b> para la oficina.</p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Agrega productos como <i>Bolsas de 1kg de Café Colombia</i> o <i>Kenia AA</i>.</li>
            <li>Puedes incluir un servicio de mantenimiento básico de la cafetera en las líneas del contrato.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Revisa las notas internas antes de facturar para validar si el cliente solicitó cambios de origen.</p>
    ]]>""",
    "template_demo_2": """<![CDATA[
        <p>🖋️ <b>Reposición trimestral de resmas, tintas y artículos de papelería.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Ideal para productos consumibles como <i>Resmas A4</i>, <i>Tóner de impresora</i>, <i>Bolígrafos</i>.</li>
            <li>Si el cliente requiere material de branding (carpetas con logo), añádelo como una línea de facturación única.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Este contrato genera una Orden de Venta. Asegúrate de procesar el remito/albarán de entrega para que el cliente firme la recepción.</p>
    ]]>""",
    "template_demo_3": """<![CDATA[
        <p>🛠️ <b>Servicio de mantenimiento preventivo y soporte técnico de infraestructura IT.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Agrega un producto de <i>Soporte Nivel 1 (Abono Fijo)</i>.</li>
            <li>Puedes agregar líneas adicionales para <i>Bolsa de 10 horas excedentes</i> o <i>Mantenimiento de Servidores Físicos</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Al finalizar el mes, adjunta el reporte de uptime del servidor en el chatter del contrato para transparencia con el cliente.</p>
    ]]>""",
    "template_demo_4": """<![CDATA[
        <p>✨ <b>Limpieza integral de oficinas y espacios comunes.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Producto principal: <i>Servicio de Limpieza Diario (Horas)</i>.</li>
            <li>Opcional: <i>Provisión de insumos de baño (papel, jabón)</i> facturados por separado según consumo.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Como genera Orden de Venta, el equipo operativo debe registrar sus partes de horas para que la factura final sea precisa.</p>
    ]]>""",
    "template_demo_5": """<![CDATA[
        <p>💼 <b>Liquidación de impuestos, sueldos y balances contables.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Línea fija: <i>Abono mensual contable</i>.</li>
            <li>Líneas variables: <i>Liquidación de Cargas Sociales (por cápita)</i>.</li>
            <li>Línea anual (facturada 1 vez): <i>Presentación de Balance Anual</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Revisa las fechas de vencimiento de AFIP y ajusta la fecha de la próxima factura para que llegue antes del día 5.</p>
    ]]>""",
    "template_demo_6": """<![CDATA[
        <p>📣 <b>Community management, diseño de posteos y pauta publicitaria.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Línea principal: <i>Gestión de Meta Ads (Fee Agencia)</i>.</li>
            <li>Línea secundaria: <i>Pack de 12 Posteos (Diseño y Copy)</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> La pauta publicitaria (inversión en Google/Meta) NO debe incluirse aquí a menos que refactures con mark-up. Configura la factura al inicio del mes.</p>
    ]]>""",
    "template_demo_7": """<![CDATA[
        <p>🔐 <b>Escaneo de vulnerabilidades y pentesting anual.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Productos: <i>Auditoría Black-Box</i>, <i>Capacitación Phishing a Empleados</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Este contrato es ideal para renovaciones automáticas anuales. Asegúrate de coordinar la ventana de mantenimiento con el cliente antes de ejecutar el escaneo.</p>
    ]]>""",
    "template_demo_8": """<![CDATA[
        <p>💻 <b>Suscripción mensual por el uso de la plataforma en la nube (Hosting/VPS).</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Añade productos de infraestructura: <i>VPS 4 Cores 8GB RAM</i>, <i>Backup en S3 (por TB)</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Revisa mensualmente el consumo de ancho de banda o almacenamiento extra antes de que se genere la factura automática.</p>
    ]]>""",
    "template_demo_9": """<![CDATA[
        <p>💪 <b>Membresía Gimnasio Premium: Acceso libre a sucursales y clases grupales.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Añade el producto <i>Pase Libre VIP</i>.</li>
            <li>Agrega <i>Alquiler de Casillero Permanente</i> como un opcional recurrente.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Si el socio solicita congelar la membresía por vacaciones, usa el botón de suspender o modifica la fecha de la próxima factura.</p>
    ]]>""",
    "template_demo_10": """<![CDATA[
        <p>🍇 <b>Club de Vinos: Envío de cajas seleccionadas por sommelier cada mes.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Producto: <i>Caja Selección Bodegas Boutique (6 botellas)</i>.</li>
            <li>Puedes incluir un <i>Seguro de rotura de carga</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Notifica a logística la cantidad de contratos activos al menos 10 días antes del cierre de mes para asegurar el stock de botellas.</p>
    ]]>""",
    "template_demo_11": """<![CDATA[
        <p>📄 <b>Alquiler mensual de equipo de impresión multifunción.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Cargo Fijo: <i>Abono Alquiler Impresora Laser</i>.</li>
            <li>Cargo Variable: <i>Copias Excedentes (precio por página)</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Si utilizas cargos variables, asegúrate de ingresar la lectura del contador de impresiones antes de que se emita la factura mensual.</p>
    ]]>""",
    "template_demo_12": """<![CDATA[
        <p>🚜 <b>Alquiler de maquinaria pesada (excavadoras, grúas) para la construcción.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Producto: <i>Alquiler de Retroexcavadora (Día/Semana)</i>.</li>
            <li>Servicio Adicional: <i>Flete de traslado de maquinaria</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Este contrato genera Órdenes de Venta. Esto te permitirá gestionar el albarán de salida de la máquina y registrar su retorno seguro al inventario.</p>
    ]]>""",
    "template_demo_13": """<![CDATA[
        <p>🪑 <b>Alquiler de espacio de trabajo fijo en Coworking con acceso a salas.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Producto Principal: <i>Escritorio Dedicado (Mensual)</i>.</li>
            <li>Extras: <i>Horas excedentes Sala de Reuniones</i>, <i>Servicio de Casillero Postal</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Si el cliente cancela, desactiva el contrato y asegúrate de revocar sus credenciales de acceso magnético al edificio.</p>
    ]]>""",
    "template_demo_14": """<![CDATA[
        <p>🛣️ <b>Renting de vehículos para ejecutivos o flota comercial.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Cargos Fijos: <i>Alquiler Vehículo Sedán (Mensual)</i>.</li>
            <li>Cargos Variables: <i>Kilómetros excedentes</i>, <i>Re-facturación de multas de tránsito</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Actualiza los precios del seguro a todo riesgo periódicamente si la póliza sufre ajustes por inflación.</p>
    ]]>""",
    "template_demo_15": """<![CDATA[
        <p>📹 <b>Servicio 24/7 de monitoreo de seguridad y respuesta rápida.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Producto: <i>Abono Monitoreo Alarma Domiciliaria/Comercial</i>.</li>
            <li>Adicionales: <i>Mantenimiento de Cámaras CCTV</i>, <i>Servicio de Acuda (Respuesta Física)</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> La facturación suele ser muy automatizada. Revisa que el cliente tenga configurada su tarjeta de crédito o método de débito automático (si está instalado el módulo de pagos).</p>
    ]]>""",
    "template_demo_16": """<![CDATA[
        <p>🥗 <b>Viandas diarias entregadas en la oficina para el personal.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Producto: <i>Menú Ejecutivo Diario (Cantidad = Número de Empleados)</i>.</li>
            <li>Opcional: <i>Menú Celíaco / Vegetariano</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Este contrato genera Órdenes de Venta. Modifica las cantidades en la orden si el cliente reporta ausencias o días de Home Office antes de confirmar la entrega.</p>
    ]]>""",
    "template_demo_17": """<![CDATA[
        <p>🔧 <b>Mantenimiento preventivo y correctivo de ascensores.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Cargo Fijo: <i>Abono de Revisión Mensual (Ley GCBA)</i>.</li>
            <li>Extras: <i>Repuestos (Lubricantes, Botoneras)</i> que superen la franquicia de la póliza.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Programa las tareas de los técnicos en el calendario basándote en la fecha de este contrato para no incurrir en multas municipales.</p>
    ]]>""",
    "template_demo_18": """<![CDATA[
        <p>🛡️ <b>Póliza colectiva de seguro de vida para empleados.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Producto: <i>Prima de Seguro de Vida (Por Cápita)</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Actualiza la cantidad de empleados en las líneas del contrato todos los meses antes de emitir la factura, cruzando datos con el departamento de RRHH.</p>
    ]]>""",
    "template_demo_19": """<![CDATA[
        <p>🏢 <b>CONTRATO DE PROVEEDOR: Pago de alquiler del edificio comercial.</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Línea de Gasto: <i>Alquiler Inmueble (Gasto Fijo)</i>.</li>
            <li>Opcional: <i>Expensas / Gastos Comunes</i> si se facturan junto al alquiler.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Como es un contrato de compras, esto generará automáticamente facturas de proveedor en estado borrador. Valida el número de comprobante fiscal antes de publicarla.</p>
    ]]>""",
    "template_demo_20": """<![CDATA[
        <p>🌩️ <b>CONTRATO DE PROVEEDOR: Abono anual de servidores y licencias (AWS/ERP).</b></p>
        <br/>
        <p><b>💡 Ideas de uso:</b></p>
        <ul>
            <li>Líneas de Compra: <i>Suscripción Odoo Enterprise</i>, <i>Servidores Google Cloud</i>.</li>
        </ul>
        <p><b>⚠️ Recuerda:</b> Revisa el tipo de cambio oficial si el contrato está en moneda extranjera y ajústalo antes de aprobar la factura de compra.</p>
    ]]>""",
}

with open(
    "/home/mario/Documentos/Desarrollo/modulos_de_odoo/creacion_de_modulos/modulos_18/contract_management/data/contract_template_data.xml",
    encoding="utf-8",
) as f:
    content = f.read()

for template_id, new_desc in descriptions.items():
    # Find the record block
    block_pattern = (
        f'(<record id="{template_id}" model="contract.template">.*?</record>)'
    )
    block_match = re.search(block_pattern, content, flags=re.DOTALL)
    if block_match:
        block = block_match.group(1)
        # Replace the description field
        desc_pattern = r'<field name="description"><!\[CDATA\[.*?\]\]></field>'
        new_field = f'<field name="description">{new_desc}</field>'
        new_block = re.sub(desc_pattern, new_field, block, flags=re.DOTALL)

        content = content.replace(block, new_block)

with open(
    "/home/mario/Documentos/Desarrollo/modulos_de_odoo/creacion_de_modulos/modulos_18/contract_management/data/contract_template_data.xml",
    "w",
    encoding="utf-8",
) as f:
    f.write(content)
import logging

logger = logging.getLogger(__name__)
logger.info("Updated XML descriptions successfully.")

# Documentación Técnica y Funcional — Módulo `pap_loyalty`
**Proyecto:** Papelería El Estudiante — Sistema Integrado de Fidelización  
**Versión Odoo:** 17.0  
**Versión módulo:** 17.0.1.0.0  
**Fecha:** 2026-04-27

---

## 1. Introducción y Resumen del Proyecto

El módulo `pap_loyalty` digitaliza el programa de fidelización de **Papelería El Estudiante**. Extiende el núcleo de ventas de Odoo 17 para acumular puntos por compra, permitir su canje como medio de pago y registrar cualquier ajuste manual sobre el saldo de un cliente.

El proyecto se despliega mediante **Docker Compose** con los siguientes servicios relevantes:

| Servicio | Imagen | Puerto | Rol |
|---|---|---|---|
| `odoo` | `odoo:17.0` | 8069 | Motor de datos y lógica de negocio |
| `db_odoo` | `postgres:15` | — | Base de datos relacional de Odoo |
| `n8n` | `n8nio/n8n:1` | 5678 | Orquestador de integraciones y webhooks |
| `bonita` | `bonita:2023.2` | 8081 | Gestor de procesos BPM y tareas humanas |

Todos los servicios comparten la red interna `default` y exponen sus interfaces hacia el exterior a través de la red `proxy`.

---

## 2. Estructura del Módulo

```
pap_loyalty/
├── __init__.py
├── __manifest__.py                        # Declaración, dependencias y lista de archivos de datos
├── data/
│   └── demo.xml                           # Datos de demostración
├── models/
│   ├── __init__.py
│   ├── pap_loyalty_move.py                # Modelo transaccional de puntos
│   ├── pap_loyalty_point_wizard.py        # Asistente de ajuste manual (TransientModel)
│   ├── product_template.py                # Extensión: flags y coste en puntos del producto
│   ├── res_partner.py                     # Extensión: saldo, consentimiento e historial del cliente
│   └── sale_order.py                      # Extensión: tipo de operación y lógica de canje
├── security/
│   └── ir.model.access.csv                # Permisos CRUD por grupo
└── views/
    ├── pap_loyalty_move_views.xml          # Lista, formulario y menú de movimientos
    ├── pap_loyalty_point_wizard_views.xml  # Formulario modal del asistente
    ├── product_template_views.xml          # Fidelización (pestaña Ventas) + minimum_stock (cabecera producto)
    ├── res_partner_views.xml               # Pestaña Fidelización en la ficha de cliente
    └── sale_order_views.xml               # Campo tipo operación y bloque de puntos en el pedido
```

---

## 3. Arquitectura de Integración

El flujo de alto nivel sigue una arquitectura **event-driven** basada en tres capas:

```
[Odoo 17]  ──webhook/API──►  [n8n]  ──HTTP POST──►  [Bonita BPM]
   │                           │
   │ (JSON-RPC)                └──► Crea pap.loyalty.move vía API
   │
   └── Lógica transaccional nativa (canje, validación de saldo)
```

- **Odoo** es el sistema de registro (*system of record*): valida, persiste y calcula.  
- **n8n** reacciona a eventos de Odoo (ventas confirmadas) y orquesta acciones externas asíncronas.  
- **Bonita BPM** gestiona el flujo de trabajo humano para encargos complejos (asignación, preparación, entrega).

![Arquitectura del Sistema](docs/images/arquitectura_sistema.png)

---

## 4. Modelos de Datos (Diccionario de Datos)

### `res.partner` — Extensión del cliente

Añade el saldo de puntos calculado en tiempo real a partir del historial de movimientos, el consentimiento comercial y un acceso directo al asistente de ajuste.

```python
loyalty_points = fields.Integer(
    compute='_compute_loyalty_points', store=True
)
# Suma únicamente movimientos en estado 'done'
partner.loyalty_points = sum(
    move.points for move in partner.loyalty_move_ids
    if move.state == 'done'
)
```

---

### `product.template` — Extensión del producto

Define los flags de fidelización y el umbral de stock mínimo para la integración con n8n/Bonita. `minimum_stock` se muestra en la cabecera del producto junto a los checkboxes de venta/compra; los campos de fidelización aparecen en la pestaña Ventas.

```python
loyalty_eligible = fields.Boolean(string='Apto para Fidelización')
redeemable       = fields.Boolean(string='Canjeable con Puntos')
loyalty_ratio    = fields.Float(string='Ratio pts/€')
loyalty_cost     = fields.Integer(string='Coste en Puntos')
minimum_stock    = fields.Integer(string='Stock Mínimo', default=0)
```

---

### `sale.order` — Extensión del pedido de venta

Clasifica cada venta en tres modalidades y, en modo canje, valida el saldo antes de confirmar y aplica un descuento del 100 % sobre las líneas canjeables.

```python
x_tipo_operacion = fields.Selection([
    ('venta_directa', 'Venta Directa'),
    ('encargo',       'Encargo Complejo'),
    ('canje_puntos',  'Canje por Puntos'),
])

# En action_confirm(), si x_tipo_operacion == 'canje_puntos':
if not order.x_puntos_suficientes:
    raise UserError("Puntos insuficientes.")
for line in order.order_line:
    if line.product_id.redeemable:
        line.discount = 100.0
```

Campos computados de apoyo: `x_puntos_disponibles` (related), `x_puntos_requeridos` (suma de `loyalty_cost × qty`), `x_puntos_suficientes` (booleano).

---

### `pap.loyalty.move` — Movimiento de puntos

Tabla transaccional que registra cada variación de saldo. Los puntos negativos representan canjes o ajustes a la baja; los positivos, acumulaciones.

```python
move_type = fields.Selection([
    ('earn',   'Acumular'),
    ('redeem', 'Canjear'),
    ('adjust', 'Ajuste'),
])
state = fields.Selection([
    ('draft', 'Borrador'), ('done', 'Confirmado'), ('cancelled', 'Cancelado')
])
# Solo los movimientos 'done' afectan al saldo del cliente.
```

---

### `pap.loyalty.point.wizard` — Asistente de ajuste manual

`TransientModel` que permite crear un movimiento de tipo `adjust` directamente desde la ficha del cliente, sin necesidad de navegar al menú de movimientos.

```python
class PapLoyaltyPointWizard(models.TransientModel):
    _name = 'pap.loyalty.point.wizard'

    partner_id = fields.Many2one('res.partner', required=True, readonly=True)
    points     = fields.Integer(required=True)   # positivo o negativo
    notes      = fields.Text()

    def action_apply(self):
        self.env['pap.loyalty.move'].create({
            'move_type': 'adjust', 'state': 'done', ...
        })
```

---

## 5. Interfaz de Usuario (Vistas)

### Vistas modificadas (herencia)

| Vista base | Modificación |
|---|---|
| `sale.order` (formulario) | Campo radio `x_tipo_operacion` tras *Plazos de pago*; bloque condicional con puntos disponibles/requeridos y alertas de suficiencia. |
| `res.partner` (formulario) | Nueva pestaña **Fidelización** con saldo, botón *Añadir / Ajustar Puntos* e historial de movimientos en modo lectura. |
| `product.template` (formulario) | Campo `minimum_stock` en la cabecera junto a *Puede ser vendido/comprado*. Campos `loyalty_eligible`, `redeemable`, `loyalty_ratio` y `loyalty_cost` en pestaña **Ventas**. |

### Vistas nuevas

| Modelo | Vistas | Descripción |
|---|---|---|
| `pap.loyalty.move` | `tree`, `form` | Lista y detalle de movimientos con botones **Confirmar** / **Cancelar** en la cabecera. |
| `pap.loyalty.point.wizard` | `form` (modal) | Formulario emergente con cliente (solo lectura), puntos y notas. |

### Menú creado

```
Fidelización
└── Movimientos   →  pap.loyalty.move (tree/form)
```

![Vista ficha de cliente con puntos](docs/images/partner_loyalty_tab.png)
![Asistente de ajuste manual de puntos](docs/images/wizard_ajuste_puntos.png)
![Vista de la configuración del producto](docs/images/product_loyalty_config.png)

---

## 6. Flujos de Trabajo (Workflows) y Automatización

n8n actúa como orquestador central entre Odoo y Bonita BPM. Los flujos se activan bien mediante **Webhooks** lanzados desde Odoo al confirmar un pedido, bien mediante un **Schedule Trigger** programado. En todos los casos, n8n es responsable de leer datos de Odoo vía JSON-RPC, autenticarse en Bonita BPM para instanciar procesos, y notificar al cliente por correo. La lógica transaccional de puntos (canje) permanece íntegramente en Odoo y no pasa por n8n.

---

### Flujo 1 — Acumulación de Puntos (`n8n + Odoo`)

Activado por Webhook cuando Odoo confirma un pedido de tipo `venta_directa`. n8n extrae los datos de la venta, calcula los puntos generados y registra el movimiento directamente en Odoo.

```
[Odoo] Confirma pedido (venta_directa)
    └─► Webhook  ──────────────────────────────────────►  [n8n]
                                                              │
                                                    ┌─────────┴──────────┐
                                             getPedido   getCliente   getProductosComprados
                                             (Odoo node) (Odoo node)  (Odoo node)
                                                    └─────────┬──────────┘
                                                              │
                                                    Cálculo de puntos:
                                                    loyalty_ratio × precio × cantidad
                                                              │
                                                    Odoo node: crea pap.loyalty.move
                                                    (move_type='earn', state='done')
                                                              │
                                                    Send Email → cliente
                                                    "Has acumulado N puntos"
```

**Nodos n8n involucrados:** `Webhook` · `getPedido` · `getCliente` · `getProductosComprados` · `Odoo` (create move) · `Send Email`

**Resultado:** El movimiento `earn` actualiza el saldo del cliente en Odoo y se notifica al cliente por correo.

![Flujo 1 n8n — Acumulación de Puntos](docs/images/n8n_flujo1_puntos.png)

---

### Subflujo — Canje de Puntos (Nativo en Odoo, sin n8n)

> **Este subflujo NO pasa por n8n.** Es lógica transaccional nativa del módulo `pap_loyalty`.

El empleado selecciona `x_tipo_operacion = 'canje_puntos'` en el pedido. El modelo `sale.order` calcula en tiempo real los campos `x_puntos_disponibles` y `x_puntos_requeridos`. Al confirmar, el método `action_confirm()` en Python valida el saldo, aplica un descuento del 100 % sobre todas las líneas con `redeemable = True` y crea automáticamente un `pap.loyalty.move` de tipo `redeem` con puntos negativos — todo en una única transacción de base de datos.

```
[Empleado] Selecciona "Canje por Puntos" en el pedido
    │
    ├─► Vista muestra x_puntos_disponibles / x_puntos_requeridos (tiempo real)
    │
    └─► Confirmar pedido
            │
            ├─► [GUARD] x_puntos_suficientes == False → UserError, operación bloqueada
            │
            └─► [OK] sale.order.action_confirm() [Python]
                    ├─► discount = 100 % en líneas redeemable
                    ├─► Pedido confirmado (total neto = 0 €)
                    └─► pap.loyalty.move (move_type='redeem', points=-N, state='done')
                                └─► loyalty_points del cliente decrementado
```

**Resultado:** El cliente paga con puntos sin intervención externa; la atomicidad está garantizada por la transacción ORM de Odoo.

![Pedido con canje de puntos](docs/images/sale_order_canje_puntos.png)
![Pedido de venta Exitoso en modo Canje por Puntos](docs/images/sale_order_exitoso.png)

---

### Flujo 2 — Reposición de Bajo Stock (`n8n + Bonita + Odoo`)

Activado por un **Schedule Trigger** programado a las **22:00 h** diariamente. n8n consulta Odoo en busca de productos con stock por debajo del umbral `minimum_stock`, inicia el proceso de reposición en Bonita BPM y genera automáticamente el borrador de pedido de compra en Odoo.

```
[n8n] Schedule Trigger — 22:00 h
    │
    └─► Odoo node: busca product.product
        WHERE qty_available ≤ minimum_stock
            │
            └─► Bonita: initializeSession → obtiene Token CSRF
                    │
                    └─► postStock: POST a API REST de Bonita
                        { producto, stock_actual, cantidad_minima }
                                │
                                ├─► Bonita instancia proceso de reposición
                                │       └─► Tarea humana asignada al equipo de compras
                                │
                                └─► Odoo node: crea purchase.order (borrador)
                                        └─► purchase.order.line con proveedor asociado
```

**Nodos n8n involucrados:** `Schedule Trigger` · `Odoo` (search products) · `initializeSession` (HTTP Request) · `postStock` (HTTP Request) · `Odoo` (create purchase.order) · `Odoo` (create purchase.order.line)

**Resultado:** Al inicio de cada noche se detectan automáticamente las roturas de stock, se abre la tarea en Bonita y el borrador de pedido de compra queda listo en Odoo para aprobación.

![Flujo 2 n8n — Reposición de Stock](docs/images/n8n_flujo2_stock.png)

---

### Flujo 3 — Gestión de Encargos (`n8n + Bonita`)

Activado por Webhook cuando Odoo confirma un pedido de tipo `encargo`. n8n recoge los datos del pedido y del comprador, inicia la tarea humana en Bonita BPM y notifica al cliente cuando el encargo está listo para recoger.

```
[Odoo] Confirma pedido (encargo)
    └─► Webhook  ──────────────────────────────────────►  [n8n]
                                                              │
                                                    ┌─────────┴─────────┐
                                                  getPedido         getCliente
                                                  (Odoo node)       (Odoo node)
                                                    └─────────┬─────────┘
                                                              │
                                                    Bonita: initializeSession
                                                    → Token CSRF
                                                              │
                                                    postEncargo: POST a API REST de Bonita
                                                    { pedido_id, cliente, productos, ... }
                                                              │
                                                    Bonita instancia tarea humana
                                                    "Preparar encargo"
                                                              │
                                                    Send Email → cliente
                                                    "Su pedido está listo para recogida"
```

**Nodos n8n involucrados:** `Webhook` · `getPedido` · `getCliente` · `initializeSession` (HTTP Request) · `postEncargo` (HTTP Request) · `Send Email`

**Resultado:** La tarea de preparación se asigna automáticamente en Bonita y el cliente recibe confirmación por correo sin intervención manual del operador.

![Flujo 3 n8n — Gestión de Encargos](docs/images/n8n_flujo3_encargos.png)
![Bandeja de Bonita BPM](docs/images/bonita_bandeja.png)

---

*Documento generado a partir del código fuente. Actualizar en cada sprint que modifique modelos o flujos.*

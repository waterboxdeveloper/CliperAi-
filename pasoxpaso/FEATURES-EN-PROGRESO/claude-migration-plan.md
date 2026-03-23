# Plan: Migración de Gemini a Claude API

**Status**: ⏳ Planificación
**Fecha**: 2026-03-22
**Objetivo**: Reducir costos y mejorar calidad de copies migrando a Claude

---

## 📊 Análisis del Estado Actual

### Uso de Gemini en CLIPER

**Ubicación**: `src/copys_generator.py` (1172 líneas)

**Puntos de integración**:
- Línea 139: Inicialización del modelo
- Línea 309: Llamada para clasificación de clips
- Línea 658: Llamada para generación de copies
- Línea 1038-1110: Guardado de metadata

**Dependencias relacionadas**:
```
langchain-google-genai>=2.1.12  ← Única dependencia Google
langgraph>=0.6.11                ← Orquestación (se mantiene)
```

**Problema**: Tier gratuito de Gemini limitado a 20 requests/día
- Se agota rápidamente procesando 30+ clips
- Requiere esperar 24h o pagar plan

---

## 🎯 Decisión Arquitectónica

### PENDIENTE: Determinar modelo Claude óptimo (Plan Pro disponible)

**DECISIÓN**: Reemplazar `ChatGoogleGenerativeAI` con `ChatAnthropic` (modelo a determinar)

**PROBLEMA RESUELTO**:
- Gemini: Tier gratuito muy limitado (20 req/día) ← **BLOQUEANTE**
- Claude (Plan Pro): Sin límites de requests, mejor performance
- Costo controlado con plan pro

**ALTERNATIVAS CON PLAN PRO**:

| Modelo | Velocidad | Calidad Copy | Costo | Rate Limit |
|--------|-----------|--------------|-------|------------|
| **Claude 3.5 Haiku** | ⚡ Muy rápida | Buena | $0.80/M input | 90k tok/min |
| **Claude 3.5 Sonnet** | ⚡⚡ Rápida | Excelente | $3/M input | 200k tok/min |
| **Claude 3 Opus** | ⚡⚡⚡ Más lenta | Superior | $15/M input | 200k tok/min |
| Gemini (upgrade) | ⚡⚡ Rápido | Buena | $5/mes + pay-go | Variable |

**CONSIDERACIONES PARA ELEGIR**:
- 🎯 **Calidad de copy**: ¿Importa más calidad o velocidad?
- 💰 **Costo mensual**: Con plan pro, ¿diferencia marginal vs beneficio?
- ⏱️ **Latency**: ¿Necesitas respuesta en <10s o tolerabas 30-60s?
- 🔄 **Volumen**: ¿Procesas 10 videos/día o 1 video/semana?

**DECISIÓN PENDIENTE**: Necesitamos evaluar:
1. ¿Cuál es tu prioridad: calidad copy vs tiempo de ejecución?
2. ¿Cuántos videos procesas típicamente por semana?
3. ¿Presupuesto disponible para LLM?

**RECOMENDACIÓN TENTATIVA**: Claude 3.5 Sonnet
- ✅ Mejor balance entre calidad y costo
- ✅ ~20% más barato que Opus pero superior a Haiku
- ✅ Rate limits suficientes para 100+ clips/día
- ✅ Excelente para contenido creativo (copies/captions)
- ⚠️ ~200ms más lento que Haiku por request, pero negligible en lote

---

## 💰 Análisis de Costo (Con Plan Pro Claude)

### Estimado de uso actual (Gemini)

**Por video procesado** (~30 clips):
- Clasificación: 1 call (5K tokens)
- Generación: 3 calls × 8K tokens = 24K tokens
- **Total**: ~29K tokens/video
- **Costo**: $0.005/video (Gemini Flash) pero **limitado a 20 req/día**

### Costo con Claude (Plan Pro)

**Modelo: Claude 3.5 Sonnet** (recomendado):
- Input: 29K tokens × $3/M = $0.087/video
- Output: ~8K tokens × $15/M = $0.12/video
- **Total**: ~$0.21/video

**Con Prompt Caching** (NUEVO - 90% descuento):
- Prompts reutilizables (~10K tokens) = $0.03
- Tokens restantes: $0.18
- **Costo efectivo**: ~$0.21/video (sin caching)
- **Con caching**: ~$0.12/video ← **60% menos por repetición**

### Comparativa económica

| Escenario | Gemini | Claude Sonnet | ROI |
|-----------|--------|---------------|-----|
| 10 videos/mes | $0.05 (limitado) | $2.10 | Worse |
| 100 videos/mes | $0.50 (limitado) | $21 | Worse pero sin límites |
| 1000 videos/mes | NO POSIBLE | $210 | ✅ Viable con plan pro |
| Con caching | N/A | $120/1000 videos | ✅ Excelente |

**ANÁLISIS**: Con plan pro, Gemini deja de ser viable por límite diario. Claude es mejor inversión a volumen alto.

### ROI de migración

- Tiempo implementación: ~30 minutos
- Costo inicial: $0 (cambio de código)
- Beneficio: Desbloquea capacidad de procesar sin límite diario
- **CRÍTICO**: ✅ Migración obligatoria si procesas >20 clips/día

---

## 🏗️ Integración Arquitectónica

### Cambios necesarios

**Dependencias** (`pyproject.toml`):
```diff
  dependencies = [
    "langchain-google-genai>=2.1.12",  ← REMOVER
+   "langchain-anthropic>=0.1.0",       ← AGREGAR
    "langgraph>=0.6.11",                ← MANTENER
  ]
```

**Código** (`src/copys_generator.py`):
```diff
- from langchain_google_genai import ChatGoogleGenerativeAI
+ from langchain_anthropic import ChatAnthropic

  class CopysGenerator:
    def __init__(self, video_id: str, model: str = "claude-3-5-haiku-20241022", ...):
-     self.llm = ChatGoogleGenerativeAI(
+     self.llm = ChatAnthropic(
        model=self.model,
        temperature=0.8,
        top_p=0.95,
      )
```

**Parámetros ajustados**:
- `temperature`: 0.8 (mismo, creativo para copies)
- `top_p`: 0.95 (mismo)
- `max_tokens`: Agregar límite explícito (Anthropic lo requiere)
- `timeout`: Considerar aumentar a 60s (Claude a veces más lento)

### Compatibilidad con LangGraph

✅ **100% compatible**: LangChain abstrae los LLMs
- `self.llm.invoke(messages)` funciona igual
- Los "nodes" del grafo no cambian
- Validación Pydantic sigue igual

### Validación de cambios

**Qué NO cambia**:
- Estructura de prompts (compatible)
- Validación de esquemas (Pydantic)
- Flujo de LangGraph (mismo architecture)
- Guardado de resultados (JSON)

**Qué cambia mínimamente**:
- Modelo name (gemini-2.5-flash → claude-3-5-haiku-20241022)
- Parámetro `max_tokens` (nuevo requerimiento)
- Error handling (excepciones de Anthropic vs Google)

---

## 📋 Plan de Implementación

### Fase 1: Preparación
- [ ] Crear API key en Anthropic console
- [ ] Guardar en `.env` como `ANTHROPIC_API_KEY`
- [ ] Revisar documentación de Claude API

### Fase 2: Implementación
- [ ] Actualizar `pyproject.toml`: instalar `langchain-anthropic`
- [ ] Editar `src/copys_generator.py` línea 34 (import)
- [ ] Editar `src/copys_generator.py` línea 139 (inicialización)
- [ ] Ajustar parámetros del modelo si es necesario
- [ ] Testear con video pequeño

### Fase 3: Validación
- [ ] Verificar que copies generados son válidos
- [ ] Comparar calidad: Gemini vs Claude
- [ ] Medir latency (tiempo de generación)
- [ ] Revisar costos reales vs estimado

### Fase 4: Optimización (Opcional)
- [ ] Implementar prompt caching (90% descuento)
- [ ] Ajustar temperatura si es necesario
- [ ] Documentar diferencias vs Gemini

### Fase 5: Deprecation
- [ ] Remover `langchain-google-genai` de dependencias
- [ ] Remover `GOOGLE_API_KEY` del `.env`
- [ ] Actualizar documentación

---

## ❓ Preguntas Pendientes (Para tu decisión)

**Necesito responder**:

1. **¿Qué prioridad tiene para CLIPER?**
   - 🎯 **Calidad de copy** (excelente, profesional)
   - ⚡ **Velocidad de procesamiento** (máximo latency)
   - 💰 **Costo mínimo** (eficiencia)

2. **¿Cuántos videos procesas típicamente?**
   - 1-5 videos/semana
   - 1-2 videos/día
   - 3+ videos/día

3. **Modelo preferido?**
   - Claude 3.5 Haiku (más barato, suficiente)
   - Claude 3.5 Sonnet (mejor balance, recomendado)
   - Claude 3 Opus (máxima calidad, más caro)

---

## 🚀 Plan de acción

**Basado en tu aprobación**:

✅ **OPCIÓN A: Migrar a Claude 3.5 Sonnet** (RECOMENDADO)
- Mejor ratio costo-calidad para copies
- Sin límites diarios (plan pro desbloqueado)
- Tiempo: ~30 minutos
- Próximo paso: Crear `todoCLAUDE-SONNET/` con pasos detallados

✅ **OPCIÓN B: Migrar a Claude 3.5 Haiku**
- Si presupuesto es crítico
- 80% más barato pero algo menos capable
- Tiempo: ~30 minutos
- Próximo paso: Crear `todoCLAUDE-HAIKU/` con pasos detallados

❌ **OPCIÓN C: Mantener Gemini + pagar upgrade**
- No recomendado: inferior a Claude
- Sigue teniendo límites diarios
- Costo: $5/mes + pay-as-you-go

**DECISIÓN**: ¿Cuál prefieres?

---

## 📚 Referencias

- LangChain Anthropic: https://python.langchain.com/docs/integrations/llms/anthropic
- Claude API: https://docs.anthropic.com/
- Prompt Caching: https://docs.anthropic.com/en/docs/build-a-Claude-app/prompt-caching
- Pricing: https://www.anthropic.com/pricing
